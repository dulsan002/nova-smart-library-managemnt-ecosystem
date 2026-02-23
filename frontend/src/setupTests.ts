/**
 * Test setup — loaded before every test file.
 *
 * Extends expect with jest-dom matchers (toBeInTheDocument, etc.).
 * Provides a clean localStorage/sessionStorage between tests.
 */

import '@testing-library/jest-dom';

// Reset all mocks and storage between tests
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});
