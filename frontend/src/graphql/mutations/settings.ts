/**
 * System Settings GraphQL mutations.
 */

import { gql } from '@apollo/client';

export const UPDATE_SYSTEM_SETTING = gql`
  mutation UpdateSystemSetting($key: String!, $value: String!) {
    updateSystemSetting(key: $key, value: $value) {
      id
      key
      value
      typedValue
      updatedAt
    }
  }
`;

export const SYNC_DEFAULT_SETTINGS = gql`
  mutation SyncDefaultSettings {
    syncDefaultSettings {
      createdCount
    }
  }
`;
