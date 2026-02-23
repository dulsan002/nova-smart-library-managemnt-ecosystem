/**
 * Members GraphQL mutations.
 */

import { gql } from '@apollo/client';
import { MEMBER_FRAGMENT } from '@/graphql/queries/members';

export const CREATE_MEMBER = gql`
  ${MEMBER_FRAGMENT}
  mutation CreateMember($input: CreateMemberInput!) {
    createMember(input: $input) {
      ...MemberFields
    }
  }
`;

export const UPDATE_MEMBER = gql`
  ${MEMBER_FRAGMENT}
  mutation UpdateMember($id: UUID!, $input: UpdateMemberInput!) {
    updateMember(id: $id, input: $input) {
      ...MemberFields
    }
  }
`;

export const DELETE_MEMBER = gql`
  mutation DeleteMember($id: UUID!) {
    deleteMember(id: $id) {
      ok
    }
  }
`;
