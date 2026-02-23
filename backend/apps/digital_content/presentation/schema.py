"""
Nova — Digital Content GraphQL Schema
=========================================
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import audit_action, require_authentication, require_roles
from apps.common.permissions import Role

from apps.digital_content.application import (
    AddBookmarkUseCase,
    AddHighlightUseCase,
    CreateBookmarkDTO,
    CreateHighlightDTO,
    EndReadingSessionUseCase,
    StartReadingSessionUseCase,
    StartSessionDTO,
    ToggleFavoriteUseCase,
    UpdateProgressDTO,
    UpdateProgressUseCase,
)
from apps.digital_content.domain.models import (
    Bookmark,
    DigitalAsset,
    Highlight,
    ReadingSession,
    UserLibrary,
)

from apps.common.utils import get_client_ip


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class DigitalAssetType(DjangoObjectType):
    is_ebook = graphene.Boolean()
    is_audiobook = graphene.Boolean()

    class Meta:
        model = DigitalAsset
        fields = (
            'id', 'book', 'asset_type', 'file_path', 'file_size_bytes', 'mime_type',
            'duration_seconds', 'narrator', 'total_pages',
            'is_drm_protected', 'upload_completed', 'created_at',
        )

    def resolve_is_ebook(self, info):
        return self.is_ebook

    def resolve_is_audiobook(self, info):
        return self.is_audiobook


class ReadingSessionType(DjangoObjectType):
    class Meta:
        model = ReadingSession
        fields = (
            'id', 'user', 'digital_asset', 'session_type', 'status',
            'started_at', 'ended_at', 'duration_seconds',
            'progress_percent', 'last_position', 'kp_awarded',
            'device_type', 'created_at',
        )


class BookmarkType(DjangoObjectType):
    class Meta:
        model = Bookmark
        fields = (
            'id', 'user', 'digital_asset', 'title',
            'position', 'note', 'color', 'created_at',
        )


class HighlightType(DjangoObjectType):
    class Meta:
        model = Highlight
        fields = (
            'id', 'user', 'digital_asset', 'text',
            'position_start', 'position_end', 'color', 'note',
            'created_at',
        )


class UserLibraryType(DjangoObjectType):
    class Meta:
        model = UserLibrary
        fields = (
            'id', 'user', 'digital_asset', 'added_at',
            'last_accessed_at', 'overall_progress',
            'total_time_seconds', 'is_finished', 'is_favorite',
            'last_position',
        )


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class StartReadingSession(graphene.Mutation):
    class Arguments:
        digital_asset_id = graphene.UUID(required=True)
        session_type = graphene.String(required=True)
        device_type = graphene.String()

    Output = ReadingSessionType

    @require_authentication
    @audit_action(action='SESSION_START', resource_type='ReadingSession')
    def mutate(self, info, digital_asset_id, session_type, device_type=''):
        user = info.context.user
        ip = get_client_ip(info.context)
        use_case = StartReadingSessionUseCase()
        dto = StartSessionDTO(
            digital_asset_id=digital_asset_id,
            session_type=session_type,
            device_type=device_type,
            ip_address=ip,
        )
        return use_case.execute(user, dto)


class EndReadingSession(graphene.Mutation):
    class Arguments:
        session_id = graphene.UUID(required=True)

    Output = ReadingSessionType

    @require_authentication
    @audit_action(action='SESSION_END', resource_type='ReadingSession')
    def mutate(self, info, session_id):
        use_case = EndReadingSessionUseCase()
        return use_case.execute(session_id, info.context.user)


class UpdateReadingProgress(graphene.Mutation):
    class Arguments:
        session_id = graphene.UUID(required=True)
        progress_percent = graphene.Float(required=True)
        position = graphene.JSONString()

    Output = ReadingSessionType

    @require_authentication
    def mutate(self, info, session_id, progress_percent, position=None):
        use_case = UpdateProgressUseCase()
        import json
        pos = json.loads(position) if isinstance(position, str) else position
        dto = UpdateProgressDTO(
            session_id=session_id,
            progress_percent=progress_percent,
            position=pos,
        )
        return use_case.execute(info.context.user, dto)


class AddBookmark(graphene.Mutation):
    class Arguments:
        digital_asset_id = graphene.UUID(required=True)
        title = graphene.String()
        position = graphene.JSONString(required=True)
        note = graphene.String()
        color = graphene.String()

    Output = BookmarkType

    @require_authentication
    def mutate(self, info, digital_asset_id, position, title='', note='', color='yellow'):
        import json
        pos = json.loads(position) if isinstance(position, str) else position
        use_case = AddBookmarkUseCase()
        dto = CreateBookmarkDTO(
            digital_asset_id=digital_asset_id,
            title=title,
            position=pos,
            note=note,
            color=color,
        )
        return use_case.execute(info.context.user, dto)


class AddHighlight(graphene.Mutation):
    class Arguments:
        digital_asset_id = graphene.UUID(required=True)
        text = graphene.String(required=True)
        position_start = graphene.JSONString(required=True)
        position_end = graphene.JSONString(required=True)
        color = graphene.String()
        note = graphene.String()

    Output = HighlightType

    @require_authentication
    def mutate(self, info, digital_asset_id, text, position_start, position_end,
               color='yellow', note=''):
        import json
        ps = json.loads(position_start) if isinstance(position_start, str) else position_start
        pe = json.loads(position_end) if isinstance(position_end, str) else position_end
        use_case = AddHighlightUseCase()
        dto = CreateHighlightDTO(
            digital_asset_id=digital_asset_id,
            text=text,
            position_start=ps,
            position_end=pe,
            color=color,
            note=note,
        )
        return use_case.execute(info.context.user, dto)


class ToggleFavorite(graphene.Mutation):
    class Arguments:
        digital_asset_id = graphene.UUID(required=True)

    Output = UserLibraryType

    @require_authentication
    def mutate(self, info, digital_asset_id):
        use_case = ToggleFavoriteUseCase()
        return use_case.execute(info.context.user, digital_asset_id)


class UploadDigitalAsset(graphene.Mutation):
    """Admin mutation to register a digital asset for a book."""

    class Arguments:
        book_id = graphene.UUID(required=True)
        asset_type = graphene.String(required=True)
        file_path = graphene.String(required=True)
        file_size_bytes = graphene.Int(required=True)
        mime_type = graphene.String()
        duration_seconds = graphene.Int()
        narrator = graphene.String()
        total_pages = graphene.Int()

    Output = DigitalAssetType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE', resource_type='DigitalAsset')
    def mutate(self, info, book_id, asset_type, file_path, file_size_bytes,
               mime_type='', duration_seconds=None, narrator='', total_pages=None):
        asset = DigitalAsset.objects.create(
            book_id=book_id,
            asset_type=asset_type,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            narrator=narrator,
            total_pages=total_pages,
            upload_completed=True,
            uploaded_by=info.context.user,
        )
        return asset


class UpdateDigitalAsset(graphene.Mutation):
    """Admin mutation to update a digital asset's metadata."""

    class Arguments:
        digital_asset_id = graphene.UUID(required=True)
        asset_type = graphene.String()
        file_path = graphene.String()
        file_size_bytes = graphene.Int()
        mime_type = graphene.String()
        duration_seconds = graphene.Int()
        narrator = graphene.String()
        total_pages = graphene.Int()

    Output = DigitalAssetType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='UPDATE', resource_type='DigitalAsset')
    def mutate(self, info, digital_asset_id, **kwargs):
        try:
            asset = DigitalAsset.objects.get(pk=digital_asset_id)
        except DigitalAsset.DoesNotExist:
            raise Exception('Digital asset not found.')

        updatable = [
            'asset_type', 'file_path', 'file_size_bytes', 'mime_type',
            'duration_seconds', 'narrator', 'total_pages',
        ]
        for field in updatable:
            val = kwargs.get(field)
            if val is not None:
                setattr(asset, field, val)
        asset.save()
        return asset


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

class DeleteDigitalAsset(graphene.Mutation):
    """Admin mutation to delete a digital asset."""

    class Arguments:
        digital_asset_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='DELETE', resource_type='DigitalAsset')
    def mutate(self, info, digital_asset_id):
        try:
            asset = DigitalAsset.objects.get(pk=digital_asset_id)
        except DigitalAsset.DoesNotExist:
            raise Exception('Digital asset not found.')
        # Remove related UserLibrary entries first
        UserLibrary.objects.filter(digital_asset=asset).delete()
        asset.delete()
        return DeleteDigitalAsset(ok=True)


class DigitalContentQuery(graphene.ObjectType):
    digital_asset = graphene.Field(DigitalAssetType, id=graphene.UUID(required=True))
    digital_assets_for_book = graphene.List(
        DigitalAssetType,
        book_id=graphene.UUID(required=True),
    )
    all_digital_assets = graphene.List(
        DigitalAssetType,
        asset_type=graphene.String(),
        description='List all uploaded digital assets. Optionally filter by asset_type.',
    )

    my_library = graphene.List(UserLibraryType, favorites_only=graphene.Boolean(default_value=False))
    my_reading_sessions = graphene.List(
        ReadingSessionType,
        status=graphene.String(),
        limit=graphene.Int(default_value=20),
    )
    active_session = graphene.Field(
        ReadingSessionType,
        digital_asset_id=graphene.UUID(),
    )

    my_bookmarks = graphene.List(
        BookmarkType,
        digital_asset_id=graphene.UUID(),
    )
    my_highlights = graphene.List(
        HighlightType,
        digital_asset_id=graphene.UUID(),
    )

    def resolve_digital_asset(self, info, id):
        try:
            return DigitalAsset.objects.get(pk=id)
        except DigitalAsset.DoesNotExist:
            return None

    def resolve_digital_assets_for_book(self, info, book_id):
        return DigitalAsset.objects.filter(book_id=book_id, upload_completed=True)

    def resolve_all_digital_assets(self, info, asset_type=None):
        qs = DigitalAsset.objects.filter(upload_completed=True).select_related('book', 'uploaded_by')
        if asset_type:
            qs = qs.filter(asset_type=asset_type)
        return qs.order_by('-created_at')

    @require_authentication
    def resolve_my_library(self, info, favorites_only=False):
        qs = UserLibrary.objects.filter(user=info.context.user)
        if favorites_only:
            qs = qs.filter(is_favorite=True)
        return qs

    @require_authentication
    def resolve_my_reading_sessions(self, info, status=None, limit=20):
        qs = ReadingSession.objects.filter(user=info.context.user)
        if status:
            qs = qs.filter(status=status)
        return qs[:limit]

    @require_authentication
    def resolve_active_session(self, info, digital_asset_id=None):
        qs = ReadingSession.objects.filter(
            user=info.context.user,
            status__in=['ACTIVE', 'PAUSED'],
        )
        if digital_asset_id:
            qs = qs.filter(digital_asset_id=digital_asset_id)
        return qs.first()

    @require_authentication
    def resolve_my_bookmarks(self, info, digital_asset_id=None):
        qs = Bookmark.objects.filter(user=info.context.user)
        if digital_asset_id:
            qs = qs.filter(digital_asset_id=digital_asset_id)
        return qs

    @require_authentication
    def resolve_my_highlights(self, info, digital_asset_id=None):
        qs = Highlight.objects.filter(user=info.context.user)
        if digital_asset_id:
            qs = qs.filter(digital_asset_id=digital_asset_id)
        return qs


# ---------------------------------------------------------------------------
# Mutation root
# ---------------------------------------------------------------------------

class DigitalContentMutation(graphene.ObjectType):
    start_reading_session = StartReadingSession.Field()
    end_reading_session = EndReadingSession.Field()
    update_reading_progress = UpdateReadingProgress.Field()
    add_bookmark = AddBookmark.Field()
    add_highlight = AddHighlight.Field()
    toggle_favorite = ToggleFavorite.Field()
    upload_digital_asset = UploadDigitalAsset.Field()
    update_digital_asset = UpdateDigitalAsset.Field()
    delete_digital_asset = DeleteDigitalAsset.Field()
