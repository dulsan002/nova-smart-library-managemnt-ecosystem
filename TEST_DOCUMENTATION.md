# Nova Smart Library Management Ecosystem — Test Documentation

---

## 1. Test Plan

### 1.1 Project Overview

**Project Name:** Nova Smart Library Management Ecosystem  
**Version:** 1.0  
**Prepared By:** QA Engineering Team  
**Date:** February 27, 2026  
**Document Type:** Master Test Plan & Test Case Repository

### 1.2 Purpose

This document defines the comprehensive test strategy, scope, approach, and detailed test cases for the Nova Smart Library Management Ecosystem — a full-stack web application built with Django (GraphQL API) backend and React (TypeScript) frontend. The system manages library operations across 9 bounded contexts: Identity, Catalog, Circulation, Digital Content, Engagement, Intelligence, Governance, Asset Management, and HR.

### 1.3 Scope

#### In Scope

| Module | Coverage Areas |
|--------|---------------|
| Identity & Authentication | Registration, login, JWT tokens, password reset, profile management, role-based access, NIC verification, member management |
| Catalog Management | Book CRUD, author CRUD, category management, book copies, reviews, search |
| Circulation | Reservations, borrowing, returns, renewals, fines, overdue handling |
| Digital Content | Digital asset management, reading sessions, bookmarks, highlights, user library |
| Engagement & Gamification | Knowledge Points (KP), achievements, streaks, leaderboard, daily activities |
| Intelligence & AI | Recommendations, trending books, search analytics, AI provider configuration |
| Governance & Audit | Audit logs, security events, KP ledger |
| Asset Management | Physical library assets, maintenance logs, disposals, depreciation |
| HR Management | Departments, employees, job vacancies, applications |
| Frontend UI | Page navigation, form validation, responsive layout, route guards |
| Cross-Cutting | Pagination, error handling, CORS, authorization, input sanitization |

#### Out of Scope

- Performance/load testing
- Penetration testing
- Mobile native applications
- Third-party AI provider integration testing (Ollama, Gemini, OpenAI external services)
- Email delivery (SMTP server testing)

### 1.4 Test Approach

| Test Type | Description | Tools |
|-----------|-------------|-------|
| Functional Testing | Verify all features work per requirements | Manual, pytest, Vitest |
| Integration Testing | Verify frontend-backend GraphQL communication | curl, Apollo DevTools |
| UI Testing | Verify frontend rendering, navigation, forms | Browser (Chrome/Firefox) |
| Authorization Testing | Verify RBAC and role-based access controls | Manual, GraphQL introspection |
| Boundary Testing | Verify input limits, edge cases, constraints | Manual |
| Negative Testing | Verify proper error handling for invalid inputs | Manual |
| Regression Testing | Re-verify previously fixed defects | Manual |

### 1.5 Test Environment

| Component | Details |
|-----------|---------|
| Backend | Django 4.2, Python 3.12, Graphene-Django 3.2.3, PostgreSQL |
| Frontend | React 18, Vite 6.4, TypeScript, Apollo Client 3.11 |
| Database | PostgreSQL (port 5433) |
| Authentication | JWT (django-graphql-jwt 0.4.0 + custom JWTTokenService) |
| OS | Linux (Ubuntu) |
| Browser | Chrome 120+, Firefox 120+ |

### 1.6 Test Data

| Credential | Role | Password |
|------------|------|----------|
| admin@nova.local | SUPER_ADMIN | NovaTest@2026 |
| librarian@nova.local | LIBRARIAN | NovaTest@2026 |
| assistant@nova.local | ASSISTANT | NovaTest@2026 |
| alice@nova.local | USER | NovaTest@2026 |
| bob@nova.local | USER | NovaTest@2026 |
| charlie@nova.local | USER | NovaTest@2026 |
| diana@nova.local | USER (unverified) | NovaTest@2026 |
| eve@nova.local | USER (unverified) | NovaTest@2026 |

### 1.7 Entry Criteria

- Backend and frontend servers are running without errors
- Database is seeded with test data (`python manage.py seed_data`)
- All migrations are applied
- Test environment is accessible at `http://localhost:3000` (frontend) and `http://localhost:8000` (backend)

### 1.8 Exit Criteria

- All 100 test cases executed
- All critical and high-severity defects resolved
- Pass rate ≥ 95% for critical path test cases
- All modules have at least basic coverage

### 1.9 Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database connection failure | High | Verify PostgreSQL is running before test execution |
| Missing seed data | Medium | Run `seed_data` command before each full test cycle |
| JWT token expiry during testing | Low | Tokens expire after 15 minutes; re-login as needed |
| Redis unavailable (Celery tasks) | Medium | Background tasks (recommendations, trending) will not execute; test synchronous features only |

### 1.10 Deliverables

- This Test Documentation (100 test cases)
- Defect reports (logged separately)
- Test execution summary report

---

## 2. Test Cases

> **Legend:**  
> - **Pre-Conditions**: Setup required before executing the test  
> - **Test Steps**: Sequential actions to perform  
> - **Expected Results**: The correct system behavior  
> - **Actual Results**: To be filled during test execution  

---

### Module 1: Authentication & Login (TC-001 to TC-012)

---

| Field | Details |
|-------|---------|
| *ID* | TC-001 |
| *Title* | Successful login with valid credentials |
| *Pre-Conditions* | User `admin@nova.local` exists in the database. Application is running at `http://localhost:3000`. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/login`. 2. Enter email: `admin@nova.local`. 3. Enter password: `NovaTest@2026`. 4. Click the "Sign In" button. |
| *Expected Results* | User is redirected to the dashboard page (`/dashboard`). The user's name is displayed in the header. JWT access token is stored in the browser. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-002 |
| *Title* | Login with invalid password |
| *Pre-Conditions* | User `admin@nova.local` exists in the database. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/login`. 2. Enter email: `admin@nova.local`. 3. Enter password: `WrongPassword123`. 4. Click the "Sign In" button. |
| *Expected Results* | An error message is displayed: "Invalid credentials" or similar. User remains on the login page. No token is stored. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-003 |
| *Title* | Login with non-existent email |
| *Pre-Conditions* | No user with email `nonexistent@nova.local` exists. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/login`. 2. Enter email: `nonexistent@nova.local`. 3. Enter password: `NovaTest@2026`. 4. Click the "Sign In" button. |
| *Expected Results* | An error message is displayed indicating invalid credentials. User remains on the login page. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-004 |
| *Title* | Login with empty email field |
| *Pre-Conditions* | Application is running. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/login`. 2. Leave the email field empty. 3. Enter password: `NovaTest@2026`. 4. Click the "Sign In" button. |
| *Expected Results* | A validation message is displayed: "Email is required" or the form prevents submission. User remains on the login page. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-005 |
| *Title* | Login with empty password field |
| *Pre-Conditions* | Application is running. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/login`. 2. Enter email: `admin@nova.local`. 3. Leave the password field empty. 4. Click the "Sign In" button. |
| *Expected Results* | A validation message is displayed: "Password is required" or the form prevents submission. User remains on the login page. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-006 |
| *Title* | Successful logout |
| *Pre-Conditions* | User is logged in as `admin@nova.local`. |
| *Test Steps* | 1. Click on the user avatar/menu in the header. 2. Click the "Logout" option. |
| *Expected Results* | User is redirected to the login page (`/login`). JWT tokens are cleared from browser storage. Accessing protected routes redirects to login. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-007 |
| *Title* | Access protected route without authentication |
| *Pre-Conditions* | User is not logged in (no tokens stored). |
| *Test Steps* | 1. Open a new browser tab. 2. Navigate directly to `http://localhost:3000/dashboard`. |
| *Expected Results* | User is automatically redirected to the login page (`/login`). The dashboard is not displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-008 |
| *Title* | JWT token refresh |
| *Pre-Conditions* | User is logged in. Access token and refresh token are stored. |
| *Test Steps* | 1. Log in as `admin@nova.local`. 2. Send a GraphQL `refreshToken` mutation using the stored refresh token via curl or Apollo DevTools. |
| *Expected Results* | A new access token and refresh token are returned. The old tokens are invalidated. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-009 |
| *Title* | Login with different user roles |
| *Pre-Conditions* | Users with all roles exist: SUPER_ADMIN, LIBRARIAN, ASSISTANT, USER. |
| *Test Steps* | 1. Log in as `librarian@nova.local` (LIBRARIAN). 2. Verify access to admin panel. 3. Log out. 4. Log in as `alice@nova.local` (USER). 5. Verify no access to admin panel. |
| *Expected Results* | Librarian can access admin pages. Regular USER cannot see or access admin routes and is redirected when trying to access `/admin/*`. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-010 |
| *Title* | Password reset — request OTP |
| *Pre-Conditions* | User `alice@nova.local` exists in the database. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/forgot-password`. 2. Enter email: `alice@nova.local`. 3. Click "Send Reset Link" or "Submit". |
| *Expected Results* | A success message is displayed indicating that a password reset email has been sent. The system generates an OTP and session token. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-011 |
| *Title* | User registration with valid data |
| *Pre-Conditions* | No user with email `newuser@nova.local` exists. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/register`. 2. Enter first name: `Test`. 3. Enter last name: `User`. 4. Enter email: `newuser@nova.local`. 5. Enter password: `StrongPass@123`. 6. Confirm password: `StrongPass@123`. 7. Click "Register". |
| *Expected Results* | Registration succeeds. A success message is displayed. The user account is created (may require verification before login). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-012 |
| *Title* | Registration with already existing email |
| *Pre-Conditions* | User `admin@nova.local` already exists. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/register`. 2. Enter first name: `Duplicate`. 3. Enter last name: `User`. 4. Enter email: `admin@nova.local`. 5. Enter password: `StrongPass@123`. 6. Confirm password: `StrongPass@123`. 7. Click "Register". |
| *Expected Results* | An error message is displayed indicating the email is already registered. The duplicate account is not created. |
| *Actual Results* | |

---

### Module 2: User Profile & Management (TC-013 to TC-020)

---

| Field | Details |
|-------|---------|
| *ID* | TC-013 |
| *Title* | View user profile |
| *Pre-Conditions* | User is logged in as `alice@nova.local`. |
| *Test Steps* | 1. Navigate to `http://localhost:3000/profile`. |
| *Expected Results* | The profile page displays the user's first name, last name, email, role, and verification status correctly. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-014 |
| *Title* | Update user profile — first and last name |
| *Pre-Conditions* | User is logged in as `alice@nova.local`. |
| *Test Steps* | 1. Navigate to `/profile`. 2. Update first name to `Alicia`. 3. Update last name to `Fernando-Silva`. 4. Click "Save" or "Update Profile". |
| *Expected Results* | A success message appears. The profile page and header reflect the updated name: `Alicia Fernando-Silva`. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-015 |
| *Title* | Change password with correct current password |
| *Pre-Conditions* | User is logged in as `alice@nova.local` with password `NovaTest@2026`. |
| *Test Steps* | 1. Navigate to `/profile`. 2. Locate the change password section. 3. Enter current password: `NovaTest@2026`. 4. Enter new password: `NewSecure@2026`. 5. Confirm new password: `NewSecure@2026`. 6. Click "Change Password". |
| *Expected Results* | A success message appears: "Password changed successfully". User can log in with the new password. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-016 |
| *Title* | Change password with incorrect current password |
| *Pre-Conditions* | User is logged in as `bob@nova.local`. |
| *Test Steps* | 1. Navigate to `/profile`. 2. Enter current password: `WrongPassword`. 3. Enter new password: `NewPass@2026`. 4. Confirm new password: `NewPass@2026`. 5. Click "Change Password". |
| *Expected Results* | An error message is displayed indicating the current password is incorrect. Password is not changed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-017 |
| *Title* | Admin — view all users list |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to `/admin/users`. 2. Observe the users table. |
| *Expected Results* | A paginated table displays all users with columns: name, email, role, status (active/inactive), verification status. All 8 seeded users are visible. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-018 |
| *Title* | Admin — activate a deactivated user |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A deactivated user exists. |
| *Test Steps* | 1. Navigate to `/admin/users`. 2. Find a deactivated user. 3. Click "Activate" action for that user. 4. Confirm the action. |
| *Expected Results* | The user's status changes to "Active". The user can now log in. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-019 |
| *Title* | Admin — change user role |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to `/admin/users`. 2. Select user `assistant@nova.local`. 3. Change the role from `ASSISTANT` to `LIBRARIAN`. 4. Save the change. |
| *Expected Results* | The user's role is updated to LIBRARIAN. The change is reflected in the users list. An audit log entry is created for the role change. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-020 |
| *Title* | Admin — create a new user |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to `/admin/users`. 2. Click "Add User" or "Create User". 3. Fill in: email `staff@nova.local`, first name `Staff`, last name `Member`, role `ASSISTANT`. 4. Submit the form. |
| *Expected Results* | A new user is created and appears in the users list. A success message is displayed. The new user can log in with the assigned password. |
| *Actual Results* | |

---

### Module 3: Book Catalog (TC-021 to TC-033)

---

| Field | Details |
|-------|---------|
| *ID* | TC-021 |
| *Title* | Browse book catalog |
| *Pre-Conditions* | Logged in as any user. 15 books exist in the database. |
| *Test Steps* | 1. Navigate to `/catalog`. 2. Observe the book listing. |
| *Expected Results* | Books are displayed in a grid or list format with title, author(s), cover image, rating, and availability count. Pagination is available if more than the page limit. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-022 |
| *Title* | Search books by title |
| *Pre-Conditions* | Logged in. Books including "Clean Code" exist. |
| *Test Steps* | 1. Navigate to `/catalog`. 2. Enter "Clean Code" in the search bar. 3. Submit the search. |
| *Expected Results* | The search results display "Clean Code" by Robert Martin. Irrelevant books are filtered out. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-023 |
| *Title* | Filter books by category |
| *Pre-Conditions* | Logged in. Books and categories exist (e.g., "Software Engineering"). |
| *Test Steps* | 1. Navigate to `/catalog`. 2. Select the "Software Engineering" category filter. |
| *Expected Results* | Only books in the "Software Engineering" category are displayed (e.g., Clean Code, Design Patterns, Pragmatic Programmer, Refactoring, DDD, Microservices Patterns). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-024 |
| *Title* | View book details |
| *Pre-Conditions* | Logged in. The book "Clean Code" exists. |
| *Test Steps* | 1. Navigate to `/catalog`. 2. Click on "Clean Code" book card. |
| *Expected Results* | The book detail page displays: title, subtitle, author(s), ISBN, publisher, publication date, page count, description, categories/tags, average rating, number of reviews, and available copies. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-025 |
| *Title* | Filter books by language |
| *Pre-Conditions* | Logged in. Books in English, French, and Spanish exist. |
| *Test Steps* | 1. Navigate to `/catalog`. 2. Select the "French" language filter. |
| *Expected Results* | Only French-language books are shown (e.g., "Le Petit Prince"). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-026 |
| *Title* | Filter books by availability |
| *Pre-Conditions* | Logged in. Some books have available copies, some do not. |
| *Test Steps* | 1. Navigate to `/catalog`. 2. Enable the "Available Only" filter. |
| *Expected Results* | Only books with at least one available copy are shown. Books with zero available copies are hidden. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-027 |
| *Title* | Admin — create a new book |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. |
| *Test Steps* | 1. Navigate to `/admin/books`. 2. Click "Add Book". 3. Enter title: `Test Driven Development`. 4. Enter ISBN-13: `9780321146533`. 5. Select author: `Kent Beck` (or create new). 6. Select category: `Software Engineering`. 7. Enter publisher: `Addison-Wesley`. 8. Provide page count and description. 9. Click "Save" or "Create". |
| *Expected Results* | The book is created and appears in the admin book list. A success message is displayed. The book also appears in the public catalog. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-028 |
| *Title* | Admin — update a book's details |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. A book exists. |
| *Test Steps* | 1. Navigate to `/admin/books`. 2. Select an existing book. 3. Update the description field with new text. 4. Click "Save" or "Update". |
| *Expected Results* | The book description is updated. A success message is displayed. The change is reflected on the book detail page. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-029 |
| *Title* | Admin — delete a book with no active borrows |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A book exists with no active borrow records. |
| *Test Steps* | 1. Navigate to `/admin/books`. 2. Select a book with no active borrows. 3. Click "Delete". 4. Confirm the deletion. |
| *Expected Results* | The book is soft-deleted and no longer appears in the catalog. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-030 |
| *Title* | Admin — attempt to delete a book with active borrows |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A book has active borrow records. |
| *Test Steps* | 1. Navigate to `/admin/books`. 2. Select a book that currently has active borrows. 3. Click "Delete". 4. Confirm the deletion. |
| *Expected Results* | An error message is displayed indicating the book cannot be deleted because it has active borrows. The book remains in the catalog. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-031 |
| *Title* | Admin — add a book copy |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. A book exists. |
| *Test Steps* | 1. Navigate to `/admin/books`. 2. Select a book. 3. Click "Add Copy". 4. Enter condition: `NEW`, shelf number: `D1`, floor: `2`. 5. Click "Save". |
| *Expected Results* | A new book copy is created with an auto-generated barcode. The book's total copies count is incremented. A success message appears. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-032 |
| *Title* | Submit a book review |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Viewing a book detail page for a book not yet reviewed by this user. |
| *Test Steps* | 1. Navigate to a book detail page (e.g., `/catalog/<bookId>`). 2. Scroll to the review section. 3. Select a rating: 5 stars. 4. Enter review title: `Excellent Resource!`. 5. Enter review content: `This book changed the way I think about software.`. 6. Click "Submit Review". |
| *Expected Results* | The review is saved and displayed on the book detail page. The book's average rating is updated. A success message appears. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-033 |
| *Title* | Attempt duplicate review for same book |
| *Pre-Conditions* | `alice@nova.local` has already reviewed a specific book. |
| *Test Steps* | 1. Navigate to the same book detail page. 2. Attempt to submit another review. |
| *Expected Results* | The system prevents a duplicate review. An error message is displayed: "You have already reviewed this book" or the review form is hidden/disabled. |
| *Actual Results* | |

---

### Module 4: Author Management (TC-034 to TC-037)

---

| Field | Details |
|-------|---------|
| *ID* | TC-034 |
| *Title* | Admin — create a new author |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. |
| *Test Steps* | 1. Navigate to `/admin/authors`. 2. Click "Add Author". 3. Enter first name: `Kent`. 4. Enter last name: `Beck`. 5. Enter nationality: `American`. 6. Click "Save". |
| *Expected Results* | The author is created and appears in the authors list. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-035 |
| *Title* | Admin — update an author |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. An author exists. |
| *Test Steps* | 1. Navigate to `/admin/authors`. 2. Select an author (e.g., Robert Martin). 3. Update biography text. 4. Click "Save". |
| *Expected Results* | The author's biography is updated. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-036 |
| *Title* | Admin — delete an author with no books |
| *Pre-Conditions* | Logged in as `admin@nova.local`. An author exists with no associated books. |
| *Test Steps* | 1. Navigate to `/admin/authors`. 2. Select an author with no books. 3. Click "Delete". 4. Confirm. |
| *Expected Results* | The author is deleted. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-037 |
| *Title* | Admin — attempt to delete an author with associated books |
| *Pre-Conditions* | Logged in as `admin@nova.local`. Author "Robert Martin" has "Clean Code" associated. |
| *Test Steps* | 1. Navigate to `/admin/authors`. 2. Select "Robert Martin". 3. Click "Delete". 4. Confirm. |
| *Expected Results* | An error message is displayed: cannot delete author with associated books. The author remains in the system. |
| *Actual Results* | |

---

### Module 5: Circulation — Reservations & Borrowing (TC-038 to TC-052)

---

| Field | Details |
|-------|---------|
| *ID* | TC-038 |
| *Title* | Reserve a book with available copies |
| *Pre-Conditions* | Logged in as `alice@nova.local`. A book has available copies. |
| *Test Steps* | 1. Navigate to a book detail page with available copies. 2. Click "Reserve" button. 3. Confirm the reservation. |
| *Expected Results* | A reservation is created with status "READY" (copy auto-assigned). A success message appears. The reservation is visible at `/reservations`. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-039 |
| *Title* | Reserve a book with no available copies |
| *Pre-Conditions* | Logged in as a user. All copies of a book are currently borrowed. |
| *Test Steps* | 1. Navigate to a book detail page with 0 available copies. 2. Click "Reserve" button. |
| *Expected Results* | A reservation is created with status "PENDING" (placed in queue). A message indicates the user is in the queue. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-040 |
| *Title* | Duplicate reservation for same book |
| *Pre-Conditions* | `alice@nova.local` already has an active reservation for a specific book. |
| *Test Steps* | 1. Navigate to the same book's detail page. 2. Attempt to click "Reserve" again. |
| *Expected Results* | An error is displayed: "You already have an active reservation for this book." The duplicate reservation is not created. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-041 |
| *Title* | Cancel a reservation |
| *Pre-Conditions* | Logged in as `alice@nova.local`. An active reservation exists. |
| *Test Steps* | 1. Navigate to `/reservations`. 2. Find an active reservation. 3. Click "Cancel". 4. Confirm cancellation. |
| *Expected Results* | The reservation status changes to "CANCELLED". The assigned copy (if any) is released. A success message appears. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-042 |
| *Title* | Librarian — confirm book pickup |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. A reservation with status "READY" exists. |
| *Test Steps* | 1. Navigate to `/admin/circulation`. 2. View pending pickups section. 3. Find a "READY" reservation. 4. Click "Confirm Pickup". |
| *Expected Results* | A BorrowRecord is created with status "ACTIVE". The reservation status changes to "FULFILLED". The book copy status changes to "BORROWED". A due date is set (14 days from now). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-043 |
| *Title* | Librarian — return a book |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. An active borrow record exists. |
| *Test Steps* | 1. Navigate to `/admin/circulation`. 2. Find an active borrow record. 3. Click "Return". 4. Select return condition: `GOOD`. 5. Confirm the return. |
| *Expected Results* | The borrow record status changes to "RETURNED". The book copy becomes "AVAILABLE". The return date and condition are recorded. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-044 |
| *Title* | User — renew an active borrow |
| *Pre-Conditions* | Logged in as `alice@nova.local`. An active borrow exists that hasn't been renewed yet. The borrow is not overdue. |
| *Test Steps* | 1. Navigate to `/borrows`. 2. Find an active borrow. 3. Click "Renew". |
| *Expected Results* | The due date is extended by 14 days. The renewal count increments to 1. A success message appears. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-045 |
| *Title* | Attempt to renew beyond maximum renewals |
| *Pre-Conditions* | A borrow record has already been renewed 2 times (max). |
| *Test Steps* | 1. Navigate to `/borrows`. 2. Find the borrow with 2 renewals. 3. Attempt to click "Renew". |
| *Expected Results* | An error message is displayed: "Maximum renewals reached." The renew button is disabled or the action is blocked. Due date is not extended. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-046 |
| *Title* | Attempt to renew an overdue borrow |
| *Pre-Conditions* | A borrow record has passed its due date (status: OVERDUE). |
| *Test Steps* | 1. Navigate to `/borrows`. 2. Find the overdue borrow. 3. Attempt to renew. |
| *Expected Results* | An error is displayed: "Cannot renew overdue borrow." Renewal is rejected. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-047 |
| *Title* | View my borrows |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Alice has active and returned borrows. |
| *Test Steps* | 1. Navigate to `/borrows`. |
| *Expected Results* | A list of the user's borrow records is displayed with: book title, borrow date, due date, status (ACTIVE/RETURNED/OVERDUE), and renewal count. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-048 |
| *Title* | View my reservations |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Alice has active reservations. |
| *Test Steps* | 1. Navigate to `/reservations`. |
| *Expected Results* | A list of the user's reservations is displayed with: book title, reservation date, status (PENDING/READY/FULFILLED/CANCELLED), and expiry time. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-049 |
| *Title* | View my fines |
| *Pre-Conditions* | Logged in as `bob@nova.local`. Bob has pending fines. |
| *Test Steps* | 1. Navigate to `/fines`. |
| *Expected Results* | A list of fines is displayed with: book title, reason (OVERDUE/LOST/DAMAGE), amount, status (PENDING/PAID/WAIVED), and payment options. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-050 |
| *Title* | Pay a fine |
| *Pre-Conditions* | Logged in as `bob@nova.local`. A pending fine exists. |
| *Test Steps* | 1. Navigate to `/fines`. 2. Find a pending fine. 3. Click "Pay". 4. Confirm payment. |
| *Expected Results* | The fine status changes to "PAID". The paid amount is recorded. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-051 |
| *Title* | Admin — waive a fine |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A pending fine exists. |
| *Test Steps* | 1. Navigate to `/admin/circulation`. 2. View the fines section. 3. Find a pending fine. 4. Click "Waive". 5. Confirm. |
| *Expected Results* | The fine status changes to "WAIVED". The waived_by field records the admin. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-052 |
| *Title* | Admin — view overdue borrows |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. Overdue borrow records exist. |
| *Test Steps* | 1. Navigate to `/admin/circulation`. 2. View the overdue borrows section. |
| *Expected Results* | A list of overdue borrow records is displayed with: user name, book title, borrow date, due date, days overdue. |
| *Actual Results* | |

---

### Module 6: Digital Content (TC-053 to TC-061)

---

| Field | Details |
|-------|---------|
| *ID* | TC-053 |
| *Title* | View digital library |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Alice has digital assets in her library. |
| *Test Steps* | 1. Navigate to `/library`. |
| *Expected Results* | A list of digital assets in the user's library is displayed with: book title, asset type (eBook/Audiobook), reading progress, and favorite status. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-054 |
| *Title* | Start a reading session |
| *Pre-Conditions* | Logged in as `alice@nova.local`. An eBook is in the user's library. |
| *Test Steps* | 1. Navigate to `/library`. 2. Click on an eBook to open the reader at `/reader/<assetId>`. |
| *Expected Results* | A reading session is started. The reader interface opens displaying the book content. Session status is "ACTIVE". |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-055 |
| *Title* | Update reading progress |
| *Pre-Conditions* | A reading session is active for the user. |
| *Test Steps* | 1. In the reader, navigate to page 50 of 200 (25% progress). 2. The progress update is sent automatically or on page turn. |
| *Expected Results* | The reading progress is updated to 25%. The user's library entry reflects the new progress. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-056 |
| *Title* | End a reading session |
| *Pre-Conditions* | A reading session is active. |
| *Test Steps* | 1. Close the reader or click "End Session". |
| *Expected Results* | The session status changes to "COMPLETED" or "PAUSED". The duration is calculated and recorded. KP may be awarded for the session. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-057 |
| *Title* | Add a bookmark |
| *Pre-Conditions* | A reading session is active in the reader. |
| *Test Steps* | 1. Navigate to a specific page in the reader. 2. Click "Add Bookmark" or the bookmark icon. 3. Enter title: `Important Section`. |
| *Expected Results* | The bookmark is saved with the current position. It appears in the bookmarks list for this asset. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-058 |
| *Title* | Add a highlight |
| *Pre-Conditions* | A reading session is active in the reader. |
| *Test Steps* | 1. Select text in the reader. 2. Click "Highlight" from the context menu. 3. Choose highlight color: yellow. 4. Optionally add a note. |
| *Expected Results* | The selected text is highlighted in yellow. The highlight is saved and visible in the highlights list. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-059 |
| *Title* | Toggle favorite status |
| *Pre-Conditions* | Logged in as `alice@nova.local`. A digital asset is in the library. |
| *Test Steps* | 1. Navigate to `/library`. 2. Click the "Favorite" icon on a book. |
| *Expected Results* | The book's favorite status is toggled. The UI reflects the change (filled/unfilled heart icon). Filtering by "Favorites" shows only favorited items. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-060 |
| *Title* | Admin — upload a digital asset |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. A book exists without a digital asset. |
| *Test Steps* | 1. Navigate to `/admin/digital`. 2. Click "Upload Asset". 3. Select a book. 4. Choose asset type: `EBOOK_PDF`. 5. Provide file path and file size. 6. Click "Upload". |
| *Expected Results* | The digital asset is created and linked to the book. It appears in the admin digital assets list. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-061 |
| *Title* | Admin — delete a digital asset |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A digital asset exists. |
| *Test Steps* | 1. Navigate to `/admin/digital`. 2. Select a digital asset. 3. Click "Delete". 4. Confirm deletion. |
| *Expected Results* | The digital asset is deleted. Associated user library entries are removed. A success message is displayed. |
| *Actual Results* | |

---

### Module 7: Engagement & Gamification (TC-062 to TC-071)

---

| Field | Details |
|-------|---------|
| *ID* | TC-062 |
| *Title* | View Knowledge Points (KP) dashboard |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Engagement data exists. |
| *Test Steps* | 1. Navigate to `/kp-center`. |
| *Expected Results* | The KP center displays: total KP, current level, level title, KP breakdown by dimension (explorer, scholar, connector, achiever, dedicated), streak info, and daily cap progress. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-063 |
| *Title* | View achievements |
| *Pre-Conditions* | Logged in as `charlie@nova.local`. Charlie has multiple achievements. |
| *Test Steps* | 1. Navigate to `/achievements`. |
| *Expected Results* | The achievements page displays all available achievements with: name, description, rarity, KP reward, and earned/locked status. Charlie's earned achievements are highlighted. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-064 |
| *Title* | View leaderboard |
| *Pre-Conditions* | Logged in as any user. Engagement data exists for multiple users. |
| *Test Steps* | 1. Navigate to `/leaderboard`. |
| *Expected Results* | A ranked list of users is displayed sorted by total KP (descending). Each entry shows: rank, user name/avatar, total KP, level, and level title. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-065 |
| *Title* | View daily activity history |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Daily activity records exist. |
| *Test Steps* | 1. Navigate to `/kp-center` or `/insights`. 2. View the activity history section. |
| *Expected Results* | The daily activity for the past 30 days is displayed with: date, KP earned, books borrowed, reading minutes, pages read, reviews written. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-066 |
| *Title* | Verify streak display |
| *Pre-Conditions* | Logged in as `charlie@nova.local`. Charlie has a 25-day streak. |
| *Test Steps* | 1. Navigate to `/kp-center` or the dashboard. |
| *Expected Results* | The current streak shows 25 days. The streak multiplier is displayed (e.g., 1.5x for 14+ days). The longest streak is also shown. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-067 |
| *Title* | View user rank and percentile |
| *Pre-Conditions* | Logged in as `alice@nova.local`. |
| *Test Steps* | 1. Navigate to `/kp-center`. 2. Observe rank information. |
| *Expected Results* | The user's rank and percentile are displayed (e.g., "Rank #3 — Top 40%"). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-068 |
| *Title* | Admin — award KP to a user |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to admin user management. 2. Select user `alice@nova.local`. 3. Use "Award KP" function. 4. Enter points: `50`, reason: `Outstanding contribution`. 5. Submit. |
| *Expected Results* | 50 KP are added to Alice's total. A KP ledger entry is created. Alice's level may increase if threshold crossed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-069 |
| *Title* | View KP history |
| *Pre-Conditions* | Logged in as `alice@nova.local`. KP transactions exist. |
| *Test Steps* | 1. Navigate to `/kp-center`. 2. View the KP history/ledger section. |
| *Expected Results* | A list of KP transactions is displayed with: date, action (AWARD/DEDUCT/BONUS), points, balance after, source, and description. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-070 |
| *Title* | Verify level progression |
| *Pre-Conditions* | A user is close to a level threshold (e.g., Level 3 requires 600 KP, user has 590 KP). |
| *Test Steps* | 1. Perform an action that awards 15+ KP (e.g., complete a reading session). 2. Check the KP center. |
| *Expected Results* | The user's level is upgraded from 3 to 4. The level title updates. A notification or visual indicator shows the level-up. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-071 |
| *Title* | Reading insights — view patterns |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Reading session data exists. |
| *Test Steps* | 1. Navigate to `/insights`. |
| *Expected Results* | The insights page displays: reading speed, session patterns (time of day, day of week), engagement heatmap, and completion predictions. |
| *Actual Results* | |

---

### Module 8: Intelligence & Recommendations (TC-072 to TC-079)

---

| Field | Details |
|-------|---------|
| *ID* | TC-072 |
| *Title* | View personalized recommendations |
| *Pre-Conditions* | Logged in as `alice@nova.local`. Recommendations have been generated. |
| *Test Steps* | 1. Navigate to `/recommendations`. |
| *Expected Results* | A list of recommended books is displayed with: book title, author, recommendation strategy, score, and explanation text. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-073 |
| *Title* | Dismiss a recommendation |
| *Pre-Conditions* | Logged in. Recommendations are displayed. |
| *Test Steps* | 1. Navigate to `/recommendations`. 2. Find a recommendation. 3. Click "Dismiss" or the dismiss icon. |
| *Expected Results* | The recommendation is dismissed and removed from the list. It does not reappear in future recommendations. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-074 |
| *Title* | Click a recommendation |
| *Pre-Conditions* | Logged in. Recommendations are displayed. |
| *Test Steps* | 1. Navigate to `/recommendations`. 2. Click on a recommended book title or card. |
| *Expected Results* | The user is navigated to the book detail page. The recommendation's `is_clicked` flag is set to true (for analytics). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-075 |
| *Title* | View trending books |
| *Pre-Conditions* | Logged in. Trending data has been seeded. |
| *Test Steps* | 1. Navigate to the dashboard or a trending section. 2. Observe the trending books. |
| *Expected Results* | Trending books are displayed by period (daily/weekly/monthly) with rank, borrow count, and score. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-076 |
| *Title* | Search books with keyword |
| *Pre-Conditions* | Logged in. Books exist in the catalog. |
| *Test Steps* | 1. Navigate to `/search`. 2. Enter search query: `algorithms`. 3. Submit the search. |
| *Expected Results* | Search results display relevant books (e.g., "Introduction to Algorithms", "The Art of Computer Programming"). Results include relevance indicators and are sorted by relevance. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-077 |
| *Title* | Update reading preferences |
| *Pre-Conditions* | Logged in as `alice@nova.local`. |
| *Test Steps* | 1. Navigate to `/recommendations` or preferences settings. 2. Update preferred categories to include "Databases". 3. Update preferred language to "English". 4. Save preferences. |
| *Expected Results* | Preferences are saved. Future recommendations reflect the updated preferences. A success message appears. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-078 |
| *Title* | View notifications |
| *Pre-Conditions* | Logged in. Notifications exist for the user. |
| *Test Steps* | 1. Navigate to `/notifications`. |
| *Expected Results* | A list of notifications is displayed with: message, timestamp, and read/unread status. Unread count is shown in the header badge. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-079 |
| *Title* | Mark notification as read |
| *Pre-Conditions* | Logged in. Unread notifications exist. |
| *Test Steps* | 1. Navigate to `/notifications`. 2. Click on an unread notification or click "Mark as Read". |
| *Expected Results* | The notification is marked as read. The unread count in the header decreases. The notification appearance changes (e.g., no longer bold). |
| *Actual Results* | |

---

### Module 9: Governance & Audit (TC-080 to TC-084)

---

| Field | Details |
|-------|---------|
| *ID* | TC-080 |
| *Title* | Admin — view audit logs |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). Audit log entries exist. |
| *Test Steps* | 1. Navigate to `/admin/audit`. 2. Observe the audit log table. |
| *Expected Results* | A paginated list of audit logs is displayed with: timestamp, actor (email, role), action type (LOGIN, BORROW, RETURN, etc.), resource type, description, and IP address. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-081 |
| *Title* | Admin — filter audit logs by action type |
| *Pre-Conditions* | Logged in as `admin@nova.local`. Multiple audit log entries exist. |
| *Test Steps* | 1. Navigate to `/admin/audit`. 2. Select action filter: `LOGIN`. 3. Apply filter. |
| *Expected Results* | Only LOGIN-type audit entries are displayed. Other action types are filtered out. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-082 |
| *Title* | Admin — view security events |
| *Pre-Conditions* | Logged in as `admin@nova.local`. Security events exist in the system. |
| *Test Steps* | 1. Navigate to `/admin/audit`. 2. View the security events section. |
| *Expected Results* | Security events are displayed with: event type (FAILED_LOGIN, BRUTE_FORCE, etc.), severity (LOW-CRITICAL), timestamp, description, and resolved status. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-083 |
| *Title* | Verify audit trail for user role change |
| *Pre-Conditions* | Logged in as `admin@nova.local`. |
| *Test Steps* | 1. Change a user's role (e.g., ASSISTANT to LIBRARIAN). 2. Navigate to `/admin/audit`. 3. Search for the recent ROLE_CHANGE action. |
| *Expected Results* | An audit log entry exists for the role change with: actor (admin), action (ROLE_CHANGE), resource (user ID), old value (ASSISTANT), and new value (LIBRARIAN). |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-084 |
| *Title* | User — view personal KP ledger |
| *Pre-Conditions* | Logged in as `alice@nova.local`. KP transactions exist. |
| *Test Steps* | 1. Navigate to `/kp-center`. 2. View the KP history section. |
| *Expected Results* | The user's KP ledger shows all transactions: awards, deductions, bonuses. Each entry has: date, action, points, balance, source, and dimension. |
| *Actual Results* | |

---

### Module 10: Asset Management (TC-085 to TC-091)

---

| Field | Details |
|-------|---------|
| *ID* | TC-085 |
| *Title* | Admin — view all library assets |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. Assets have been seeded. |
| *Test Steps* | 1. Navigate to `/admin/assets`. |
| *Expected Results* | A table of library assets is displayed with: asset tag, name, category, status (ACTIVE/UNDER_MAINTENANCE/etc.), condition, location (floor/room), and current value. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-086 |
| *Title* | Admin — create a new asset |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. Asset categories exist. |
| *Test Steps* | 1. Navigate to `/admin/assets`. 2. Click "Add Asset". 3. Enter asset tag: `AST-007`. 4. Enter name: `Study Lamp - Reading Area`. 5. Select category: `Electronics`. 6. Set status: `ACTIVE`, condition: `NEW`. 7. Enter purchase price: `150.00`, floor: `1`, room: `Reading Area`. 8. Click "Save". |
| *Expected Results* | The asset is created and appears in the assets list. A success message is displayed. Asset statistics are updated. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-087 |
| *Title* | Admin — update an asset |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. An asset exists. |
| *Test Steps* | 1. Navigate to `/admin/assets`. 2. Select an existing asset. 3. Change condition from `GOOD` to `FAIR`. 4. Update room to `Study Hall B`. 5. Click "Save". |
| *Expected Results* | The asset details are updated. A success message is displayed. Changes are reflected in the asset list. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-088 |
| *Title* | Admin — log maintenance for an asset |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. An asset exists. |
| *Test Steps* | 1. Navigate to `/admin/assets`. 2. Select the "HP LaserJet Pro MFP" asset. 3. Click "Log Maintenance". 4. Enter type: `CORRECTIVE`, description: `Replaced toner cartridge`, cost: `80.00`, vendor: `HP Service`. 5. Submit. |
| *Expected Results* | A maintenance log entry is created. The asset's condition is updated. The next maintenance date is calculated. A success message appears. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-089 |
| *Title* | Admin — dispose of an asset |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). An asset exists. |
| *Test Steps* | 1. Navigate to `/admin/assets`. 2. Select an asset. 3. Click "Dispose". 4. Select method: `RECYCLED`. 5. Enter reason: `End of useful life`. 6. Confirm. |
| *Expected Results* | The asset status changes to "DISPOSED". A disposal record is created. The asset is no longer counted in active asset statistics. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-090 |
| *Title* | Admin — view asset statistics |
| *Pre-Conditions* | Logged in as `librarian@nova.local`. Assets exist. |
| *Test Steps* | 1. Navigate to `/admin/assets`. 2. Observe the statistics/dashboard section. |
| *Expected Results* | Asset statistics display: total assets, active assets, under maintenance, disposed, total value, overdue maintenance count, and warranties expiring soon. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-091 |
| *Title* | Admin — view maintenance history for an asset |
| *Pre-Conditions* | Logged in. An asset has maintenance log entries. |
| *Test Steps* | 1. Navigate to `/admin/assets`. 2. Select the "Self-Checkout Kiosk #1" asset. 3. View maintenance history section. |
| *Expected Results* | Maintenance logs are displayed with: date, type (PREVENTIVE/CORRECTIVE), description, cost, vendor, and resulting condition. |
| *Actual Results* | |

---

### Module 11: HR Management (TC-092 to TC-098)

---

| Field | Details |
|-------|---------|
| *ID* | TC-092 |
| *Title* | Admin — view departments |
| *Pre-Conditions* | Logged in as `admin@nova.local`. Departments have been seeded. |
| *Test Steps* | 1. Navigate to `/admin/employees`. 2. Observe the departments section. |
| *Expected Results* | Departments are displayed with: name, code, head (employee name), employee count, and active status. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-093 |
| *Title* | Admin — create a new department |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to `/admin/employees`. 2. Click "Add Department". 3. Enter name: `Special Collections`. 4. Enter code: `SPEC`. 5. Click "Save". |
| *Expected Results* | The department is created and appears in the departments list. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-094 |
| *Title* | Admin — view employees |
| *Pre-Conditions* | Logged in as `admin@nova.local`. Employees have been seeded. |
| *Test Steps* | 1. Navigate to `/admin/employees`. 2. Observe the employees table. |
| *Expected Results* | Employees are displayed with: employee ID, name, department, job title, employment type, status, and hire date. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-095 |
| *Title* | Admin — create a new employee |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A user and department exist. |
| *Test Steps* | 1. Navigate to `/admin/employees`. 2. Click "Add Employee". 3. Link to a user account. 4. Enter employee ID: `EMP-004`. 5. Select department: `IT & Digital Services`. 6. Enter job title: `Systems Administrator`. 7. Set employment type: `FULL_TIME`, salary: `55000`. 8. Click "Save". |
| *Expected Results* | The employee record is created and appears in the employees list. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-096 |
| *Title* | Admin — view job vacancies |
| *Pre-Conditions* | Logged in as `admin@nova.local`. Job vacancies have been seeded. |
| *Test Steps* | 1. Navigate to `/admin/jobs`. 2. Observe the vacancies table. |
| *Expected Results* | Job vacancies are displayed with: title, department, experience level, status (OPEN/CLOSED/DRAFT), positions available, salary range, and closing date. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-097 |
| *Title* | Admin — create a job vacancy |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A department exists. |
| *Test Steps* | 1. Navigate to `/admin/jobs`. 2. Click "Add Vacancy". 3. Enter title: `Part-Time Clerk`. 4. Select department: `Circulation Services`. 5. Enter description and requirements. 6. Set experience level: `ENTRY`, type: `PART_TIME`. 7. Set salary range: 20000-28000. 8. Set status: `OPEN`. 9. Click "Save". |
| *Expected Results* | The job vacancy is created and visible in the vacancies list. A success message is displayed. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-098 |
| *Title* | Admin — review job application |
| *Pre-Conditions* | Logged in as `admin@nova.local`. A job application exists. |
| *Test Steps* | 1. Navigate to `/admin/jobs`. 2. Select a vacancy with applications. 3. View the applications list. 4. Select an application. 5. Change status from `SUBMITTED` to `SHORTLISTED`. 6. Add review notes: `Strong candidate`. 7. Save. |
| *Expected Results* | The application status is updated to "SHORTLISTED". Review notes are saved. A success message appears. |
| *Actual Results* | |

---

### Module 12: Roles & Settings (TC-099 to TC-100)

---

| Field | Details |
|-------|---------|
| *ID* | TC-099 |
| *Title* | Admin — manage RBAC role configurations |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to `/admin/roles`. 2. Click "Create Role". 3. Enter role key: `INTERN`. 4. Enter display name: `Library Intern`. 5. Set permissions: read-only access to `books`, `catalog`, `circulation`. 6. Click "Save". |
| *Expected Results* | The new role configuration is created and appears in the roles list. A success message is displayed. The role can be assigned to users. |
| *Actual Results* | |

---

| Field | Details |
|-------|---------|
| *ID* | TC-100 |
| *Title* | Admin — update system settings |
| *Pre-Conditions* | Logged in as `admin@nova.local` (SUPER_ADMIN). |
| *Test Steps* | 1. Navigate to `/admin/settings`. 2. Locate a system setting (e.g., daily KP cap, borrow period). 3. Update the value (e.g., change borrow period from 14 to 21 days). 4. Click "Save". |
| *Expected Results* | The system setting is updated. A success message is displayed. The new value takes effect for subsequent operations. |
| *Actual Results* | |

---

## 3. Test Case Summary

| Module | Test Case IDs | Count |
|--------|--------------|-------|
| Authentication & Login | TC-001 to TC-012 | 12 |
| User Profile & Management | TC-013 to TC-020 | 8 |
| Book Catalog | TC-021 to TC-033 | 13 |
| Author Management | TC-034 to TC-037 | 4 |
| Circulation (Reservations, Borrows, Fines) | TC-038 to TC-052 | 15 |
| Digital Content | TC-053 to TC-061 | 9 |
| Engagement & Gamification | TC-062 to TC-071 | 10 |
| Intelligence & Recommendations | TC-072 to TC-079 | 8 |
| Governance & Audit | TC-080 to TC-084 | 5 |
| Asset Management | TC-085 to TC-091 | 7 |
| HR Management | TC-092 to TC-098 | 7 |
| Roles & Settings | TC-099 to TC-100 | 2 |
| **Total** | **TC-001 to TC-100** | **100** |

---

## 4. Test Execution Tracker

| Metric | Value |
|--------|-------|
| Total Test Cases | 100 |
| Executed | — |
| Passed | — |
| Failed | — |
| Blocked | — |
| Not Executed | 100 |
| Pass Rate | — |

---

## 5. Defect Severity Classification

| Severity | Description |
|----------|-------------|
| Critical | System crash, data loss, security vulnerability, complete feature failure |
| High | Major feature not working, no workaround available |
| Medium | Feature partially working, workaround available |
| Low | Cosmetic issue, minor UI inconsistency, typo |

---

## 6. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| QA Lead | | | |
| Project Manager | | | |
| Development Lead | | | |

---

*Document Version: 1.0 — Generated February 27, 2026*
