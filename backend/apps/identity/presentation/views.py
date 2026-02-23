"""
Nova — Identity REST Views
==============================
Handles file uploads for NIC verification.
GraphQL doesn't natively support multipart uploads, so we use
a REST endpoint for document/selfie uploads.
"""

import logging
import os
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger('nova.identity')

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@csrf_exempt
@require_POST
def upload_verification_document(request):
    """
    Upload a verification document (NIC photo or selfie).

    POST /api/upload/verification/
    Content-Type: multipart/form-data
    Body: file (image), type ("nic" | "selfie")

    Returns: { "success": true, "path": "/media/verifications/..." }
    """
    file = request.FILES.get('file')
    doc_type = request.POST.get('type', 'nic')  # 'nic' or 'selfie'

    if not file:
        return JsonResponse(
            {'success': False, 'error': 'No file provided.'},
            status=400,
        )

    # Validate file extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JsonResponse(
            {'success': False, 'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'},
            status=400,
        )

    # Validate file size
    if file.size > MAX_FILE_SIZE:
        return JsonResponse(
            {'success': False, 'error': 'File too large. Maximum size is 10 MB.'},
            status=400,
        )

    # Generate unique filename
    unique_name = f'{doc_type}_{uuid.uuid4().hex}{ext}'
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'verifications')
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, unique_name)

    # Save file
    with open(file_path, 'wb+') as dest:
        for chunk in file.chunks():
            dest.write(chunk)

    # Return the relative path under MEDIA_ROOT
    relative_path = os.path.join('verifications', unique_name)
    media_url = f'{settings.MEDIA_URL}{relative_path}'

    logger.info('Verification document uploaded: type=%s, path=%s', doc_type, relative_path)

    return JsonResponse({
        'success': True,
        'path': file_path,  # Absolute path for backend processing
        'url': media_url,   # URL for frontend display
        'filename': unique_name,
    })
