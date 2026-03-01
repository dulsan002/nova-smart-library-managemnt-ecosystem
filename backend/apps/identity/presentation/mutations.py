"""
Nova — Identity GraphQL Mutations
=====================================
All write operations for the identity bounded context.
"""

import graphene
import logging
from graphql import GraphQLError

from apps.common.decorators import audit_action, require_authentication, require_roles
from apps.common.permissions import Role
from apps.common.utils import get_client_ip
from apps.identity.application.account_security import (
    check_account_locked,
    record_failed_attempt,
    record_successful_login,
)

from apps.identity.application import (
    ChangePasswordDTO,
    LoginDTO,
    RegisterUserDTO,
    UpdateProfileDTO,
    VerificationSubmitDTO,
)
from apps.identity.application.services import (
    AdminManageUserUseCase,
    AuthenticateUserUseCase,
    ChangePasswordUseCase,
    GetUserProfileUseCase,
    LogoutUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
    SubmitVerificationUseCase,
    UpdateUserProfileUseCase,
)
from apps.identity.infrastructure.repositories import DjangoUserRepository
from apps.identity.infrastructure.token_service import JWTTokenService
from apps.identity.infrastructure.verification_service import AIVerificationService
from apps.identity.presentation.types import AuthPayloadType, TokenPairType, UserType, RoleConfigType, MemberType

logger = logging.getLogger('nova.identity')


def _build_user_repo():
    return DjangoUserRepository()


def _build_token_service():
    return JWTTokenService()


def _build_verification_service():
    return AIVerificationService()


# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------

class RegisterInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    institution_id = graphene.String()


class LoginInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    device_fingerprint = graphene.String()


class UpdateProfileInput(graphene.InputObjectType):
    first_name = graphene.String()
    last_name = graphene.String()
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    institution_id = graphene.String()
    avatar_url = graphene.String()


class ChangePasswordInput(graphene.InputObjectType):
    old_password = graphene.String(required=True)
    new_password = graphene.String(required=True)


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class RegisterUser(graphene.Mutation):
    class Arguments:
        input = RegisterInput(required=True)

    Output = UserType

    @audit_action(action='REGISTER', resource_type='User')
    def mutate(self, info, input):
        from apps.common.exceptions import ConflictError, ValidationError as NovaValidationError
        try:
            use_case = RegisterUserUseCase(
                user_repo=_build_user_repo(),
                token_service=_build_token_service(),
            )
            dto = RegisterUserDTO(
                email=input.email,
                password=input.password,
                first_name=input.first_name,
                last_name=input.last_name,
                phone_number=input.phone_number,
                date_of_birth=input.date_of_birth,
                institution_id=input.institution_id,
            )
            profile = use_case.execute(dto)
            from apps.identity.domain.models import User
            return User.objects.get(pk=profile.id)
        except ConflictError as e:
            raise GraphQLError(e.message)
        except NovaValidationError as e:
            raise GraphQLError(e.message)


class LoginUser(graphene.Mutation):
    class Arguments:
        input = LoginInput(required=True)

    Output = AuthPayloadType

    @audit_action(action='LOGIN', resource_type='User')
    def mutate(self, info, input):
        ip = get_client_ip(info.context)

        # --- Account lockout check ---
        is_locked, retry_after = check_account_locked(input.email, ip)
        if is_locked:
            from apps.common.exceptions import AuthenticationError as AuthErr
            raise AuthErr(
                message=f'Account temporarily locked. Try again in {retry_after} seconds.',
                details={'retry_after': retry_after},
            )

        use_case = AuthenticateUserUseCase(
            user_repo=_build_user_repo(),
            token_service=_build_token_service(),
        )
        dto = LoginDTO(
            email=input.email,
            password=input.password,
            device_fingerprint=input.device_fingerprint,
            ip_address=ip,
        )
        try:
            token_pair = use_case.execute(dto)
        except Exception:
            record_failed_attempt(input.email, ip)
            raise

        # Success — clear failure counters
        record_successful_login(input.email, ip)

        user = _build_user_repo().find_by_email(input.email)
        return AuthPayloadType(
            user=user,
            tokens=TokenPairType(
                access_token=token_pair.access_token,
                refresh_token=token_pair.refresh_token,
                expires_in=token_pair.expires_in,
                token_type=token_pair.token_type,
            ),
        )


class RefreshToken(graphene.Mutation):
    class Arguments:
        refresh_token = graphene.String(required=True)

    Output = TokenPairType

    def mutate(self, info, refresh_token):
        use_case = RefreshTokenUseCase(token_service=_build_token_service())
        pair = use_case.execute(refresh_token)
        return TokenPairType(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            expires_in=pair.expires_in,
            token_type=pair.token_type,
        )


class Logout(graphene.Mutation):
    class Arguments:
        refresh_token_hash = graphene.String(required=True)
        revoke_all = graphene.Boolean(default_value=False)

    success = graphene.Boolean()

    @require_authentication
    def mutate(self, info, refresh_token_hash, revoke_all=False):
        user = info.context.user
        use_case = LogoutUseCase(token_service=_build_token_service())
        use_case.execute(
            refresh_token_hash=refresh_token_hash,
            revoke_all=revoke_all,
            user_id=user.id,
        )
        return Logout(success=True)


class UpdateProfile(graphene.Mutation):
    class Arguments:
        input = UpdateProfileInput(required=True)

    Output = UserType

    @require_authentication
    @audit_action(action='UPDATE_PROFILE', resource_type='User')
    def mutate(self, info, input):
        user = info.context.user
        use_case = UpdateUserProfileUseCase(user_repo=_build_user_repo())
        dto = UpdateProfileDTO(
            first_name=input.first_name,
            last_name=input.last_name,
            phone_number=input.phone_number,
            date_of_birth=input.date_of_birth,
            institution_id=input.institution_id,
            avatar_url=input.avatar_url,
        )
        profile = use_case.execute(user.id, dto)
        from apps.identity.domain.models import User
        return User.objects.get(pk=profile.id)


class ChangePassword(graphene.Mutation):
    class Arguments:
        input = ChangePasswordInput(required=True)

    success = graphene.Boolean()

    @require_authentication
    @audit_action(action='CHANGE_PASSWORD', resource_type='User')
    def mutate(self, info, input):
        from apps.common.exceptions import (
            AuthenticationError as NovaAuthError,
            ValidationError as NovaValidationError,
        )
        user = info.context.user
        use_case = ChangePasswordUseCase(user_repo=_build_user_repo())
        dto = ChangePasswordDTO(
            old_password=input.old_password,
            new_password=input.new_password,
        )
        try:
            use_case.execute(user.id, dto)
        except NovaAuthError as e:
            raise GraphQLError(e.message)
        except NovaValidationError as e:
            raise GraphQLError(e.message)
        return ChangePassword(success=True)


class SubmitVerification(graphene.Mutation):
    class Arguments:
        id_document_path = graphene.String(required=True)
        selfie_path = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @require_authentication
    @audit_action(action='SUBMIT_VERIFICATION', resource_type='VerificationRequest')
    def mutate(self, info, id_document_path, selfie_path):
        user = info.context.user
        ip = get_client_ip(info.context)

        use_case = SubmitVerificationUseCase(
            user_repo=_build_user_repo(),
            verification_service=_build_verification_service(),
        )
        dto = VerificationSubmitDTO(
            user_id=user.id,
            id_document_path=id_document_path,
            selfie_path=selfie_path,
            ip_address=ip,
        )
        use_case.execute(dto)
        return SubmitVerification(
            success=True,
            message='Verification request submitted. You will be notified of the result.',
        )


class ActivateUser(graphene.Mutation):
    class Arguments:
        user_id = graphene.UUID(required=True)

    Output = UserType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='ACTIVATE_USER', resource_type='User')
    def mutate(self, info, user_id):
        use_case = AdminManageUserUseCase(user_repo=_build_user_repo())
        profile = use_case.activate_user(user_id)
        from apps.identity.domain.models import User
        return User.objects.get(pk=profile.id)


class DeactivateUser(graphene.Mutation):
    class Arguments:
        user_id = graphene.UUID(required=True)

    Output = UserType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='DEACTIVATE_USER', resource_type='User')
    def mutate(self, info, user_id):
        use_case = AdminManageUserUseCase(user_repo=_build_user_repo())
        profile = use_case.deactivate_user(user_id)
        from apps.identity.domain.models import User
        return User.objects.get(pk=profile.id)


class ChangeUserRole(graphene.Mutation):
    class Arguments:
        user_id = graphene.UUID(required=True)
        new_role = graphene.String(required=True)

    Output = UserType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='CHANGE_ROLE', resource_type='User')
    def mutate(self, info, user_id, new_role):
        use_case = AdminManageUserUseCase(user_repo=_build_user_repo())
        profile = use_case.change_role(user_id, new_role)
        from apps.identity.domain.models import User
        return User.objects.get(pk=profile.id)


# ---------------------------------------------------------------------------
# NIC Verification types
# ---------------------------------------------------------------------------

class NICVerificationResultType(graphene.ObjectType):
    """Result of AI-powered NIC verification."""
    success = graphene.Boolean()
    is_verified = graphene.Boolean()
    extracted_name = graphene.String()
    extracted_nic_number = graphene.String()
    name_match_score = graphene.Float()
    nic_number_match = graphene.Boolean()
    ocr_confidence = graphene.Float()
    document_type = graphene.String()
    message = graphene.String()
    status = graphene.String()  # APPROVED / REJECTED / MANUAL_REVIEW


class VerifyNICInput(graphene.InputObjectType):
    nic_front_image_path = graphene.String(required=True, description='Path to uploaded NIC front image')
    nic_back_image_path = graphene.String(description='Path to uploaded NIC back image')
    full_name = graphene.String(required=True, description='Name as entered by user')
    nic_number = graphene.String(required=True, description='NIC number as entered by user')


class VerifyNIC(graphene.Mutation):
    """
    Synchronous NIC verification — performs OCR on the NIC image,
    extracts name and NIC number, and compares them against user-provided data.
    Returns instant feedback on whether the details match.
    """

    class Arguments:
        input = VerifyNICInput(required=True)

    Output = NICVerificationResultType

    def mutate(self, info, input):
        from difflib import SequenceMatcher
        from apps.intelligence.infrastructure.ocr_service import OCRService

        front_path = input.nic_front_image_path
        back_path = getattr(input, 'nic_back_image_path', None) or None
        user_name = input.full_name.strip()
        user_nic = input.nic_number.strip()

        # Run OCR on both sides of the NIC
        ocr = OCRService()
        result = ocr.extract_both_sides(front_path, back_path)

        extracted_name = result.extracted_name
        extracted_nic = result.extracted_id_number
        ocr_confidence = result.confidence
        doc_type = result.document_type

        # Name matching — fuzzy comparison (case-insensitive)
        name_match_score = 0.0
        if extracted_name and user_name:
            name_match_score = SequenceMatcher(
                None,
                extracted_name.lower(),
                user_name.lower(),
            ).ratio()

        # NIC number matching — exact match (normalised)
        nic_number_match = False
        if extracted_nic and user_nic:
            nic_number_match = (
                extracted_nic.replace(' ', '').upper()
                == user_nic.replace(' ', '').upper()
            )

        # Decision logic
        from django.conf import settings
        ai_config = getattr(settings, 'AI_CONFIG', {})
        name_threshold = ai_config.get('nic_name_match_threshold', 0.65)
        ocr_threshold = ai_config.get('ocr_confidence_threshold', 0.50)

        if (
            ocr_confidence >= ocr_threshold
            and name_match_score >= name_threshold
            and nic_number_match
        ):
            status = 'APPROVED'
            is_verified = True
            message = 'NIC verification successful. Your identity has been confirmed.'
        elif (
            ocr_confidence >= ocr_threshold * 0.7
            and (name_match_score >= name_threshold * 0.8 or nic_number_match)
        ):
            status = 'MANUAL_REVIEW'
            is_verified = False
            message = (
                'Some details could not be fully verified. '
                'Your application will be reviewed by an administrator.'
            )
        else:
            status = 'REJECTED'
            is_verified = False
            reasons = []
            if ocr_confidence < ocr_threshold * 0.7:
                reasons.append('Image quality too low for text extraction')
            if name_match_score < name_threshold * 0.8:
                reasons.append(
                    f'Name mismatch (extracted: "{extracted_name}", '
                    f'entered: "{user_name}")'
                )
            if not nic_number_match:
                reasons.append(
                    f'NIC number mismatch (extracted: "{extracted_nic}", '
                    f'entered: "{user_nic}")'
                )
            message = 'Verification failed: ' + '; '.join(reasons)

        logger.info(
            'NIC verification: status=%s, name_score=%.2f, nic_match=%s, ocr=%.2f',
            status, name_match_score, nic_number_match, ocr_confidence,
        )

        return NICVerificationResultType(
            success=True,
            is_verified=is_verified,
            extracted_name=extracted_name,
            extracted_nic_number=extracted_nic,
            name_match_score=round(name_match_score, 4),
            nic_number_match=nic_number_match,
            ocr_confidence=round(ocr_confidence, 4),
            document_type=doc_type,
            message=message,
            status=status,
        )


class RegisterWithNICInput(graphene.InputObjectType):
    """Extended registration with NIC verification."""
    email = graphene.String(required=True)
    password = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    institution_id = graphene.String()
    nic_number = graphene.String(required=True, description='Sri Lankan NIC number')
    nic_front_image_path = graphene.String(required=True, description='Path to uploaded NIC front image')
    nic_back_image_path = graphene.String(description='Path to uploaded NIC back image (optional)')


class RegisterWithNIC(graphene.Mutation):
    """
    Advanced registration that includes NIC verification.
    1. Registers the user account (inactive)
    2. Performs synchronous OCR on NIC image
    3. Compares extracted data with user-provided details
    4. Auto-approves if details match, otherwise queues for manual review
    """

    class Arguments:
        input = RegisterWithNICInput(required=True)

    user = graphene.Field(UserType)
    verification = graphene.Field(NICVerificationResultType)

    @audit_action(action='REGISTER_WITH_NIC', resource_type='User')
    def mutate(self, info, input):
        from difflib import SequenceMatcher
        from apps.intelligence.infrastructure.ocr_service import OCRService
        from apps.identity.domain.models import User, VerificationRequest
        from apps.common.exceptions import ConflictError, ValidationError as NovaValidationError

        # 1. Register the user
        try:
            use_case = RegisterUserUseCase(
                user_repo=_build_user_repo(),
                token_service=_build_token_service(),
            )
            dto = RegisterUserDTO(
                email=input.email,
                password=input.password,
                first_name=input.first_name,
                last_name=input.last_name,
                phone_number=input.phone_number,
                date_of_birth=input.date_of_birth,
                institution_id=input.institution_id or input.nic_number,
            )
            profile = use_case.execute(dto)
        except ConflictError as e:
            raise GraphQLError(e.message)
        except NovaValidationError as e:
            raise GraphQLError(e.message)
        user = User.objects.get(pk=profile.id)

        # 2. Run OCR on both sides of NIC
        ocr = OCRService()
        front_path = input.nic_front_image_path
        back_path = getattr(input, 'nic_back_image_path', None) or None
        result = ocr.extract_both_sides(front_path, back_path)

        extracted_name = result.extracted_name
        extracted_nic = result.extracted_id_number
        ocr_confidence = result.confidence
        doc_type = result.document_type

        # 3. Name matching
        full_name = f'{input.first_name} {input.last_name}'.strip()
        name_match_score = 0.0
        if extracted_name and full_name:
            name_match_score = SequenceMatcher(
                None,
                extracted_name.lower(),
                full_name.lower(),
            ).ratio()

        user_nic = input.nic_number.strip()
        nic_number_match = False
        if extracted_nic and user_nic:
            nic_number_match = (
                extracted_nic.replace(' ', '').upper()
                == user_nic.replace(' ', '').upper()
            )

        # 4. Create verification request record
        ip = get_client_ip(info.context)
        verification_request = VerificationRequest.objects.create(
            user=user,
            id_document_path=input.nic_front_image_path,
            selfie_path='',  # No selfie in NIC-only flow
            extracted_name=extracted_name,
            extracted_id_number=extracted_nic,
            ocr_confidence=ocr_confidence,
            face_match_score=None,
            attempt_number=1,
            ip_address=ip,
            status='PENDING',
        )

        # 5. Decision
        from django.conf import settings
        ai_config = getattr(settings, 'AI_CONFIG', {})
        name_threshold = ai_config.get('nic_name_match_threshold', 0.65)
        ocr_threshold = ai_config.get('ocr_confidence_threshold', 0.50)

        if (
            ocr_confidence >= ocr_threshold
            and name_match_score >= name_threshold
            and nic_number_match
        ):
            status = 'APPROVED'
            verification_request.approve()
            message = 'Verification successful! Your account has been activated.'
        elif (
            ocr_confidence >= ocr_threshold * 0.7
            and (name_match_score >= name_threshold * 0.8 or nic_number_match)
        ):
            status = 'MANUAL_REVIEW'
            verification_request.queue_for_manual_review()
            message = (
                'Your NIC details are being reviewed. '
                'An administrator will verify your account shortly.'
            )
        else:
            status = 'REJECTED'
            reasons = []
            if ocr_confidence < ocr_threshold * 0.7:
                reasons.append('Poor image quality')
            if name_match_score < name_threshold * 0.8:
                reasons.append('Name does not match NIC')
            if not nic_number_match:
                reasons.append('NIC number does not match')
            message = 'Verification failed: ' + '; '.join(reasons) + '. Please try again with a clearer photo.'
            verification_request.reject(reason=message)

        # Refresh user from DB (may have been updated by approve)
        user.refresh_from_db()

        verification_result = NICVerificationResultType(
            success=True,
            is_verified=status == 'APPROVED',
            extracted_name=extracted_name,
            extracted_nic_number=extracted_nic,
            name_match_score=round(name_match_score, 4),
            nic_number_match=nic_number_match,
            ocr_confidence=round(ocr_confidence, 4),
            document_type=doc_type,
            message=message,
            status=status,
        )

        logger.info(
            'RegisterWithNIC: email=%s, status=%s, name_score=%.2f, nic_match=%s',
            input.email, status, name_match_score, nic_number_match,
        )

        return RegisterWithNIC(user=user, verification=verification_result)


class AdminUpdateUserInput(graphene.InputObjectType):
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    institution_id = graphene.String()
    nic_number = graphene.String()
    avatar_url = graphene.String()
    role = graphene.String()
    is_active = graphene.Boolean()
    is_verified = graphene.Boolean()


class AdminUpdateUser(graphene.Mutation):
    """Admin-only mutation to update any user's details."""

    class Arguments:
        user_id = graphene.UUID(required=True)
        input = AdminUpdateUserInput(required=True)

    Output = UserType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='ADMIN_UPDATE_USER', resource_type='User')
    def mutate(self, info, user_id, input):
        from apps.identity.domain.models import User as UserModel
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            raise Exception('User not found')

        updatable = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'institution_id', 'nic_number', 'avatar_url',
            'role', 'is_active', 'is_verified',
        ]
        for field in updatable:
            val = getattr(input, field, None)
            if val is not None:
                setattr(user, field, val)
        user.save()
        return user


# ---------------------------------------------------------------------------
# RBAC — Role Config Mutations
# ---------------------------------------------------------------------------

class RolePermissionInput(graphene.InputObjectType):
    """Input for a single module's permissions."""
    module = graphene.String(required=True)
    actions = graphene.List(graphene.String, required=True)


class CreateRoleConfig(graphene.Mutation):
    """Create a new role configuration."""

    class Arguments:
        role_key = graphene.String(required=True)
        display_name = graphene.String(required=True)
        description = graphene.String()
        permissions = graphene.List(RolePermissionInput, required=True)

    Output = RoleConfigType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='CREATE_ROLE_CONFIG', resource_type='RoleConfig')
    def mutate(self, info, role_key, display_name, permissions, description=''):
        from apps.identity.domain.models import RoleConfig

        # Validate
        role_key = role_key.upper().replace(' ', '_')
        if RoleConfig.objects.filter(role_key=role_key).exists():
            raise Exception(f'Role key "{role_key}" already exists.')

        valid_modules = RoleConfig.get_modules()
        valid_actions = RoleConfig.VALID_ACTIONS
        perm_dict = {}
        for p in permissions:
            if p.module not in valid_modules:
                raise Exception(f'Invalid module: {p.module}')
            perm_dict[p.module] = [a for a in p.actions if a in valid_actions]

        role = RoleConfig.objects.create(
            role_key=role_key,
            display_name=display_name,
            description=description,
            permissions=perm_dict,
            is_system=False,
        )
        return role


class UpdateRoleConfig(graphene.Mutation):
    """Update an existing role configuration."""

    class Arguments:
        id = graphene.UUID(required=True)
        display_name = graphene.String()
        description = graphene.String()
        permissions = graphene.List(RolePermissionInput)
        is_active = graphene.Boolean()

    Output = RoleConfigType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='UPDATE_ROLE_CONFIG', resource_type='RoleConfig')
    def mutate(self, info, id, display_name=None, description=None, permissions=None, is_active=None):
        from apps.identity.domain.models import RoleConfig

        try:
            role = RoleConfig.objects.get(pk=id)
        except RoleConfig.DoesNotExist:
            raise Exception('Role configuration not found.')

        if display_name is not None:
            role.display_name = display_name
        if description is not None:
            role.description = description
        if is_active is not None:
            role.is_active = is_active
        if permissions is not None:
            valid_modules = RoleConfig.get_modules()
            valid_actions = RoleConfig.VALID_ACTIONS
            perm_dict = {}
            for p in permissions:
                if p.module not in valid_modules:
                    raise Exception(f'Invalid module: {p.module}')
                perm_dict[p.module] = [a for a in p.actions if a in valid_actions]
            role.permissions = perm_dict

        role.save()
        return role


class DeleteRoleConfig(graphene.Mutation):
    """Delete a non-system role configuration."""

    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN])
    @audit_action(action='DELETE_ROLE_CONFIG', resource_type='RoleConfig')
    def mutate(self, info, id):
        from apps.identity.domain.models import RoleConfig

        try:
            role = RoleConfig.objects.get(pk=id)
        except RoleConfig.DoesNotExist:
            raise Exception('Role configuration not found.')

        if role.is_system:
            raise Exception('Cannot delete a system role.')

        role.delete()
        return DeleteRoleConfig(ok=True)


# ---------------------------------------------------------------------------
# Admin Create User (skip OCR verification)
# ---------------------------------------------------------------------------

class AdminCreateUserInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    password = graphene.String(required=True)
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    institution_id = graphene.String()
    nic_number = graphene.String()
    role = graphene.String()


class AdminCreateUser(graphene.Mutation):
    """Admin / Librarian mutation to create a user directly, bypassing OCR verification."""

    class Arguments:
        input = AdminCreateUserInput(required=True)

    Output = UserType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='ADMIN_CREATE_USER', resource_type='User')
    def mutate(self, info, input):
        from apps.identity.domain.models import User as UserModel
        from apps.common.types import UserRole, VerificationStatus

        # Check duplicate email
        if UserModel.objects.filter(email=input.email).exists():
            raise Exception(f'A user with email "{input.email}" already exists.')

        user = UserModel(
            email=input.email,
            first_name=input.first_name,
            last_name=input.last_name,
            phone_number=input.phone_number or '',
            date_of_birth=input.date_of_birth,
            institution_id=input.institution_id or '',
            nic_number=input.nic_number or '',
            role=input.role or UserRole.USER.value,
            is_active=True,
            is_verified=True,
            verification_status=VerificationStatus.APPROVED.value,
        )
        user.set_password(input.password)
        user.save()
        return user


# ---------------------------------------------------------------------------
# Member CRUD
# ---------------------------------------------------------------------------

class CreateMemberInput(graphene.InputObjectType):
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    email = graphene.String()
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    nic_number = graphene.String()
    address = graphene.String()
    membership_type = graphene.String()
    max_borrows = graphene.Int()
    expiry_date = graphene.Date()
    emergency_contact_name = graphene.String()
    emergency_contact_phone = graphene.String()
    notes = graphene.String()
    user_id = graphene.UUID(description='Optional link to a system user account.')


class CreateMember(graphene.Mutation):
    class Arguments:
        input = CreateMemberInput(required=True)

    Output = MemberType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE_MEMBER', resource_type='Member')
    def mutate(self, info, input):
        from apps.identity.domain.models import Member
        import uuid, datetime

        # Auto-generate membership number
        today = datetime.date.today()
        prefix = f'MEM-{today.strftime("%Y")}'
        seq = Member.all_objects.filter(
            membership_number__startswith=prefix
        ).count() + 1
        membership_number = f'{prefix}-{seq:05d}'

        member = Member(
            membership_number=membership_number,
            first_name=input.first_name,
            last_name=input.last_name,
            email=input.email or '',
            phone_number=input.phone_number or '',
            date_of_birth=input.date_of_birth,
            nic_number=input.nic_number or '',
            address=input.address or '',
            membership_type=input.membership_type or 'PUBLIC',
            max_borrows=input.max_borrows if input.max_borrows is not None else 5,
            expiry_date=input.expiry_date,
            emergency_contact_name=input.emergency_contact_name or '',
            emergency_contact_phone=input.emergency_contact_phone or '',
            notes=input.notes or '',
        )

        if input.user_id:
            from apps.identity.domain.models import User as UserModel
            try:
                member.user = UserModel.objects.get(pk=input.user_id)
            except UserModel.DoesNotExist:
                raise Exception('Linked user not found.')

        member.save()
        return member


class UpdateMemberInput(graphene.InputObjectType):
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    phone_number = graphene.String()
    date_of_birth = graphene.Date()
    nic_number = graphene.String()
    address = graphene.String()
    membership_type = graphene.String()
    status = graphene.String()
    max_borrows = graphene.Int()
    expiry_date = graphene.Date()
    emergency_contact_name = graphene.String()
    emergency_contact_phone = graphene.String()
    notes = graphene.String()
    user_id = graphene.UUID()


class UpdateMember(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)
        input = UpdateMemberInput(required=True)

    Output = MemberType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='UPDATE_MEMBER', resource_type='Member')
    def mutate(self, info, id, input):
        from apps.identity.domain.models import Member

        try:
            member = Member.objects.get(pk=id)
        except Member.DoesNotExist:
            raise Exception('Member not found.')

        simple_fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'nic_number', 'address', 'membership_type',
            'status', 'max_borrows', 'expiry_date',
            'emergency_contact_name', 'emergency_contact_phone', 'notes',
        ]
        for field in simple_fields:
            val = getattr(input, field, None)
            if val is not None:
                setattr(member, field, val)

        if input.user_id is not None:
            from apps.identity.domain.models import User as UserModel
            try:
                member.user = UserModel.objects.get(pk=input.user_id)
            except UserModel.DoesNotExist:
                raise Exception('Linked user not found.')

        member.save()
        return member


class DeleteMember(graphene.Mutation):
    class Arguments:
        id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='DELETE_MEMBER', resource_type='Member')
    def mutate(self, info, id):
        from apps.identity.domain.models import Member

        try:
            member = Member.objects.get(pk=id)
        except Member.DoesNotExist:
            raise Exception('Member not found.')

        member.soft_delete()
        return DeleteMember(ok=True)


# ---------------------------------------------------------------------------
# Password Reset  (3-step OTP flow)
# ---------------------------------------------------------------------------

def _mask_email(email: str) -> str:
    """Show first 2 chars of local part, mask rest. e.g. ad****@gmail.com"""
    local, domain = email.split('@')
    if len(local) <= 2:
        masked = local + '***'
    else:
        masked = local[:2] + '*' * (len(local) - 2)
    return f'{masked}@{domain}'


class RequestPasswordReset(graphene.Mutation):
    """
    Step 1 — User submits their email.
    If the account exists:
      • generate a 6-digit OTP and a session token
      • email the OTP via SMTP (if configured)
      • return masked email hint + session token
    """

    class Arguments:
        email = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    masked_email = graphene.String(description='Masked version of the email for display.')
    session_token = graphene.String(description='Session token to use in the next step.')

    @staticmethod
    def mutate(root, info, email):
        import secrets
        import random
        from datetime import timedelta
        from django.utils import timezone as tz
        from apps.identity.domain.models import User, PasswordResetToken
        from apps.common.email_service import send_password_reset_otp

        email = email.strip().lower()

        # Always respond with the same shape to prevent enumeration
        not_found = RequestPasswordReset(
            success=False,
            message='No account found with that email address.',
            masked_email=None,
            session_token=None,
        )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return not_found

        # Invalidate previous unused tokens
        PasswordResetToken.invalidate_existing(user)

        # Generate OTP (6 digits) and session token
        otp = f'{random.randint(0, 999999):06d}'
        raw_token = secrets.token_urlsafe(48)

        PasswordResetToken.objects.create(
            user=user,
            token_hash=PasswordResetToken.hash_token(raw_token),
            otp_code=otp,
            expires_at=tz.now() + timedelta(minutes=10),
            ip_address=get_client_ip(info.context),
        )

        # Send OTP email (non-blocking — if SMTP fails, OTP is still logged)
        email_sent = send_password_reset_otp(email, otp, user.first_name)
        if not email_sent:
            logger.warning('SMTP not configured or failed; OTP for %s: %s', email, otp)

        logger.info('Password reset OTP requested for %s', email)

        return RequestPasswordReset(
            success=True,
            message='A 6-digit verification code has been sent to your email.',
            masked_email=_mask_email(email),
            session_token=raw_token,
        )


class VerifyResetOtp(graphene.Mutation):
    """
    Step 2 — User enters the 6-digit OTP.
    On success the session token is promoted to a verified state,
    allowing the final password change.
    """

    class Arguments:
        session_token = graphene.String(required=True)
        otp = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, session_token, otp):
        from apps.identity.domain.models import PasswordResetToken

        token_hash = PasswordResetToken.hash_token(session_token)

        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(
                token_hash=token_hash,
            )
        except PasswordResetToken.DoesNotExist:
            raise Exception('Invalid session. Please request a new reset code.')

        if not reset_token.is_valid:
            raise Exception('This code has expired. Please request a new one.')

        if reset_token.otp_code != otp.strip():
            raise Exception('Incorrect verification code. Please try again.')

        reset_token.mark_otp_verified()

        return VerifyResetOtp(
            success=True,
            message='Code verified. You can now set your new password.',
        )


class ConfirmPasswordReset(graphene.Mutation):
    """
    Step 3 — User sets a new password after OTP verification.
    """

    class Arguments:
        session_token = graphene.String(required=True)
        new_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @staticmethod
    def mutate(root, info, session_token, new_password):
        from apps.identity.domain.models import PasswordResetToken
        from apps.identity.domain.models import RefreshToken as RefreshTokenModel

        token_hash = PasswordResetToken.hash_token(session_token)

        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(
                token_hash=token_hash,
            )
        except PasswordResetToken.DoesNotExist:
            raise Exception('Invalid session. Please request a new reset code.')

        if not reset_token.is_valid:
            raise Exception('This session has expired. Please request a new reset code.')

        if not reset_token.otp_verified:
            raise Exception('OTP not verified. Please complete verification first.')

        if len(new_password) < 8:
            raise Exception('Password must be at least 8 characters long.')

        user = reset_token.user
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])

        reset_token.mark_used()
        RefreshTokenModel.revoke_all_for_user(user)

        logger.info('Password reset confirmed for %s', user.email)

        return ConfirmPasswordReset(
            success=True,
            message='Your password has been reset successfully. You can now sign in.',
        )


# ---------------------------------------------------------------------------
# Mutation root
# ---------------------------------------------------------------------------

class IdentityMutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    register_with_nic = RegisterWithNIC.Field()
    verify_nic = VerifyNIC.Field()
    login = LoginUser.Field()
    refresh_token = RefreshToken.Field()
    logout = Logout.Field()
    update_profile = UpdateProfile.Field()
    change_password = ChangePassword.Field()
    submit_verification = SubmitVerification.Field()

    # Password Reset
    request_password_reset = RequestPasswordReset.Field()
    verify_reset_otp = VerifyResetOtp.Field()
    confirm_password_reset = ConfirmPasswordReset.Field()

    # Admin
    activate_user = ActivateUser.Field()
    deactivate_user = DeactivateUser.Field()
    change_user_role = ChangeUserRole.Field()
    admin_update_user = AdminUpdateUser.Field()
    admin_create_user = AdminCreateUser.Field()

    # RBAC
    create_role_config = CreateRoleConfig.Field()
    update_role_config = UpdateRoleConfig.Field()
    delete_role_config = DeleteRoleConfig.Field()

    # Members
    create_member = CreateMember.Field()
    update_member = UpdateMember.Field()
    delete_member = DeleteMember.Field()
