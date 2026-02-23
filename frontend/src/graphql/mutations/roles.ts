/**
 * RBAC — Role configuration mutations.
 */

import { gql } from '@apollo/client';

export const CREATE_ROLE_CONFIG = gql`
  mutation CreateRoleConfig(
    $roleKey: String!
    $displayName: String!
    $description: String
    $permissions: [RolePermissionInput]!
  ) {
    createRoleConfig(
      roleKey: $roleKey
      displayName: $displayName
      description: $description
      permissions: $permissions
    ) {
      id
      roleKey
      displayName
      description
      permissions
      isSystem
      isActive
    }
  }
`;

export const UPDATE_ROLE_CONFIG = gql`
  mutation UpdateRoleConfig(
    $id: UUID!
    $displayName: String
    $description: String
    $permissions: [RolePermissionInput]
    $isActive: Boolean
  ) {
    updateRoleConfig(
      id: $id
      displayName: $displayName
      description: $description
      permissions: $permissions
      isActive: $isActive
    ) {
      id
      roleKey
      displayName
      description
      permissions
      isSystem
      isActive
    }
  }
`;

export const DELETE_ROLE_CONFIG = gql`
  mutation DeleteRoleConfig($id: UUID!) {
    deleteRoleConfig(id: $id) {
      ok
    }
  }
`;
