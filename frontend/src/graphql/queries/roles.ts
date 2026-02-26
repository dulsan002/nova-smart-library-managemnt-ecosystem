/**
 * RBAC —  Role configuration queries.
 */

import { gql } from '@apollo/client';

export const GET_ROLE_CONFIGS = gql`
  query GetRoleConfigs {
    roleConfigs {
      id
      roleKey
      displayName
      description
      permissions
      isSystem
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const GET_ROLE_CONFIG = gql`
  query GetRoleConfig($id: UUID!) {
    roleConfig(id: $id) {
      id
      roleKey
      displayName
      description
      permissions
      isSystem
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const GET_AVAILABLE_MODULES = gql`
  query GetAvailableModules {
    availableModules {
      key
      label
    }
  }
`;

/**
 * Fetch the current authenticated user's role permissions.
 * Returns a JSON map: { module_key: ["create","read","update","delete"], ... }
 */
export const MY_PERMISSIONS = gql`
  query MyPermissions {
    myPermissions
  }
`;
