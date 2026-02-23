"""
Nova — Shared Decorators
==========================
Reusable decorators for authorization, auditing, and rate limiting.
"""

import functools
import logging
from typing import List, Optional

from django.conf import settings

from apps.common.permissions import Permission, has_permission, has_any_role
from apps.common.exceptions import AuthorizationError, AuthenticationError

logger = logging.getLogger('nova')


def require_authentication(func):
    """
    Decorator to ensure the user is authenticated.
    For use on GraphQL resolvers.
    """
    @functools.wraps(func)
    def wrapper(root, info, *args, **kwargs):
        user = info.context.user
        if not user or not user.is_authenticated:
            raise AuthenticationError('Authentication required.')
        if not user.is_active:
            raise AuthenticationError('Your account has been deactivated.')
        return func(root, info, *args, **kwargs)
    return wrapper


def require_roles(allowed_roles: List[str]):
    """
    Decorator to restrict access to specific roles.
    For use on GraphQL resolvers.

    Args:
        allowed_roles: List of role strings that can access this resolver.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(root, info, *args, **kwargs):
            user = info.context.user
            if not user or not user.is_authenticated:
                raise AuthenticationError('Authentication required.')
            if not user.is_active:
                raise AuthenticationError('Your account has been deactivated.')

            if not has_any_role(user.role, allowed_roles):
                logger.warning(
                    f'Authorization denied: user={user.id} role={user.role} '
                    f'attempted access requiring roles={allowed_roles}'
                )
                raise AuthorizationError(
                    f'This action requires one of the following roles: {", ".join(allowed_roles)}'
                )

            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: Permission):
    """
    Decorator to restrict access based on fine-grained permissions.
    For use on GraphQL resolvers.

    Args:
        permission: The Permission enum value required.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(root, info, *args, **kwargs):
            user = info.context.user
            if not user or not user.is_authenticated:
                raise AuthenticationError('Authentication required.')
            if not user.is_active:
                raise AuthenticationError('Your account has been deactivated.')

            if not has_permission(user.role, permission):
                logger.warning(
                    f'Permission denied: user={user.id} role={user.role} '
                    f'lacks permission={permission.value}'
                )
                raise AuthorizationError(
                    f'You do not have the required permission: {permission.value}'
                )

            return func(root, info, *args, **kwargs)
        return wrapper
    return decorator


def audit_action(action: str, resource_type: str):
    """
    Decorator to automatically log an audit entry after successful execution.
    For use on GraphQL mutation resolvers.

    Args:
        action: Description of the action (e.g., 'book_created').
        resource_type: Type of resource being acted upon (e.g., 'Book').
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(root, info, *args, **kwargs):
            result = func(root, info, *args, **kwargs)

            try:
                from apps.governance.services import AuditService
                from apps.common.utils import get_client_ip, get_user_agent

                user = info.context.user
                resource_id = None

                # Try to extract resource ID from result
                if hasattr(result, 'id'):
                    resource_id = str(result.id)
                elif hasattr(result, 'pk'):
                    resource_id = str(result.pk)

                AuditService.log(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id or '',
                    actor_id=getattr(user, 'id', None),
                    actor_email=getattr(user, 'email', ''),
                    actor_role=getattr(user, 'role', ''),
                    ip_address=get_client_ip(info.context),
                    user_agent=get_user_agent(info.context),
                )
            except Exception as e:
                logger.error(f'Failed to create audit log: {e}', exc_info=True)

            return result
        return wrapper
    return decorator
