"""
Nova — Digital Content REST Views
=====================================
Serves paginated ebook content and audiobook streams for the reader UI.

Endpoints:
    GET /media/digital/<asset_id>/page/<page_number>/  — ebook pages
    GET /media/digital/<asset_id>/audio/                — audiobook stream
"""

import hashlib
import io
import struct
import textwrap

from django.http import FileResponse, JsonResponse
from django.views import View

from apps.digital_content.domain.models import DigitalAsset


# ---------------------------------------------------------------------------
# Deterministic content generation
# ---------------------------------------------------------------------------
# Since we don't store real PDF files, we generate realistic placeholder
# page content based on the book's metadata.  The content is deterministic
# (seeded by asset-id + page number) so the same page always renders the
# same text, bookmarks / highlights remain valid, and the reading
# experience feels natural during development/demos.
# ---------------------------------------------------------------------------

# Paragraph pool — drawn from classic CS / literature themes so the reader
# looks convincing.  We cycle through these deterministically per page.
_PARAGRAPHS = [
    (
        "The fundamental concepts underlying this chapter form the backbone of "
        "modern computational theory. As we explore each principle, consider how "
        "these ideas connect to the broader landscape of algorithmic design and "
        "software craftsmanship."
    ),
    (
        "In practice, the distinction between theory and implementation is often "
        "less clear than textbooks suggest. Real-world systems must balance "
        "correctness with performance, elegance with pragmatism, and simplicity "
        "with the demands of scale."
    ),
    (
        "Consider the following scenario: a distributed system must maintain "
        "consistency across multiple nodes while tolerating network partitions. "
        "The CAP theorem tells us we cannot have all three guarantees "
        "simultaneously, forcing architects to make deliberate trade-offs."
    ),
    (
        "Data structures are the building blocks of efficient algorithms. "
        "Choosing the right structure — whether a balanced tree, hash table, "
        "or graph — can mean the difference between a solution that scales "
        "gracefully and one that collapses under load."
    ),
    (
        "Software engineering is as much about communication as it is about "
        "code. Clear naming, thoughtful documentation, and well-structured "
        "abstractions enable teams to collaborate effectively across time "
        "zones and experience levels."
    ),
    (
        "The evolution of programming paradigms — from procedural to "
        "object-oriented to functional — reflects our growing understanding "
        "of how to manage complexity. Each paradigm offers unique tools for "
        "reasoning about state, side effects, and composition."
    ),
    (
        "Testing is not merely a quality assurance activity; it is a design "
        "tool. Writing tests first forces us to think about interfaces, "
        "contracts, and edge cases before committing to an implementation — "
        "leading to code that is more modular and resilient."
    ),
    (
        "Machine learning has transformed fields from natural language "
        "processing to computer vision. Yet the underlying mathematics — "
        "linear algebra, probability theory, and optimization — remain the "
        "essential foundation upon which all modern AI systems are built."
    ),
    (
        "Security must be considered at every layer of the stack. From input "
        "validation on the frontend to encryption at rest in the database, "
        "a defence-in-depth strategy ensures that no single vulnerability "
        "can compromise the entire system."
    ),
    (
        "The history of computing is a story of abstraction. Assembly gave "
        "way to high-level languages, monoliths yielded to microservices, "
        "and bare metal was replaced by cloud infrastructure — each layer "
        "hiding complexity while unlocking new possibilities."
    ),
    (
        "Concurrency introduces subtle challenges that sequential thinking "
        "cannot anticipate. Race conditions, deadlocks, and starvation "
        "require developers to reason carefully about shared state and "
        "adopt patterns like message passing or software transactional memory."
    ),
    (
        "Good API design is an exercise in empathy. The best APIs anticipate "
        "how consumers will use them, provide sensible defaults, fail "
        "gracefully with clear error messages, and evolve without breaking "
        "existing clients."
    ),
]


def _page_seed(asset_id: str, page: int) -> int:
    """Produce a deterministic integer seed from asset + page."""
    h = hashlib.md5(f"{asset_id}:{page}".encode()).hexdigest()
    return int(h[:8], 16)


def _generate_chapter_title(book_title: str, page: int, total_pages: int) -> str:
    """Generate a plausible chapter title for the given page."""
    chapters_approx = max(total_pages // 40, 5)
    chapter_num = (page * chapters_approx) // total_pages + 1
    chapter_titles = [
        "Introduction", "Foundations", "Core Concepts",
        "Analysis and Design", "Implementation Strategies",
        "Advanced Topics", "Case Studies", "Optimization",
        "Testing and Validation", "Integration Patterns",
        "Scaling Approaches", "Security Considerations",
        "Performance Tuning", "Emerging Trends",
        "Practical Applications", "Review and Summary",
        "Theoretical Framework", "Methodology",
        "Experimental Results", "Conclusions",
    ]
    idx = (chapter_num - 1) % len(chapter_titles)
    return f"Chapter {chapter_num}: {chapter_titles[idx]}"


def _generate_page_html(asset: DigitalAsset, page: int) -> tuple[str, str]:
    """
    Return (html, plain_text) for the requested page of the given asset.
    """
    book = asset.book
    total = asset.total_pages or 300
    seed = _page_seed(str(asset.pk), page)
    authors_str = ", ".join(
        f"{a.first_name} {a.last_name}" for a in book.authors.all()
    ) or "Unknown Author"

    # --- Page 1: title page ---
    if page == 1:
        html = (
            f'<div style="text-align:center; padding:60px 20px;">'
            f'<h1 style="font-size:2em; margin-bottom:0.3em;">{book.title}</h1>'
        )
        if book.subtitle:
            html += f'<h2 style="font-size:1.2em; color:#666; margin-bottom:1em;">{book.subtitle}</h2>'
        html += (
            f'<p style="font-size:1.1em; color:#444;">{authors_str}</p>'
            f'<hr style="margin:2em auto; width:60%; border-color:#ddd;">'
            f'<p style="color:#888;">{book.publisher or ""}'
            f'{" · " + str(book.publication_date.year) if book.publication_date else ""}</p>'
            f'<p style="color:#888;">ISBN: {book.isbn_13 or book.isbn_10 or "N/A"}</p>'
            f'<p style="color:#888; margin-top:2em;">{total} pages</p>'
            f'</div>'
        )
        text = f"{book.title}\n{authors_str}\n{book.publisher or ''}"
        return html, text

    # --- Page 2: description / preface ---
    if page == 2:
        desc = book.description or "No description available."
        html = (
            f'<div style="padding:20px;">'
            f'<h2 style="margin-bottom:0.8em;">Preface</h2>'
            f'<p style="line-height:1.8; text-align:justify;">{desc}</p>'
            f'<p style="line-height:1.8; text-align:justify; margin-top:1em;">'
            f'This book spans {total} pages and is organized into multiple '
            f'chapters covering both theoretical foundations and practical '
            f'applications. We hope it serves as a valuable resource for '
            f'students, researchers, and practitioners alike.</p>'
            f'</div>'
        )
        return html, desc

    # --- Regular content pages ---
    # Decide whether this page starts a new chapter
    pages_per_chapter = max(total // max(total // 40, 5), 10)
    is_chapter_start = (page - 3) % pages_per_chapter == 0

    parts_html = ['<div style="padding:20px;">']
    parts_text = []

    if is_chapter_start:
        chapter_title = _generate_chapter_title(book.title, page, total)
        parts_html.append(
            f'<h2 style="margin-bottom:0.8em; border-bottom:1px solid #e5e7eb; '
            f'padding-bottom:0.4em;">{chapter_title}</h2>'
        )
        parts_text.append(chapter_title)

    # Generate 4-6 paragraphs per page
    num_paragraphs = 4 + (seed % 3)   # 4, 5, or 6
    for i in range(num_paragraphs):
        idx = (seed + i * 7) % len(_PARAGRAPHS)
        para = _PARAGRAPHS[idx]
        # Slightly vary paragraphs by inserting the book title occasionally
        if i == 1:
            para = para.replace(
                "this chapter",
                f"this section of <em>{book.title}</em>",
            )
        parts_html.append(
            f'<p style="line-height:1.8; text-align:justify; '
            f'margin-bottom:1em; text-indent:1.5em;">{para}</p>'
        )
        parts_text.append(para)

    # Optional aside / note block every ~8 pages
    if page % 8 == 0:
        parts_html.append(
            '<blockquote style="border-left:3px solid #10b981; padding:10px 15px; '
            'margin:1em 0; background:#f0fdf4; font-style:italic;">'
            f'<strong>Key Insight:</strong> The concepts discussed in {book.title} '
            'build upon each other progressively. Revisiting earlier sections '
            'after completing later chapters often reveals deeper connections.'
            '</blockquote>'
        )

    parts_html.append('</div>')

    return "\n".join(parts_html), "\n\n".join(parts_text)


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class DigitalAssetPageView(View):
    """
    GET /media/digital/<uuid:asset_id>/page/<int:page>/

    Returns JSON ``{ "html": "...", "text": "..." }`` for the requested page.
    """

    def get(self, request, asset_id, page):
        try:
            asset = DigitalAsset.objects.select_related('book').get(
                pk=asset_id, upload_completed=True,
            )
        except DigitalAsset.DoesNotExist:
            return JsonResponse(
                {"error": "Digital asset not found."},
                status=404,
            )

        total = asset.total_pages or 300
        if page < 1 or page > total:
            return JsonResponse(
                {"error": f"Page {page} out of range (1–{total})."},
                status=404,
            )

        # Prefetch authors for the content generator
        asset.book.authors.all()  # force evaluation so it's cached

        html, text = _generate_page_html(asset, page)

        return JsonResponse({
            "html": html,
            "text": text,
            "page": page,
            "totalPages": total,
        })


# ---------------------------------------------------------------------------
# Audio generation helpers
# ---------------------------------------------------------------------------

def _generate_wav(duration_seconds: int, sample_rate: int = 22050) -> bytes:
    """
    Generate a minimal WAV file with silence for the given duration.
    Uses 16-bit mono PCM at a low sample rate to keep the file tiny.
    A 3-hour audiobook at 22050 Hz × 16-bit mono ≈ ~475 MB which is too
    much, so we cap at 30 seconds of real silence and let the frontend
    player display the full duration via the `duration_seconds` metadata
    from the GraphQL query instead.
    """
    capped = min(duration_seconds, 30)  # short silence placeholder
    num_samples = sample_rate * capped
    bits_per_sample = 16
    num_channels = 1
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    buf = io.BytesIO()
    # RIFF header
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + data_size))  # file size - 8
    buf.write(b'WAVE')
    # fmt chunk
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16))               # chunk size
    buf.write(struct.pack('<H', 1))                # PCM format
    buf.write(struct.pack('<H', num_channels))
    buf.write(struct.pack('<I', sample_rate))
    buf.write(struct.pack('<I', byte_rate))
    buf.write(struct.pack('<H', block_align))
    buf.write(struct.pack('<H', bits_per_sample))
    # data chunk
    buf.write(b'data')
    buf.write(struct.pack('<I', data_size))
    buf.write(b'\x00' * data_size)                 # silence

    return buf.getvalue()


class AudiobookStreamView(View):
    """
    GET /media/digital/<uuid:asset_id>/audio/

    Streams a WAV audio file for the requested audiobook.
    In production this would proxy to object storage; for dev/demo we
    return a short silent WAV so the player UI works end-to-end.
    """

    def get(self, request, asset_id):
        try:
            asset = DigitalAsset.objects.select_related('book').get(
                pk=asset_id, upload_completed=True,
            )
        except DigitalAsset.DoesNotExist:
            return JsonResponse({'error': 'Digital asset not found.'}, status=404)

        if not asset.is_audiobook:
            return JsonResponse({'error': 'Asset is not an audiobook.'}, status=400)

        duration = asset.duration_seconds or 30
        wav_bytes = _generate_wav(duration)

        return FileResponse(
            io.BytesIO(wav_bytes),
            content_type='audio/wav',
            filename=f'{asset.book.title}.wav',
        )
