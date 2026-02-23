/**
 * System Settings GraphQL queries.
 */

import { gql } from '@apollo/client';

export const GET_SYSTEM_SETTINGS = gql`
  query GetSystemSettings($category: String) {
    systemSettings(category: $category) {
      id
      key
      value
      valueType
      category
      label
      description
      isSensitive
      typedValue
      updatedAt
      updatedBy {
        id
        firstName
        lastName
      }
    }
  }
`;
