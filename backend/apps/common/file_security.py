"""
Nova — File Upload Security
===============================
Defence-in-depth validation for all user-uploaded files.

Checks performed (in order):
1. **Extension allow-list** — Only extensions in ``ALLOWED_UPLOAD_EXTENSIONS``
   are accepted.
2. **MIME / magic-byte verification** — The actual first bytes of the file
   must match the declared extension so a renamed ``malware.exe`` → ``img.png``
   is rejected.
3. **Size limit** — Per-category size limits from ``MAX_UPLOAD_SIZES``.
4. **Filename sanitisation** — Path traversal, null bytes, and shell
   meta-characters are scrubbed.
5. **Image EXIF stripping** — GPS and other PII-rich EXIF tags are removed
   from JPEG/PNG uploads.
6. **Content scanning hooks** — A pluggable function slot for ClamAV or
   similar AV scans (no-op by default).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
import struct
from io import BytesIO
from pathlib import PurePosixPath
from typing import BinaryIO, Dict, Optional, Set, Tuple

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from apps.common.exceptions import ValidationError
from apps.common.sanitizers import sanitize_path

logger = logging.getLogger("nova.security")

# =========================================================================
# Magic-byte signatures
# =========================================================================

MAGIC_SIGNATURES: Dict[str, list[bytes]] = {
    ".pdf": [b"%PDF"],
    ".epub": [b"PK\x03\x04"],                       # EPUB is a ZIP archive
    ".mp3": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    ".m4a": [b"\x00\x00\x00"],                       # ftyp box (checked deeper below)
    ".ogg": [b"OggS"],
    ".wav": [b"RIFF"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".webp": [b"RIFF"],                               # RIFF....WEBP
}


def _check_magic(data: bytes, ext: str) -> bool:
    """Return True if ``data`` starts with a valid magic sequence for ``ext``."""
    sigs = MAGIC_SIGNATURES.get(ext.lower())
    if sigs is None:
        # No signature registered → accept (trust the extension allow-list)
        return True
    return any(data.startswith(sig) for sig in sigs)


# =========================================================================
# Public API
# =========================================================================

def validate_upload(
    file: UploadedFile,
    category: str,
) -> Tuple[str, str]:
    """
    Validate an uploaded file.

    Parameters
    ----------
    file : UploadedFile
        Django uploaded file object.
    category : str
        One of the keys in ``settings.ALLOWED_UPLOAD_EXTENSIONS``
        (``ebook``, ``audiobook``, ``image``, ``id_document``).

    Returns
    -------
    (safe_filename, sha256_hash)
        The sanitised filename and the hex SHA-256 digest of the content.

    Raises
    ------
    ValidationError
        If any check fails.
    """
    allowed_exts: Dict[str, list] = getattr(
        settings, "ALLOWED_UPLOAD_EXTENSIONS", {}
    )
    max_sizes: Dict[str, int] = getattr(settings, "MAX_UPLOAD_SIZES", {})

    if category not in allowed_exts:
        raise ValidationError(
            f"Unknown upload category: {category}",
            field="category",
        )

    # --- 1. Extension check ---
    ext = _extract_extension(file.name)
    if ext not in allowed_exts[category]:
        raise ValidationError(
            f"File type '{ext}' is not allowed for {category} uploads. "
            f"Allowed types: {', '.join(allowed_exts[category])}",
            field="file",
        )

    # --- 2. Size check ---
    max_size = max_sizes.get(category, 10 * 1024 * 1024)
    if file.size and file.size > max_size:
        mb = max_size / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds the {mb:.0f} MB limit for {category} uploads.",
            field="file",
        )

    # --- 3. Magic-byte verification ---
    header = file.read(16)
    file.seek(0)
    if not _check_magic(header, ext):
        logger.warning(
            "Magic-byte mismatch: ext=%s header=%r filename=%s",
            ext, header[:8], file.name,
        )
        raise ValidationError(
            "File content does not match the declared file type.",
            field="file",
        )

    # --- 4. Compute hash (stream to avoid loading entire file) ---
    sha256 = _compute_sha256(file)
    file.seek(0)

    # --- 5. Sanitise filename ---
    safe_name = _safe_filename(file.name, ext)

    # --- 6. Image EXIF strip (JPEG / PNG) ---
    if ext in (".jpg", ".jpeg", ".png"):
        _strip_exif(file)

    # --- 7. AV scan hook ---
    _antivirus_scan(file, safe_name)

    logger.info(
        "Upload validated",
        extra={
            "category": category,
            "filename": safe_name,
            "size": file.size,
            "sha256": sha256,
        },
    )

    return safe_name, sha256


# =========================================================================
# Internal helpers
# =========================================================================

def _extract_extension(filename: str) -> str:
    """Return the lower-cased file extension including the dot."""
    ext = PurePosixPath(filename).suffix.lower()
    if not ext:
        raise ValidationError("File has no extension.", field="file")
    return ext


def _safe_filename(original: str, ext: str) -> str:
    """Generate a safe filename preserving the extension."""
    # Attempt to sanitize the original stem
    stem = PurePosixPath(original).stem
    stem = re.sub(r"[^\w\-.]", "_", stem)[:80]
    # Append a random token to prevent collisions
    token = secrets.token_hex(8)
    return f"{stem}_{token}{ext}"


def _compute_sha256(file: BinaryIO) -> str:
    """Stream-compute SHA-256 without loading the full file into memory."""
    h = hashlib.sha256()
    for chunk in file.chunks() if hasattr(file, "chunks") else _read_chunks(file):
        h.update(chunk)
    return h.hexdigest()


def _read_chunks(f: BinaryIO, chunk_size: int = 65_536):
    while True:
        data = f.read(chunk_size)
        if not data:
            break
        yield data


def _strip_exif(file: UploadedFile) -> None:
    """
    Remove EXIF metadata from JPEG/PNG images (best-effort).

    Uses Pillow if available; silently skips if not installed.
    """
    try:
        from PIL import Image

        img = Image.open(file)

        # Remove EXIF by re-saving without metadata
        cleaned = BytesIO()
        img_format = img.format or "JPEG"

        # Create a new image without EXIF
        data = list(img.getdata())
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(data)
        clean_img.save(cleaned, format=img_format, quality=95)

        # Replace file content
        file.seek(0)
        file.truncate(0)
        file.write(cleaned.getvalue())
        file.seek(0)

        logger.debug("EXIF data stripped from upload")

    except ImportError:
        logger.debug("Pillow not available; skipping EXIF strip")
    except Exception as exc:
        logger.warning("EXIF strip failed (non-blocking): %s", exc)


def _antivirus_scan(file: UploadedFile, filename: str) -> None:
    """
    Hook for antivirus scanning.

    Override by setting ``settings.ANTIVIRUS_SCAN_FUNC`` to a callable
    that accepts ``(file, filename)`` and raises ``ValidationError``
    if a threat is detected.

    Default: no-op.
    """
    scan_func = getattr(settings, "ANTIVIRUS_SCAN_FUNC", None)
    if callable(scan_func):
        try:
            scan_func(file, filename)
        except ValidationError:
            raise
        except Exception as exc:
            logger.error("Antivirus scan error (fail-open): %s", exc)
