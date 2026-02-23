/**
 * Tests for application constants.
 */

import { ROLES, ADMIN_ROLES, STAFF_ROLES, BORROW_STATUS, RESERVATION_STATUS, FINE_STATUS } from '@/lib/constants';

describe('constants', () => {
  describe('ROLES', () => {
    it('has all expected roles', () => {
      expect(ROLES.SUPER_ADMIN).toBe('SUPER_ADMIN');
      expect(ROLES.LIBRARIAN).toBe('LIBRARIAN');
      expect(ROLES.LIBRARY_ASSISTANT).toBe('LIBRARY_ASSISTANT');
      expect(ROLES.MEMBER).toBe('MEMBER');
      expect(ROLES.STUDENT).toBe('STUDENT');
      expect(ROLES.GUEST).toBe('GUEST');
    });

    it('has exactly 6 roles', () => {
      expect(Object.keys(ROLES)).toHaveLength(6);
    });
  });

  describe('ADMIN_ROLES', () => {
    it('includes SUPER_ADMIN, LIBRARIAN, LIBRARY_ASSISTANT', () => {
      expect(ADMIN_ROLES).toContain('SUPER_ADMIN');
      expect(ADMIN_ROLES).toContain('LIBRARIAN');
      expect(ADMIN_ROLES).toContain('LIBRARY_ASSISTANT');
    });

    it('does not include MEMBER', () => {
      expect(ADMIN_ROLES).not.toContain('MEMBER');
    });
  });

  describe('STAFF_ROLES', () => {
    it('includes only SUPER_ADMIN and LIBRARIAN', () => {
      expect(STAFF_ROLES).toEqual(['SUPER_ADMIN', 'LIBRARIAN']);
    });
  });

  describe('BORROW_STATUS', () => {
    it('has all statuses', () => {
      expect(BORROW_STATUS.ACTIVE).toBe('ACTIVE');
      expect(BORROW_STATUS.RETURNED).toBe('RETURNED');
      expect(BORROW_STATUS.OVERDUE).toBe('OVERDUE');
      expect(BORROW_STATUS.LOST).toBe('LOST');
    });
  });

  describe('RESERVATION_STATUS', () => {
    it('has all statuses', () => {
      expect(Object.keys(RESERVATION_STATUS)).toHaveLength(5);
    });
  });

  describe('FINE_STATUS', () => {
    it('has PENDING, PAID, WAIVED, OVERDUE', () => {
      expect(FINE_STATUS.PENDING).toBe('PENDING');
      expect(FINE_STATUS.PAID).toBe('PAID');
      expect(FINE_STATUS.WAIVED).toBe('WAIVED');
    });
  });
});
