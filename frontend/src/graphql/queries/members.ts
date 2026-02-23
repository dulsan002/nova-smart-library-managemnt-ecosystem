/**
 * Members GraphQL queries.
 */

import { gql } from '@apollo/client';

export const MEMBER_FRAGMENT = gql`
  fragment MemberFields on MemberType {
    id
    membershipNumber
    firstName
    lastName
    email
    phoneNumber
    dateOfBirth
    nicNumber
    address
    membershipType
    status
    joinedDate
    expiryDate
    maxBorrows
    emergencyContactName
    emergencyContactPhone
    notes
    fullName
    isActiveMember
    createdAt
    updatedAt
    user {
      id
      email
      fullName
    }
  }
`;

export const GET_MEMBERS = gql`
  ${MEMBER_FRAGMENT}
  query GetMembers(
    $first: Int
    $after: String
    $status: String
    $membershipType: String
    $search: String
  ) {
    members(
      first: $first
      after: $after
      status: $status
      membershipType: $membershipType
      search: $search
    ) {
      edges {
        node {
          ...MemberFields
        }
        cursor
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
      totalCount
    }
  }
`;

export const GET_MEMBER = gql`
  ${MEMBER_FRAGMENT}
  query GetMember($id: UUID!) {
    member(id: $id) {
      ...MemberFields
    }
  }
`;
