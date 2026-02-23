/**
 * Admin GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const ACTIVATE_USER = gql`
  mutation ActivateUser($userId: UUID!) {
    activateUser(userId: $userId) {
      id
      isActive
    }
  }
`;

export const DEACTIVATE_USER = gql`
  mutation DeactivateUser($userId: UUID!) {
    deactivateUser(userId: $userId) {
      id
      isActive
    }
  }
`;

export const CHANGE_USER_ROLE = gql`
  mutation ChangeUserRole($userId: UUID!, $newRole: String!) {
    changeUserRole(userId: $userId, newRole: $newRole) {
      id
      role
    }
  }
`;

export const ADMIN_AWARD_KP = gql`
  mutation AdminAwardKP(
    $userId: UUID!
    $points: Int!
    $reason: String!
    $dimension: String
  ) {
    adminAwardKp(
      userId: $userId
      points: $points
      reason: $reason
      dimension: $dimension
    ) {
      success
      actualPoints
    }
  }
`;

export const ADMIN_UPDATE_USER = gql`
  mutation AdminUpdateUser($userId: UUID!, $input: AdminUpdateUserInput!) {
    adminUpdateUser(userId: $userId, input: $input) {
      id
      email
      firstName
      lastName
      role
      isActive
      isVerified
      phoneNumber
      dateOfBirth
      avatarUrl
      institutionId
      nicNumber
    }
  }
`;

export const ADMIN_CREATE_USER = gql`
  mutation AdminCreateUser($input: AdminCreateUserInput!) {
    adminCreateUser(input: $input) {
      id
      email
      firstName
      lastName
      role
      isActive
      isVerified
      phoneNumber
      dateOfBirth
      institutionId
      nicNumber
    }
  }
`;
