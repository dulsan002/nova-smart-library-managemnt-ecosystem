/**
 * Auth GraphQL queries.
 */

import { gql } from '@apollo/client';

export const ME = gql`
  query Me {
    me {
      id
      email
      firstName
      lastName
      role
      isVerified
      avatarUrl
      phoneNumber
      dateOfBirth
      institutionId
      createdAt
    }
  }
`;
