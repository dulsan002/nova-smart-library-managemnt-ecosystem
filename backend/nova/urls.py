"""
Nova — URL Configuration
=========================
Routes all traffic through GraphQL endpoint with admin fallback.

Security Notes:
- Django admin is behind a non-guessable URL path.
- GraphQL endpoint uses csrf_exempt because auth is JWT-based (Bearer tokens).
- GraphiQL interactive IDE is only available when DEBUG=True.
"""

import os

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView

# Read admin URL from env or use a non-default path
ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL', 'nova-admin-panel/')

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG))),
]

# Identity REST endpoints (file uploads)
from apps.identity.presentation.views import upload_verification_document  # noqa: E402
urlpatterns += [
    path('api/upload/verification/', upload_verification_document, name='upload-verification'),
]

# Digital content page-serving endpoint
from apps.digital_content.presentation.views import DigitalAssetPageView, AudiobookStreamView  # noqa: E402
urlpatterns += [
    path('media/digital/<uuid:asset_id>/page/<int:page>/', DigitalAssetPageView.as_view(), name='digital-page'),
    path('media/digital/<uuid:asset_id>/audio/', AudiobookStreamView.as_view(), name='audiobook-stream'),
]

# Health check (no auth required — load balancer probe)
from django.http import JsonResponse  # noqa: E402


def health_check(request):
    return JsonResponse({'status': 'ok'})


urlpatterns += [path('healthz/', health_check)]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar
        from django.urls import include
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Admin site customization
admin.site.site_header = 'Nova Digital Library Administration'
admin.site.site_title = 'Nova Admin'
admin.site.index_title = 'System Management'
admin.site.login_template = 'admin/login.html'
