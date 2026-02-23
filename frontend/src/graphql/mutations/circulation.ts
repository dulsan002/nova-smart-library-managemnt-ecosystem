/**
 * Circulation GraphQL mutations.
 *
 * Flow: reserveBook → confirmPickup (librarian) → renewBorrow → returnBook (librarian)
 */

import { gql } from '@apollo/client';

/** Reserve a book. If a copy is available, it's assigned immediately with a 12 h pickup window. */
export const RESERVE_BOOK = gql`
  mutation ReserveBook($bookId: UUID!) {
    reserveBook(bookId: $bookId) {
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
        availableCopies
      }
    }
  }
`;

/** Librarian confirms physical pickup → creates BorrowRecord. */
export const CONFIRM_PICKUP = gql`
  mutation ConfirmPickup($reservationId: UUID!) {
    confirmPickup(reservationId: $reservationId) {
      id
      status
      borrowedAt
      dueDate
      user {
        id
        email
        firstName
        lastName
      }
      bookCopy {
        id
        barcode
        book {
          id
          title
        }
      }
    }
  }
`;

/** Librarian confirms physical return. */
export const RETURN_BOOK = gql`
  mutation ReturnBook($borrowId: UUID!, $condition: String) {
    returnBook(borrowId: $borrowId, condition: $condition) {
      id
      status
      returnedAt
      bookCopy {
        id
        barcode
        book {
          id
          title
        }
      }
    }
  }
`;

/** User renews a borrow via the app. */
export const RENEW_BORROW = gql`
  mutation RenewBorrow($borrowId: UUID!) {
    renewBorrow(borrowId: $borrowId) {
      id
      dueDate
      renewalCount
      canRenew
    }
  }
`;

/** Cancel a reservation (user or staff). */
export const CANCEL_RESERVATION = gql`
  mutation CancelReservation($reservationId: UUID!) {
    cancelReservation(reservationId: $reservationId) {
      id
      status
    }
  }
`;

export const PAY_FINE = gql`
  mutation PayFine($fineId: UUID!, $amount: Float) {
    payFine(fineId: $fineId, amount: $amount) {
      id
      paidAmount
      status
    }
  }
`;

export const WAIVE_FINE = gql`
  mutation WaiveFine($fineId: UUID!) {
    waiveFine(fineId: $fineId) {
      id
      status
    }
  }
`;

/** Staff lifts a reservation ban early. */
export const LIFT_RESERVATION_BAN = gql`
  mutation LiftReservationBan($banId: UUID!) {
    liftReservationBan(banId: $banId) {
      id
      isActive
      liftedAt
    }
  }
`;
