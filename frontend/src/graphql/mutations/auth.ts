/**
 * Auth GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const LOGIN = gql`
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      user {
        id
        email
        firstName
        lastName
        role
        isVerified
        avatarUrl
      }
      tokens {
        accessToken
        refreshToken
      }
    }
  }
`;

export const REGISTER = gql`
  mutation Register($input: RegisterInput!) {
    registerUser(input: $input) {
      id
      email
      firstName
      lastName
      role
      isVerified
    }
  }
`;

export const REFRESH_TOKEN = gql`
  mutation RefreshToken($refreshToken: String!) {
    refreshToken(refreshToken: $refreshToken) {
      accessToken
      refreshToken
    }
  }
`;

export const LOGOUT = gql`
  mutation Logout($refreshTokenHash: String!, $revokeAll: Boolean) {
    logout(refreshTokenHash: $refreshTokenHash, revokeAll: $revokeAll) {
      success
    }
  }
`;

export const CHANGE_PASSWORD = gql`
  mutation ChangePassword($input: ChangePasswordInput!) {
    changePassword(input: $input) {
      success
    }
  }
`;

export const UPDATE_PROFILE = gql`
  mutation UpdateProfile($input: UpdateProfileInput!) {
    updateProfile(input: $input) {
      id
      email
      firstName
      lastName
      phoneNumber
      dateOfBirth
      avatarUrl
    }
  }
`;

export const VERIFY_NIC = gql`
  mutation VerifyNIC($input: VerifyNICInput!) {
    verifyNic(input: $input) {
      success
      isVerified
      extractedName
      extractedNicNumber
      nameMatchScore
      nicNumberMatch
      ocrConfidence
      documentType
      message
      status
    }
  }
`;

export const REGISTER_WITH_NIC = gql`
  mutation RegisterWithNIC($input: RegisterWithNICInput!) {
    registerWithNic(input: $input) {
      user {
        id
        email
        firstName
        lastName
        role
        isVerified
        verificationStatus
      }
      verification {
        success
        isVerified
        extractedName
        extractedNicNumber
        nameMatchScore
        nicNumberMatch
        ocrConfidence
        documentType
        message
        status
      }
    }
  }
`;

export const REQUEST_PASSWORD_RESET = gql`
  mutation RequestPasswordReset($email: String!) {
    requestPasswordReset(email: $email) {
      success
      message
      maskedEmail
      sessionToken
    }
  }
`;

export const VERIFY_RESET_OTP = gql`
  mutation VerifyResetOtp($sessionToken: String!, $otp: String!) {
    verifyResetOtp(sessionToken: $sessionToken, otp: $otp) {
      success
      message
    }
  }
`;

export const CONFIRM_PASSWORD_RESET = gql`
  mutation ConfirmPasswordReset($sessionToken: String!, $newPassword: String!) {
    confirmPasswordReset(sessionToken: $sessionToken, newPassword: $newPassword) {
      success
      message
    }
  }
`;
