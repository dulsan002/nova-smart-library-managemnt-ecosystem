/**
 * Circulation GraphQL queries.
 */

import { gql } from '@apollo/client';

export const MY_BORROWS = gql`
  query MyBorrows($status: String, $limit: Int) {
    myBorrows(status: $status, limit: $limit) {
      id
      status
      borrowedAt
      dueDate
      returnedAt
      renewalCount
      maxRenewals
      isOverdue
      daysOverdue
      canRenew
      bookCopy {
        id
        barcode
        floorNumber
        shelfNumber
        book {
          id
          title
          coverImageUrl
          authors {
            firstName
            lastName
          }
        }
      }
    }
  }
`;

export const MY_RESERVATIONS = gql`
  query MyReservations {
    myReservations {
      id
      status
      reservedAt
      readyAt
      expiresAt
      queuePosition
      pickupLocation
      hoursUntilExpiry
      assignedCopy {
        id
        barcode
        floorNumber
        shelfNumber
      }
      book {
        id
        title
        coverImageUrl
        authors {
          firstName
          lastName
        }
      }
    }
  }
`;

export const MY_FINES = gql`
  query MyFines($status: String) {
    myFines(status: $status) {
      id
      amount
      paidAmount
      outstanding
      status
      reason
      description
      issuedAt
      createdAt
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

export const MY_RESERVATION_BAN = gql`
  query MyReservationBan {
    myReservationBan {
      id
      reason
      noShowCount
      bannedAt
      expiresAt
      isActive
    }
  }
`;

export const ALL_BORROWS = gql`
  query AllBorrows($first: Int, $after: String, $status: String, $userId: UUID) {
    allBorrows(first: $first, after: $after, status: $status, userId: $userId) {
      edges {
        node {
          id
          status
          borrowedAt
          dueDate
          returnedAt
          isOverdue
          daysOverdue
          user {
            id
            email
            firstName
            lastName
          }
          bookCopy {
            barcode
            book {
              title
            }
          }
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

export const OVERDUE_BORROWS = gql`
  query OverdueBorrows($limit: Int) {
    overdueBorrows(limit: $limit) {
      id
      borrowedAt
      dueDate
      daysOverdue
      user {
        id
        email
        firstName
        lastName
      }
      bookCopy {
        barcode
        book {
          title
        }
      }
    }
  }
`;

export const PENDING_PICKUPS = gql`
  query PendingPickups($limit: Int) {
    pendingPickups(limit: $limit) {
      id
      status
      expiresAt
      hoursUntilExpiry
      pickupLocation
      user {
        id
        email
        firstName
        lastName
      }
      book {
        id
        title
      }
      assignedCopy {
        id
        barcode
        floorNumber
        shelfNumber
      }
    }
  }
`;
