/**
 * Admin user management GraphQL queries.
 */

import { gql } from '@apollo/client';

export const GET_USERS = gql`
  query GetUsers(
    $first: Int
    $after: String
    $role: String
    $isActive: Boolean
    $search: String
  ) {
    users(
      first: $first
      after: $after
      role: $role
      isActive: $isActive
      search: $search
    ) {
      edges {
        node {
          id
          email
          firstName
          lastName
          role
          isActive
          isVerified
          createdAt
          lastLoginAt
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
`;

export const GET_USER = gql`
  query GetUser($id: UUID!) {
    user(id: $id) {
      id
      email
      firstName
      lastName
      fullName
      role
      isActive
      isVerified
      verificationStatus
      phoneNumber
      dateOfBirth
      avatarUrl
      institutionId
      nicNumber
      loginCount
      lastLoginAt
      createdAt
      updatedAt
    }
  }
`;

export const USER_BORROWS = gql`
  query UserBorrows($userId: UUID!, $status: String, $limit: Int) {
    userBorrows(userId: $userId, status: $status, limit: $limit) {
      id
      status
      borrowedAt
      dueDate
      returnedAt
      renewalCount
      isOverdue
      daysOverdue
      bookCopy {
        barcode
        book {
          id
          title
          coverImageUrl
        }
      }
    }
  }
`;

export const USER_FINES = gql`
  query UserFines($userId: UUID!, $status: String) {
    userFines(userId: $userId, status: $status) {
      id
      amount
      paidAmount
      outstanding
      status
      reason
      description
      issuedAt
      borrowRecord {
        id
        bookCopy {
          book {
            title
          }
        }
      }
    }
  }
`;

export const USER_RESERVATIONS = gql`
  query UserReservations($userId: UUID!) {
    userReservations(userId: $userId) {
      id
      status
      reservedAt
      readyAt
      expiresAt
      queuePosition
      book {
        id
        title
        coverImageUrl
      }
    }
  }
`;

export const USER_ENGAGEMENT = gql`
  query UserEngagement($userId: UUID!) {
    userEngagement(userId: $userId) {
      id
      totalKp
      level
      levelTitle
      currentStreak
      longestStreak
      lastActivityDate
      explorerKp
      scholarKp
      connectorKp
      achieverKp
      dedicatedKp
      rank
      rankPercentile
    }
  }
`;

export const USER_ACHIEVEMENTS = gql`
  query UserAchievements($userId: UUID!) {
    userAchievements(userId: $userId) {
      id
      earnedAt
      kpAwarded
      achievement {
        id
        name
        description
        category
        icon
        kpReward
        rarity
      }
    }
  }
`;
