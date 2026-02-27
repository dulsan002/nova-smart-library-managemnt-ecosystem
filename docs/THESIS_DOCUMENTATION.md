# Nova Smart Library Management Ecosystem

## Comprehensive Technical Documentation

**Academic Thesis Reference Document**

---

**Document Version:** 1.0
**Date:** February 2026
**Classification:** Technical Architecture & Design Documentation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Design](#4-database-design)
5. [System Modules](#5-system-modules)
6. [UML and System Design](#6-uml-and-system-design)
7. [System Workflows](#7-system-workflows)
8. [Security Design](#8-security-design)
9. [Implementation Details](#9-implementation-details)
10. [Testing Strategy](#10-testing-strategy)
11. [Design Decisions and Justifications](#11-design-decisions-and-justifications)

---

## 1. System Overview

### 1.1 System Name

**Nova Smart Library Management Ecosystem** — an enterprise-grade, AI-augmented, full-stack digital library management platform engineered with Domain-Driven Design principles.

### 1.2 System Purpose

The Nova Smart Library Management Ecosystem serves as a comprehensive, intelligent library management platform that unifies the administration of physical book collections, digital content repositories, user engagement systems, and institutional operations within a single cohesive software ecosystem. The system transcends the capabilities of conventional library management systems by incorporating artificial intelligence for search, recommendations, predictive analytics, and natural language interaction, while simultaneously providing gamification mechanics to incentivise sustained reader engagement. Its design objective is to deliver a modern, data-driven library experience that automates operational workflows, provides actionable intelligence to administrators, and fosters a vibrant reading culture among library patrons.

### 1.3 Problem Statement

Traditional library management systems suffer from several critical limitations that reduce operational efficiency and patron satisfaction. First, they typically lack intelligent search capabilities, forcing users to rely on rigid keyword matching that cannot interpret natural language queries or compensate for typographical errors. Second, conventional systems provide no mechanism for personalised content discovery; users must browse catalogues manually without receiving recommendations aligned with their reading preferences and history. Third, the absence of integrated digital content management means that physical and digital collections are managed in disparate systems, creating fragmented user experiences. Fourth, existing solutions provide limited analytics, offering administrators no predictive capabilities for demand forecasting, overdue risk assessment, or patron churn detection. Fifth, most library systems lack engagement mechanics, providing no gamification or achievement systems to motivate continued library usage. Finally, institutional operations such as human resource management, physical asset tracking, and role-based access governance are typically handled by entirely separate platforms, creating administrative overhead and data silos.

The Nova Smart Library Management Ecosystem addresses each of these deficiencies through a unified platform that integrates AI-powered search and recommendation engines, digital content streaming, a Knowledge Points gamification system, predictive analytics, comprehensive role-based access control, and institutional management modules — all within a single, coherent architectural framework.

### 1.4 Target Users

The system accommodates six distinct user personas, each with differentiated access levels and interaction patterns:

**Public Users (Guests)** — unauthenticated visitors who may browse the catalogue, search for books, and register for accounts. Their interactions are limited to read-only catalogue access and the registration workflow.

**Library Members** — authenticated patrons who represent the primary user base. Members may borrow and reserve physical books, access digital content (e-books and audiobooks), receive personalised recommendations, participate in the Knowledge Points gamification system, track reading insights, and manage their personal profiles.

**Library Assistants** — staff members with elevated privileges who may process borrow transactions, confirm pickups, handle returns, manage fines, and assist patrons with day-to-day circulation operations.

**Librarians** — senior staff with broader administrative access encompassing catalogue management (creating and editing books, authors, and categories), digital asset management, circulation oversight, member management, and access to analytical dashboards.

**Super Administrators** — the highest-privileged role with unrestricted system access, including user role management, role-based access configuration, system settings administration, AI provider configuration, audit log review, asset management, human resource operations, and SMTP configuration.

**System Actors (Automated)** — background processes executed by the Celery distributed task queue, responsible for overdue detection, recommendation refresh, embedding computation, trend calculation, notification delivery, streak evaluation, model training, and session cleanup.

### 1.5 Business Value

The system delivers measurable business value across multiple dimensions. Operational efficiency is improved through automated overdue detection, fine calculation, reservation queue management, and notification delivery — reducing manual administrative workload. Patron engagement is enhanced through the Knowledge Points system, achievement mechanics, streak tracking, and leaderboards, which collectively incentivise sustained library usage. Decision support is provided by AI-powered predictive analytics including demand forecasting, collection gap analysis, churn prediction, and overdue risk scoring, enabling administrators to make data-informed collection development and operational decisions. The hybrid search engine, combining full-text, semantic, and fuzzy search strategies, significantly improves content discoverability. Digital content integration enables the library to serve patrons beyond physical premises, with e-book reading and audiobook streaming capabilities. Institutional consolidation is achieved by incorporating HR management and physical asset tracking within the same platform, eliminating the need for separate administrative systems.

---

## 2. System Architecture

### 2.1 Architecture Style

The Nova Smart Library Management Ecosystem is engineered following **Domain-Driven Design (DDD)** principles, organised into ten distinct **bounded contexts** that encapsulate cohesive domains of business logic. Each bounded context maintains its own domain models, application services, infrastructure adapters, and presentation layer — enforcing a clear separation of concerns and minimising inter-module coupling.

The system further employs a **layered architecture** within each bounded context, consisting of four tiers: (i) the **Domain Layer**, containing entity models, value objects, domain events, and business invariants; (ii) the **Application Layer**, containing use case orchestrators, service classes, and command handlers; (iii) the **Infrastructure Layer**, containing repository implementations, external service adapters, and persistence logic; and (iv) the **Presentation Layer**, containing GraphQL type definitions, query resolvers, and mutation handlers.

Cross-cutting concerns such as event propagation, audit logging, and security enforcement are managed through an **Event Bus** pattern and a **middleware pipeline** that intercepts all incoming requests. The architecture additionally incorporates elements of **Command Query Responsibility Segregation (CQRS)**, where query resolvers and mutation handlers operate through distinct execution paths, enabling independent optimization of read and write operations.

### 2.2 High-Level Architecture Overview

Figure 1 (see [01-architecture-overview.md, Section 1](01-architecture-overview.md)) illustrates the high-level system architecture. The client layer consists of a React Single-Page Application that communicates exclusively with the backend through a single GraphQL endpoint. The API gateway layer incorporates a security middleware pipeline that enforces rate limiting, query depth and complexity validation, authentication, and security header injection. Behind this gateway, the Django application server hosts the ten bounded contexts, each of which interacts with the shared PostgreSQL database (augmented with the pgvector and pg_trgm extensions for vector similarity and trigram fuzzy search), the Redis cache and session store, and the Celery distributed task queue backed by a Redis message broker. The AI/ML subsystem connects to an Ollama server running the LLaMA 3.1 large language model for conversational search and natural language analytics, while embedding generation is handled by the locally executed sentence-transformers library (all-MiniLM-L6-v2).

### 2.3 Component Breakdown

The system is decomposed into ten bounded contexts, each representing a cohesive domain:

**Common** — provides shared abstract base models (`TimeStampedModel`, `UUIDModel`, `SoftDeletableModel`, `VersionedModel`), system-wide settings management, utility functions, custom exception hierarchy, event bus implementation, pagination helpers, input sanitisers, file security validators, and structured JSON logging formatters.

**Identity** — manages user registration, authentication, profile management, NIC/document verification (OCR and face recognition), password reset with OTP, refresh token rotation, role-based access configuration, and member management.

**Catalog** — governs the book catalogue including books, authors, categories, physical book copies, and book reviews, with support for soft deletion, optimistic concurrency control, and embedding vector storage.

**Circulation** — handles the complete borrowing lifecycle encompassing reservations, borrow records, returns, renewals, overdue detection, fine calculation and escalation, fine payment and waiver, and reservation ban enforcement.

**Digital Content** — manages digital assets (e-books and audiobooks), user digital libraries, reading and listening sessions, bookmarks, highlights, and reading progress tracking.

**Engagement** — implements the gamification subsystem including Knowledge Points (KP) award and tracking across five dimensions (Explorer, Scholar, Connector, Achiever, Dedicated), achievement definitions and unlocks, daily activity tracking, reading streaks, and leaderboard rankings.

**Intelligence** — encapsulates all AI/ML capabilities including the hybrid search engine, recommendation engine (collaborative, content-based, trending, and hybrid strategies), predictive analytics (overdue, demand, churn, collection gap), LLM-powered search and analytics, user preference management, notification delivery, search logging, AI provider configuration, model version management, and trending book computation.

**Governance** — provides compliance and auditability through immutable audit logs, security event tracking, and a Knowledge Points ledger for financial-grade KP transaction recording.

**Asset Management** — tracks physical library assets (furniture, equipment, technology) with categorisation, condition monitoring, maintenance scheduling, and disposal tracking.

**HR** — manages human resource operations including departments, employees, job vacancies, and job applications.

### 2.4 Frontend–Backend Interaction

The frontend React application communicates with the Django backend exclusively through a single GraphQL endpoint (`/graphql/`). All data fetching is performed via GraphQL queries, and all data mutations are executed through GraphQL mutations. The Apollo Client library manages the client-side request lifecycle, including automatic injection of JWT Bearer tokens via an authentication link, transparent token refresh upon expiry detection via an error link, and intelligent response caching via an in-memory cache with type-specific normalisation policies.

The Apollo Client link chain is structured as: **Error Link → Auth Link → HTTP Link**. The Error Link intercepts 401 responses containing JWT expiry signatures, automatically invokes the token refresh mutation, and retries the original operation with the new access token. If refresh fails, it triggers a logout and redirects to the login page. The Auth Link injects the `Authorization: Bearer <token>` header from the Zustand authentication store. The HTTP Link dispatches the request to the `/graphql/` endpoint with `credentials: 'include'` for cookie-based session support.

### 2.5 Backend–Database Interaction

The Django application interacts with the PostgreSQL database through the Django Object-Relational Mapper (ORM), with `ATOMIC_REQUESTS` enabled to ensure that each HTTP request executes within a single database transaction — providing automatic rollback on any unhandled exception. The database schema leverages UUID primary keys throughout (via the `UUIDModel` abstract base) to facilitate distributed system compatibility and to prevent sequential ID enumeration attacks. The pgvector extension enables storage and efficient similarity search over 384-dimensional embedding vectors, supporting the semantic search component. The pg_trgm extension provides trigram-based similarity scoring for fuzzy search functionality.

Database access is further optimised through Django's query annotation capabilities (for dynamic fields such as borrow counts and average ratings), composite database indexes on frequently queried field combinations (e.g., `(user, status)`, `(book, status)`, `(role, is_active)`), conditional partial indexes for performance-critical queries (e.g., `idx_user_not_deleted` with condition `deleted_at__isnull=True`), and unique constraints with conditions (e.g., `uniq_active_reservation` ensuring a user may hold at most one active reservation per book).

### 2.6 Authentication and Authorisation Flow

Authentication is implemented through JSON Web Tokens (JWT) using the `django-graphql-jwt` library. Upon successful login, the server issues a short-lived access token (15-minute expiration) and a long-lived refresh token (7-day expiration), both signed with the HS256 algorithm. The access token is stored client-side in `localStorage` and transmitted with every GraphQL request via the `Authorization: Bearer` header. When the access token expires, the Apollo Client error link automatically detects the expiry and invokes the refresh token mutation to obtain a new token pair.

Authorisation operates on two levels. **Role-based access control (RBAC)** is enforced at the API resolver level through the `@role_required` decorator, which verifies that the authenticated user holds a role with sufficient privilege (SUPER_ADMIN, LIBRARIAN, ASSISTANT, or USER). **Module-level permission control** is managed through the `RoleConfig` model, which stores a JSON-structured permissions matrix mapping role keys to modules and CRUD actions. The frontend `PermissionGuard` component and `usePermissions` hook query these permissions and conditionally render administrative interfaces based on the authenticated user's effective permissions.

---

## 3. Technology Stack

### 3.1 Frontend

**React 18.3** serves as the user interface framework, selected for its component-based architecture, virtual DOM rendering performance, concurrent features (automatic batching, transitions), and extensive ecosystem. React's declarative programming model enables predictable UI state management, while its lazy-loading capabilities (via `React.lazy()` and `Suspense`) support code splitting across the application's 38 page components, reducing initial bundle size and improving time-to-interactive.

**TypeScript 5.7** provides static type safety across the entire frontend codebase, catching type errors at compile time, enabling superior IDE autocompletion, and improving long-term maintainability. TypeScript's strict mode is enabled, enforcing null safety and exhaustive type checking.

**Vite 6.0** is employed as the build tool and development server, chosen for its near-instantaneous Hot Module Replacement (HMR) during development (powered by native ES module resolution) and its optimised production builds via Rollup. The Vite configuration implements manual chunk splitting, separating vendor dependencies (React, Apollo, Chart.js, Framer Motion) into discrete bundles to maximize browser caching effectiveness.

**Apollo Client 3.11** manages all GraphQL communication, providing a normalised in-memory cache with type-specific merge policies, automatic query deduplication, and configurable fetch policies (`cache-and-network` for subscribed queries, `cache-first` for one-time reads). Its link chain architecture enables modular request processing, separating authentication, error handling, and HTTP transport concerns.

**Zustand 5.0** provides lightweight global state management for authentication state and UI preferences. Unlike Redux, Zustand avoids boilerplate through a minimalist API while maintaining performance through selective re-rendering. The authentication store manually persists tokens and user data to `localStorage`, with hydration executed on module initialisation.

**Tailwind CSS 3.4** enables utility-first styling with a custom design system incorporating semantic CSS custom properties (enabling dark/light theme switching via class-based toggling), custom colour scales (primary blue, accent purple, KP gamification colours), custom typography (Poppins for display, JetBrains Mono for monospace), and custom animations. The `@tailwindcss/typography` plugin provides prose styling for the e-book reader.

### 3.2 Backend

**Django 6.0.2** serves as the backend web framework, selected for its mature ORM with migration support, robust middleware pipeline, comprehensive security features (CSRF protection, clickjacking prevention, SQL injection prevention), and its "batteries-included" philosophy that reduces dependency on external packages for common functionality. Django's `ATOMIC_REQUESTS` configuration ensures transactional integrity across all API operations.

**Graphene-Django 3.x** provides the GraphQL API layer, integrating tightly with Django's ORM to enable automatic type generation from model definitions. GraphQL was chosen over REST for its single-endpoint architecture (eliminating over-fetching and under-fetching), strong typing, introspection capabilities, and its ability to serve complex, nested data structures in a single round-trip.

**Celery 5.3+** implements distributed task processing for background operations including overdue detection, recommendation refresh, embedding computation, notification delivery, streak evaluation, and model training. Celery's routing architecture distributes tasks across five dedicated queues (default, engagement, intelligence, verification, maintenance), enabling independent scaling and priority management.

**django-graphql-jwt** provides JWT authentication integrated with Graphene's middleware system, supporting token issuance, verification, refresh, and revocation with configurable expiration deltas.

### 3.3 Database

**PostgreSQL 15+** serves as the primary relational database, selected for its advanced features including the **pgvector** extension (enabling efficient cosine similarity search over 384-dimensional embedding vectors), the **pg_trgm** extension (providing trigram-based fuzzy string matching), native full-text search with `tsvector`/`ts_rank` scoring, partial indexes with conditions, JSON/JSONB column support, and ACID-compliant transactional integrity. PostgreSQL's extensibility model enables the system's hybrid search engine to execute all three search strategies (full-text, semantic, fuzzy) within the database layer, avoiding the need for external search infrastructure such as Elasticsearch.

### 3.4 API Layer

The system exposes a single **GraphQL** endpoint (`/graphql/`) that unifies all data access and mutation operations. The schema is composed from ten bounded-context-specific query and mutation classes, yielding a comprehensive API surface of 83+ queries and 82+ mutations. GraphQL was selected over REST for several architectural reasons: (i) it eliminates the N+1 endpoint problem inherent in REST APIs by allowing the client to specify exactly the data shape required; (ii) its strong typing system provides self-documenting interfaces; (iii) its introspection capability enables development tooling (GraphiQL); and (iv) its single-endpoint model simplifies security middleware application, as all traffic flows through a single path.

### 3.5 Infrastructure

**Redis 5.x** provides three infrastructure roles: (i) application caching (database 0) with a 15-minute default TTL and the `nova` key prefix, accelerating frequently accessed queries; (ii) session storage (database 1) using Django's cache-backed session engine with 30-minute rolling expiry; and (iii) Celery message brokering and result storage (database 3), decoupling task producers from consumers. Redis's in-memory architecture provides sub-millisecond response times for rate limiting counters and session lookups.

For production deployment, **Gunicorn** with **gevent** workers serves as the WSGI application server, **Sentry** provides error tracking and performance monitoring, and **Prometheus** enables metrics collection for observability.

### 3.6 AI / Background Services

**Sentence-Transformers (all-MiniLM-L6-v2)** generates 384-dimensional dense vector embeddings from book metadata (title, description, authors), enabling semantic search through cosine similarity computation over pgvector-indexed columns. This model was selected for its balance of embedding quality and computational efficiency, producing meaningful semantic representations without requiring GPU acceleration.

**scikit-learn 1.3+** provides the machine learning foundation for recommendation models (collaborative filtering via cosine similarity matrices), predictive analytics (overdue risk classification, churn prediction, demand time-series analysis), and content analysis (TF-IDF feature extraction for auto-tagging).

**Ollama** hosts the **LLaMA 3.1** large language model locally, powering two capabilities: (i) AI-powered conversational search, where user queries are enriched with book context and processed through the LLM to generate natural-language responses with source citations; and (ii) LLM analytics, where aggregated library metrics are processed through the LLM to generate natural-language insight summaries for administrators.

**pytesseract** provides OCR capabilities for extracting text from NIC/identity document images during the verification workflow, while **face-recognition** (built on dlib) performs facial encoding comparison between ID document photos and user selfies for identity verification.

---

## 4. Database Design

### 4.1 Database Design Strategy

The database schema follows a normalised relational design, primarily conforming to Third Normal Form (3NF) to eliminate data redundancy and ensure referential integrity. Strategic denormalisation is employed in specific cases for performance optimisation — notably, the `Book` entity maintains computed fields (`total_copies`, `available_copies`, `total_borrows`, `average_rating`, `rating_count`) that are synchronised upon related operations, avoiding expensive aggregate queries during catalogue browsing.

All entities utilise UUID version 4 primary keys generated at the application layer, ensuring global uniqueness without centralised sequence coordination and preventing sequential enumeration attacks. Temporal audit fields (`created_at`, `updated_at`) are provided universally through the `TimeStampedModel` abstract base. Soft deletion is implemented through the `SoftDeletableModel` mixin, which records a `deleted_at` timestamp rather than performing physical deletion, enabling data recovery and maintaining referential integrity for historical records.

The schema comprises 42 concrete entities (38 domain models plus 4 auto-generated many-to-many through tables) across 10 bounded contexts, supported by 4 abstract base models. Figure 2 (see [02-er-diagrams.md](02-er-diagrams.md)) presents the complete Entity-Relationship diagrams.

### 4.2 Common Context Entities

#### 4.2.1 SystemSetting

The `SystemSetting` entity provides a key-value configuration store for runtime-adjustable system parameters, enabling administrators to modify operational settings (circulation policies, engagement thresholds, notification preferences) without code deployment. Each setting record comprises a unique `key` identifier, a `value` stored as text, a `value_type` discriminator (`STRING`, `INTEGER`, `FLOAT`, `BOOLEAN`, `JSON`) enabling typed interpretation, a `category` classifier (`CIRCULATION`, `ENGAGEMENT`, `SECURITY`, `GENERAL`, `NOTIFICATIONS`, `EMAIL`), a human-readable `label` and `description`, and an `is_sensitive` flag that controls display masking for secrets. The `updated_by` foreign key to `User` tracks accountability for setting modifications.

**Primary key:** `id` (UUID). **Foreign keys:** `updated_by → identity.User`. **Constraints:** `key` is unique. **Normalisation:** The key-value pattern is employed instead of a wide settings table to support dynamic addition of new configuration parameters without schema migration.

### 4.3 Identity Context Entities

#### 4.3.1 User

The `User` entity extends Django's `AbstractBaseUser` and `PermissionsMixin`, inheriting password hashing (Argon2 primary hasher) and permission management, while adding the `UUIDModel` and `SoftDeletableModel` mixins. It captures authentication credentials (`email` as the username field, password managed by Django's hasher framework), personal information (`first_name`, `last_name`, `phone_number`, `date_of_birth`, `nic_number`, `institution_id`), authorisation attributes (`role` with choices SUPER_ADMIN, LIBRARIAN, ASSISTANT, USER; `is_active`; `is_staff`; `is_verified`; `verification_status`), and login telemetry (`last_login_at`, `login_count`). An `avatar_url` supports profile personalisation.

**Primary key:** `id` (UUID). **Foreign keys:** None (root entity). **Constraints:** `email` is unique; composite index on `(role, is_active)`; conditional partial index on `deleted_at IS NULL`. **Normalisation:** The entity incorporates role assignment directly rather than through a separate role-assignment junction table, as the system implements a single-role-per-user policy.

#### 4.3.2 RoleConfig

The `RoleConfig` entity defines the permission matrix for each role through a `permissions` JSON field structured as `{module_key: {action: boolean}}`. Thirteen permission modules are defined: `books`, `authors`, `digital_content`, `users`, `employees`, `circulation`, `assets`, `analytics`, `ai`, `audit`, `settings`, `roles`, `members`. Four CRUD actions (`create`, `read`, `update`, `delete`) are evaluated per module. The `is_system` flag distinguishes built-in roles from custom-created roles, preventing accidental deletion of system-critical role definitions.

**Primary key:** `id` (UUID). **Constraints:** `role_key` is unique.

#### 4.3.3 Member

The `Member` entity represents a formal library membership record, optionally linked to a `User` account via a one-to-one relationship. This separation enables creation of member records for individuals who may not have system accounts (walk-in registrations). The entity captures membership metadata (`membership_number`, `membership_type`, `status`, `joined_date`, `expiry_date`, `max_borrows`), personal details (duplicated from User for cases where no User account exists), and administrative notes.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User` (OneToOne, nullable). **Constraints:** `membership_number` is unique; composite index on `(status, membership_type)`.

#### 4.3.4 VerificationRequest

The `VerificationRequest` entity records identity verification attempts, storing document and selfie file paths, OCR extraction results (`extracted_name`, `extracted_id_number`, `ocr_confidence`), face comparison scores (`face_match_score`), review workflow state (`status`, `reviewed_by`, `reviewed_at`, `rejection_reason`), and security metadata (`attempt_number`, `ip_address`).

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `reviewed_by → User`. **Constraints:** composite index on `(user, status)`.

#### 4.3.5 RefreshToken

The `RefreshToken` entity manages JWT refresh token lifecycle, storing a cryptographic hash of the raw token (`token_hash`), device fingerprinting data, revocation state, and token rotation lineage via the self-referencing `rotated_from` foreign key — enabling token family revocation when reuse is detected.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `rotated_from → RefreshToken` (self-referential). **Constraints:** `token_hash` is unique.

#### 4.3.6 PasswordResetToken

The `PasswordResetToken` entity implements the three-step password reset flow: OTP generation, OTP verification (`otp_verified`), and password confirmation (`is_used`, `used_at`). Tokens are hashed before storage and carry expiration timestamps for time-limited validity.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`. **Constraints:** `token_hash` is unique.

### 4.4 Catalog Context Entities

#### 4.4.1 Author

The `Author` entity stores biographical information for book authors including name components, biography, lifespan dates, nationality, and a photo URL. A composite index on `(last_name, first_name)` optimises alphabetical browsing queries.

**Primary key:** `id` (UUID). **Constraints:** composite index on `(last_name, first_name)`.

#### 4.4.2 Category

The `Category` entity implements a hierarchical classification taxonomy using a self-referencing `parent` foreign key, enabling multi-level category trees (e.g., Science → Physics → Quantum Mechanics). The `slug` field provides URL-safe identifiers, and `sort_order` enables administrative control over display ordering.

**Primary key:** `id` (UUID). **Constraints:** `name` is unique; `slug` is unique.

#### 4.4.3 Book

The `Book` entity is the central catalogue entity, incorporating the `SoftDeletableModel` and `VersionedModel` mixins for safe deletion and optimistic concurrency control. It stores bibliographic metadata (`title`, `subtitle`, `isbn_10`, `isbn_13`, `publisher`, `publication_date`, `edition`, `language`, `page_count`, `description`, `table_of_contents`), classification data (many-to-many relationships with `Author` and `Category`, `dewey_decimal`, `lcc_number`, `tags` as JSON array), physical copy aggregates (`total_copies`, `available_copies`), engagement metrics (`total_borrows`, `average_rating`, `rating_count`), and an `embedding_vector` (JSON-serialised 384-dimensional vector) for semantic search. The `version` field enables optimistic concurrency — concurrent edits are detected and rejected by comparing the expected version against the stored version.

**Primary key:** `id` (UUID). **Foreign keys:** `added_by → User`. **Many-to-many:** `authors → Author`, `categories → Category`. **Constraints:** `isbn_13` is unique. **Indexes:** Eight covering indexes on title, ISBN, publisher, language, popularity, rating, and creation date.

#### 4.4.4 BookCopy

The `BookCopy` entity represents individual physical copies of a book, tracking a unique `barcode`, `condition` (NEW, GOOD, FAIR, WORN, DAMAGED), `status` (AVAILABLE, BORROWED, RESERVED, MAINTENANCE, LOST, RETIRED), physical location (`floor_number`, `shelf_number`, `shelf_location`, `branch`), and acquisition details (`acquisition_date`, `acquisition_price`, `supplier`).

**Primary key:** `id` (UUID). **Foreign keys:** `book → Book`. **Constraints:** `barcode` is unique; composite index on `(book, status)`.

#### 4.4.5 BookReview

The `BookReview` entity stores user-submitted book reviews with a rating (1–5, clamped on save), optional title and content, and an approval flag. A `unique_together` constraint on `(book, user)` ensures one review per user per book.

**Primary key:** `id` (UUID). **Foreign keys:** `book → Book`, `user → User`. **Constraints:** `unique_together = (book, user)`.

### 4.5 Circulation Context Entities

#### 4.5.1 BorrowRecord

The `BorrowRecord` entity tracks the complete lifecycle of a book borrowing transaction from issuance through return. It records the borrowing user, the specific physical copy (`book_copy`), the originating reservation (if any), temporal markers (`borrowed_at`, `due_date`, `returned_at`), renewal tracking (`renewal_count`, `max_renewals`), condition documentation (`condition_at_borrow`, `condition_at_return`), and staff attribution (`issued_by`, `returned_to`). The `status` field (ACTIVE, RETURNED, OVERDUE, LOST) is managed through domain methods that enforce business rules.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `book_copy → BookCopy`, `reservation → Reservation` (OneToOne, nullable), `issued_by → User`, `returned_to → User`. **Indexes:** Five composite indexes covering user-status, copy-status, status-due, and temporal queries.

#### 4.5.2 Reservation

The `Reservation` entity manages the book reservation queue. It records the requesting user, the target book, the assigned physical copy (populated when a copy becomes available), status transitions (PENDING → READY → FULFILLED or CANCELLED/EXPIRED), temporal markers for each state, queue positioning, and notification tracking. A conditional unique constraint (`uniq_active_reservation`) ensures that a user may hold at most one active reservation (PENDING or READY) per book.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `book → Book`, `assigned_copy → BookCopy`. **Constraints:** Conditional unique on `(user, book)` where `status IN ('PENDING', 'READY')`.

#### 4.5.3 Fine

The `Fine` entity records financial penalties assessed for overdue returns, lost items, or physical damage. It tracks the assessed amount, paid amount, currency (defaulting to LKR), status (PENDING, PAID, WAIVED, PARTIALLY_PAID), waiver attribution, and the originating borrow record.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `borrow_record → BorrowRecord`, `waived_by → User`.

#### 4.5.4 ReservationBan

The `ReservationBan` entity enforces penalty periods for users who repeatedly fail to collect reserved books. It records the no-show count, ban duration, and lifting metadata, enabling the system to temporarily restrict reservation privileges for abusive patrons.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `lifted_by → User`.

### 4.6 Digital Content Context Entities

#### 4.6.1 DigitalAsset

The `DigitalAsset` entity represents a digital file (e-book or audiobook) associated with a physical book. It stores the file path, size, hash (for integrity verification), MIME type, format-specific metadata (`duration_seconds` for audiobooks, `total_pages` for e-books, `narrator` for audiobooks), and DRM status. A `unique_together` constraint on `(book, asset_type)` ensures one digital asset per format per book.

**Primary key:** `id` (UUID). **Foreign keys:** `book → Book`, `uploaded_by → User`. **Constraints:** `unique_together = (book, asset_type)`.

#### 4.6.2 UserLibrary

The `UserLibrary` entity tracks each user's personal digital collection, recording access timestamps, overall progress, accumulated reading time, completion status, and favourite marking. A `unique_together` constraint on `(user, digital_asset)` prevents duplicate library entries.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `digital_asset → DigitalAsset`. **Constraints:** `unique_together = (user, digital_asset)`.

#### 4.6.3 ReadingSession

The `ReadingSession` entity records individual reading or listening sessions, capturing temporal boundaries, duration, progress percentage, last position (JSON for chapter/page/timestamp), KP awarded, and device metadata.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `digital_asset → DigitalAsset`.

#### 4.6.4 Bookmark and Highlight

The `Bookmark` and `Highlight` entities store user annotations within digital content. Bookmarks record a position and optional note, while highlights store selected text spans with start/end positions, colour, and notes.

**Primary keys:** `id` (UUID). **Foreign keys:** `user → User`, `digital_asset → DigitalAsset`.

### 4.7 Engagement Context Entities

#### 4.7.1 UserEngagement

The `UserEngagement` entity (one-to-one with User) serves as the aggregate root for gamification state, storing the user's total KP, current level and title, dimension-specific KP counts (explorer, scholar, connector, achiever, dedicated), streak data (current and longest), daily KP tracking, and leaderboard rank.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User` (OneToOne). **Indexes:** total_kp, level, rank.

#### 4.7.2 Achievement

The `Achievement` entity defines earnable achievements with a unique code, categorisation (READING, BORROWING, SOCIAL, STREAK, MILESTONE, SPECIAL), rarity tier (COMMON through LEGENDARY), a KP reward value, and machine-evaluable criteria stored as JSON.

**Primary key:** `id` (UUID). **Constraints:** `code` is unique.

#### 4.7.3 UserAchievement

The `UserAchievement` junction entity records which users have earned which achievements, with timestamps and KP awarded. A `unique_together` constraint on `(user, achievement)` prevents duplicate awards.

**Primary key:** `id` (UUID). **Constraints:** `unique_together = (user, achievement)`.

#### 4.7.4 DailyActivity

The `DailyActivity` entity aggregates per-user daily activity metrics (KP earned, books borrowed/returned, reading minutes, pages read, reviews written, sessions completed), enabling trend analysis and streak evaluation. A `unique_together` constraint on `(user, date)` ensures one record per user per day.

**Primary key:** `id` (UUID). **Constraints:** `unique_together = (user, date)`.

### 4.8 Intelligence Context Entities

#### 4.8.1 Recommendation

The `Recommendation` entity stores personalised book suggestions with the generating strategy (COLLABORATIVE, CONTENT_BASED, HYBRID, TRENDING, SIMILAR_USERS, BECAUSE_YOU_READ, BROWSE_BASED), a confidence score, a natural language explanation, an optional seed book reference, and interaction tracking (clicked, dismissed).

**Primary key:** `id` (UUID). **Foreign keys:** `user → User`, `book → Book`, `seed_book → Book`.

#### 4.8.2 UserPreference

The `UserPreference` entity (one-to-one with User) stores reading preference profiles including preferred/disliked categories, preferred authors and languages, reading speed, and a 384-dimensional preference vector computed from reading history.

**Primary key:** `id` (UUID). **Foreign keys:** `user → User` (OneToOne).

#### 4.8.3 SearchLog

The `SearchLog` entity records search interactions for analytics including the query text, applied filters, result count, clicked result, session identifier, and IP address.

#### 4.8.4 AIProviderConfig and AIModelVersion

The `AIProviderConfig` entity manages external AI service provider configurations (OLLAMA, OPENAI, GEMINI, LOCAL_TRANSFORMERS) with capability mapping (CHAT, EMBEDDING, SUMMARIZATION, CLASSIFICATION), health monitoring, and activation control. The `AIModelVersion` entity tracks trained model artifacts with type classification, evaluation metrics (stored as JSON), and activation state management.

#### 4.8.5 TrendingBook and BookView

The `TrendingBook` entity caches computed trending rankings by period (DAILY, WEEKLY, MONTHLY, ALL_TIME) with composite scoring from borrow, view, and review counts. The `BookView` entity logs individual book page views for analytics and trending computation.

### 4.9 Governance Context Entities

#### 4.9.1 AuditLog

The `AuditLog` entity provides an immutable, append-only record of all significant system operations. It captures the acting user (by ID, email, and role — denormalised to preserve historical attribution even if the user account is later modified), the action performed (26 action types from CREATE through SYSTEM), the affected resource (type and ID), a description, before/after value snapshots (for change tracking), request metadata (IP, user agent, request ID), and extensible metadata. The entity has no UPDATE or DELETE operations in its API — ensuring audit trail integrity.

**Primary key:** `id` (UUID). **Indexes:** Four composite indexes covering action-time, actor-time, resource, and creation.

#### 4.9.2 SecurityEvent

The `SecurityEvent` entity records security-relevant occurrences (FAILED_LOGIN, BRUTE_FORCE, TOKEN_REUSE, RATE_LIMIT, SUSPICIOUS_ACTIVITY, PRIVILEGE_ESCALATION, DATA_EXPORT, ACCOUNT_LOCKED, PASSWORD_RESET) with severity classification (LOW, MEDIUM, HIGH, CRITICAL) and resolution tracking.

#### 4.9.3 KPLedger

The `KPLedger` entity provides financial-grade, double-entry-style recording of all Knowledge Point transactions (AWARD, DEDUCT, BONUS, PENALTY, EXPIRE, ADMIN_ADJUST), storing the point delta, running balance after transaction, source reference, dimension, and metadata.

### 4.10 Asset Management Context Entities

The `AssetCategory` entity provides hierarchical categorisation for physical assets (self-referential parent). The `Asset` entity tracks individual assets with tag identification, categorisation, status/condition lifecycle, location details, financial data (purchase price, salvage value, depreciation via useful life years), maintenance scheduling, and user assignment. The `MaintenanceLog` entity records maintenance activities (PREVENTIVE, CORRECTIVE, INSPECTION, UPGRADE) with cost tracking. The `AssetDisposal` entity records asset retirement (SOLD, DONATED, RECYCLED, SCRAPPED, TRANSFERRED) with approval workflow.

### 4.11 HR Context Entities

The `Department` entity organises the institutional structure with hierarchical head-of-department references. The `Employee` entity (one-to-one with User) records employment details including department, title, employment type, salary, hire date, probation, and a self-referential `reports_to` hierarchy. The `JobVacancy` entity manages open positions with detailed descriptions, requirements, and salary ranges. The `JobApplication` entity tracks applicant submissions through the hiring pipeline (SUBMITTED → UNDER_REVIEW → SHORTLISTED → INTERVIEW → OFFERED → ACCEPTED/REJECTED/WITHDRAWN), with a `unique_together` constraint on `(vacancy, applicant_email)` preventing duplicate applications.

---

## 5. System Modules

### 5.1 Identity Module

**Purpose:** Manage the complete user identity lifecycle from registration through verification, authentication, and profile management.

**Responsibilities:** User registration with email verification; JWT-based authentication with refresh token rotation; three-step password reset (request → OTP verification → new password confirmation); NIC/identity document verification via OCR text extraction and facial recognition comparison; user profile management; member record management (walk-in and linked registrations); role-based access configuration management.

**Features:** Email-based registration with automatic engagement profile creation; login with exponential backoff lockout (5 attempts → 5-minute base lockout, doubling up to 1 hour); IP-level rate limiting (20 attempts → 10-minute lockout); NIC verification with configurable auto-approve threshold (0.75 confidence); manual review queue for low-confidence verifications; administrative user activation/deactivation; role assignment with module-level CRUD permission matrix.

**Workflow:** Upon registration, a User record is created alongside an associated UserEngagement record and default UserPreference record. The user's `is_active` flag is set to `False` until administrative activation or successful NIC verification. Login generates JWT access and refresh token pairs, with the refresh token stored as a hash in the RefreshToken entity. Password reset issues a 6-digit OTP, which must be verified before the new password is accepted.

**Database Entities:** User, RoleConfig, Member, VerificationRequest, RefreshToken, PasswordResetToken.

**API Interactions:** 11 queries (ME, GET_USERS, GET_USER, etc.), 23 mutations (LOGIN, REGISTER, REFRESH_TOKEN, VERIFY_NIC, CHANGE_PASSWORD, etc.).

### 5.2 Catalog Module

**Purpose:** Manage the library's book catalogue including bibliographic records, authors, categories, physical copies, and patron reviews.

**Responsibilities:** CRUD operations for books, authors, and categories; physical copy tracking with barcode identification and location mapping; availability computation; rating aggregation; embedding vector storage for semantic search; cover image management; soft deletion with recoverability.

**Features:** ISBN-10 and ISBN-13 support; Dewey Decimal and LCC classification; hierarchical category taxonomy; copy condition and status lifecycle management; average rating computation with count tracking; optimistic concurrency control for concurrent edits; per-book embedding vector for AI-powered similarity search.

**Workflow:** Book creation involves validating ISBN uniqueness, persisting the bibliographic record, creating initial physical copies, and scheduling embedding computation via Celery. Copy status transitions follow a state machine: AVAILABLE → RESERVED → BORROWED → RETURNED (AVAILABLE) or LOST/RETIRED. Rating updates recalculate the book's average through incremental aggregation.

**Database Entities:** Book, Author, Category, BookCopy, BookReview, and two auto-generated M2M tables (book_authors, book_categories).

### 5.3 Circulation Module

**Purpose:** Manage the complete physical book borrowing lifecycle including reservations, lending, returns, renewals, overdue management, and fine enforcement.

**Responsibilities:** Reservation creation with queue position management; pickup confirmation with copy assignment; borrow record creation; due date calculation; renewal processing (up to 2 per borrow); return processing with condition assessment; overdue detection (hourly); fine calculation with escalation tiers ($0.50/day base, escalating to $1.00 at 7 days, $1.50 at 30 days, $2.00 beyond); fine payment and waivers; reservation ban enforcement for habitual no-shows.

**Features:** Configurable borrow period (default 14 days); concurrent borrow limit (2); concurrent reservation limit (2); 12-hour pickup window; reservation queue with automatic copy assignment; overdue reminder schedule (3, 1, 0, −1, −3, −7 days relative to due date); unpaid fine threshold blocking new borrows ($25.00); abuse detection (3 no-shows in 30 days triggers 7-day reservation ban).

**Database Entities:** BorrowRecord, Reservation, Fine, ReservationBan.

### 5.4 Digital Content Module

**Purpose:** Manage digital library assets and provide streaming access to e-books and audiobooks with reading progress tracking.

**Responsibilities:** Digital asset upload and management (PDF, EPUB, audiobook formats); e-book page rendering; audiobook streaming; reading/listening session lifecycle management; progress tracking; bookmark and highlight management; user digital library curation with favourites.

**Database Entities:** DigitalAsset, UserLibrary, ReadingSession, Bookmark, Highlight.

### 5.5 Engagement Module

**Purpose:** Implement gamification mechanics to incentivise sustained library engagement through Knowledge Points, achievements, streaks, and competitive leaderboards.

**Responsibilities:** KP award computation across five dimensions with configurable weights (Reading Time 0.30, Completion 0.25, Content Creation 0.20, Consistency 0.15, Diversity 0.10); streak multiplier application (3d → 1.1×, 7d → 1.2×, 14d → 1.3×, 30d → 1.5×); daily KP cap enforcement (200); level progression (Curious Reader → Active Learner → Knowledge Seeker → Scholar → Thought Leader); achievement evaluation and unlock; daily activity aggregation; leaderboard ranking.

**Database Entities:** UserEngagement, Achievement, UserAchievement, DailyActivity.

### 5.6 Intelligence Module

**Purpose:** Provide AI-powered capabilities including hybrid search, personalised recommendations, predictive analytics, LLM interaction, and smart notifications.

**Responsibilities:** Hybrid search execution combining full-text (weight 0.45), semantic (0.35), and fuzzy (0.20) strategies; recommendation generation using collaborative filtering, content-based filtering, trending analysis, and hybrid merging; predictive analytics for overdue risk, demand forecasting, churn detection, and collection gap identification; LLM-powered conversational search via Ollama; natural language analytics summaries; notification delivery with deduplication and daily caps; AI provider configuration management; model training pipeline orchestration with evaluation metrics (Precision@K, Recall@K, NDCG, MRR).

**Database Entities:** Recommendation, UserPreference, SearchLog, AIProviderConfig, AIModelVersion, TrendingBook, BookView.

### 5.7 Governance Module

**Purpose:** Ensure regulatory compliance, operational transparency, and system auditability through comprehensive logging.

**Responsibilities:** Append-only audit logging of all significant operations (26 action types); security event detection and recording (9 event types with severity classification); Knowledge Point ledger maintenance for financial-grade KP transaction recording.

**Database Entities:** AuditLog, SecurityEvent, KPLedger.

### 5.8 Asset Management Module

**Purpose:** Track physical library assets (furniture, equipment, technology) through their complete lifecycle.

**Responsibilities:** Asset registration with tag identification; hierarchical categorisation; condition and status lifecycle management; maintenance scheduling and logging; depreciation calculation; disposal management with approval workflow.

**Database Entities:** AssetCategory, Asset, MaintenanceLog, AssetDisposal.

### 5.9 HR Module

**Purpose:** Manage institutional human resource operations including organisational structure, employee records, and recruitment.

**Responsibilities:** Department management; employee lifecycle tracking (hire, probation, active, leave, termination); organisational hierarchy (reports_to); salary management; job vacancy publishing; application pipeline management.

**Database Entities:** Department, Employee, JobVacancy, JobApplication.

---

## 6. UML and System Design

### 6.1 ER Diagram Explanation

Figure 2 (see [02-er-diagrams.md](02-er-diagrams.md)) presents the complete Entity-Relationship diagrams organised by bounded context. The diagrams illustrate 42 entities with their attributes, primary keys, and inter-entity relationships. Key relationships include: the one-to-many relationship between Book and BookCopy (a single bibliographic record may have multiple physical copies); the one-to-many relationship between User and BorrowRecord (a user may have multiple active or historical borrows); the many-to-many relationships between Book and Author/Category (implemented through auto-generated junction tables); the one-to-one relationship between User and UserEngagement (each user has exactly one gamification profile); and the self-referencing relationships in Category (parent hierarchy), Employee (reports_to), and RefreshToken (rotated_from).

Cross-context relationships are explicitly documented: Circulation references Catalog entities (BorrowRecord → BookCopy, Reservation → Book); Digital Content references Catalog (DigitalAsset → Book); Intelligence references Catalog (Recommendation → Book, TrendingBook → Book); Engagement references Identity (UserEngagement → User); and Governance references Identity (AuditLog.actor_id → User.id, though stored as UUID rather than a foreign key to avoid coupling).

### 6.2 Use Case Diagram Explanation

Figure 3 (see [03-use-case-diagrams.md](03-use-case-diagrams.md)) presents actor-based use case diagrams for each of the six system actors. The Public User actor has 21 use cases centring on catalogue browsing, searching, and registration. The Library Member actor extends the Public User with 38 additional use cases including borrowing, digital reading, gamification, and notification management. The Librarian actor has 37 administrative use cases for catalogue management, circulation oversight, and analytics access. The Administrator and Super Administrator actors add progressively elevated capabilities for user management, system configuration, AI management, and HR operations. The System (Celery) actor has 12 automated use cases executed on scheduled intervals.

### 6.3 Class Diagram Explanation

Figure 4 (see [04-class-diagrams.md](04-class-diagrams.md)) presents UML class diagrams for each bounded context, illustrating the inheritance hierarchy from abstract base models through concrete entity classes. The diagrams detail all attributes with their types, key domain methods, and inter-class relationships (association, composition, generalisation). The abstract base hierarchy — `TimeStampedModel → UUIDModel`, with `SoftDeletableModel` and `VersionedModel` as mixins — is documented as the foundation from which all domain entities derive. Service classes (SearchEngine, RecommendationEngine, PredictiveAnalytics) are included with their public interfaces.

### 6.4 Sequence Diagram Explanation

Figure 5 (see [05-sequence-diagrams.md](05-sequence-diagrams.md)) presents 14 sequence diagrams covering the system's critical interaction workflows. These include: the user registration flow (client → GraphQL → IdentityService → User creation → Engagement initialisation → Audit logging); the authentication flow with JWT issuance; the token refresh cycle; the three-step password reset; the complete reservation-to-borrow handoff; the book return with fine assessment and KP award; the hybrid search pipeline (parallel full-text, semantic, and fuzzy execution with weighted merge); the LLM-powered conversational search; recommendation generation; overdue detection; NIC verification with OCR and face recognition; digital content reading session lifecycle; the GraphQL request lifecycle through the middleware pipeline; and Knowledge Points award with ledger recording.

### 6.5 Architecture Diagram Explanation

Figures 6 and 7 (see [06-component-diagrams.md](06-component-diagrams.md) and [07-data-flow-diagrams.md](07-data-flow-diagrams.md)) present component and data flow diagrams respectively. The component diagrams illustrate the system's structural decomposition: the full system topology (client, gateway, application contexts, infrastructure), the internal structure of a bounded context (domain, application, infrastructure, presentation layers), the frontend component architecture (layouts, guards, pages, UI design system, hooks, stores), the middleware pipeline sequence, the Intelligence/AI module's sub-components, the Celery task queue routing, the Apollo Client link chain, and the database component layout (PostgreSQL with extensions). The data flow diagrams trace information movement through: the overall system, authentication flows, book lifecycle (creation through borrowing and return), event bus propagation, KP computation, search execution, recommendation generation, digital content streaming, and audit trail accumulation.

---

## 7. System Workflows

### 7.1 User Registration

The registration workflow begins when a public user submits a registration form containing email, first name, last name, and password. The React frontend dispatches the `REGISTER` mutation through Apollo Client. The GraphQL resolver invokes the Identity application service, which: (i) validates that the email is not already registered; (ii) hashes the password using Argon2; (iii) creates the User record with `is_active=False` and `role=USER`; (iv) creates the associated UserEngagement record (initialising KP at zero, level at 1); (v) creates a default UserPreference record; (vi) emits a `USER_REGISTERED` event to the event bus, triggering an audit log entry and a welcome notification. The user must subsequently be activated by an administrator or through the NIC verification workflow before gaining full system access.

### 7.2 Authentication

The login workflow begins with the user submitting email and password credentials. The `LOGIN` mutation resolver: (i) checks for active account lockout (evaluating failed attempts within the 15-minute sliding window against the 5-attempt threshold); (ii) validates credentials against the Argon2-hashed password; (iii) upon success, records the login event (`last_login_at`, `login_count`), generates JWT access and refresh tokens, and returns the token pair; (iv) upon failure, increments the failed attempt counter and checks whether the lockout threshold has been reached. The access token carries a 15-minute TTL; the refresh token carries a 7-day TTL and is stored as a SHA-256 hash in the RefreshToken entity. When the access token expires, the Apollo Client error link detects the `Signature has expired` error, invokes the `REFRESH_TOKEN` mutation, and retries the original operation transparently.

### 7.3 Core System Operations

**Book Borrowing:** A librarian initiates the `confirmPickup` mutation for a ready reservation, which: (i) validates the reservation status is READY; (ii) creates a BorrowRecord linking the user, book copy, and reservation; (iii) transitions the reservation to FULFILLED; (iv) transitions the book copy to BORROWED; (v) updates the book's available copy count; (vi) emits a `BOOK_BORROWED` event triggering audit logging, KP award, and notification.

**Book Return:** The `returnBook` mutation: (i) validates the borrow record is ACTIVE or OVERDUE; (ii) marks the borrow as RETURNED with the current timestamp; (iii) transitions the book copy back to AVAILABLE; (iv) updates copy counts; (v) if the return is overdue, creates a Fine record with the calculated amount; (vi) emits a `BOOK_RETURNED` event triggering audit logging, KP award, and potential reservation queue advancement.

**Hybrid Search:** The `searchBooks` query invokes the SearchEngine service, which executes three strategies in parallel: (a) full-text search using PostgreSQL tsvector matching with ts_rank scoring (weight 0.45); (b) semantic search by encoding the query text into a 384-dim vector and computing cosine similarity against book embedding vectors (weight 0.35); (c) fuzzy search using pg_trgm trigram similarity (weight 0.20). Results are merged by book ID, scores are weighted and summed, duplicates are removed, user-specified filters are applied, facet counts are computed, and the final ranked result set is returned.

### 7.4 Administrative Operations

Administrative operations are governed by the RBAC permission matrix. When an administrator accesses an admin page, the `PermissionGuard` component queries `MY_PERMISSIONS`, which returns the user's role configuration. The guard evaluates whether the user's role grants the required module-action permission (e.g., `books.create`). Administrative mutations similarly verify permissions at the resolver level before executing domain logic. All administrative actions generate audit log entries recording the actor, action, resource, and before/after value snapshots.

---

## 8. Security Design

### 8.1 Authentication Mechanism

The system employs JWT-based stateless authentication with the HS256 symmetric signing algorithm. Access tokens carry a 15-minute expiration to limit the window of compromise for intercepted tokens. Refresh tokens carry a 7-day expiration and are rotated upon each refresh operation, with the previous token linked via the `rotated_from` field. If a revoked refresh token is reused, the system revokes the entire token family (all tokens derived from the same lineage), mitigating replay attacks. Passwords are hashed using Argon2 (the winner of the Password Hashing Competition), with PBKDF2 as a fallback. Account lockout is implemented with exponential backoff: 5 failed attempts within a 15-minute window trigger a 5-minute lockout, doubling with each subsequent lockout up to a 1-hour maximum.

### 8.2 Authorisation Model

Authorisation operates on two tiers. The first tier is role-based: four user roles (SUPER_ADMIN, LIBRARIAN, ASSISTANT, USER) are arranged in a hierarchical privilege model, enforced by the `@role_required` decorator at the resolver level. The second tier is module-action-based: the `RoleConfig` entity defines a JSON permissions matrix mapping 13 modules to 4 CRUD actions per module, allowing fine-grained control without code modification. The frontend enforces permission visibility through the `PermissionGuard` component, which conditionally renders administrative interfaces based on the user's effective permissions.

### 8.3 Data Protection Strategy

Data protection is implemented through multiple layers. **Transport security:** in production, HSTS is enforced with a 2-year max-age, SSL redirect is mandatory, and secure cookie flags are set. **Input validation:** all user inputs pass through Django's validation framework, with additional custom validators for NIC numbers, ISBN formats, and email addresses. HTML content is sanitised server-side and client-side (via DOMPurify with a strict whitelist). File uploads are validated by extension, MIME type, and size against configurable limits. **Output security:** security headers are injected by the `SecurityHeadersMiddleware`, including Content-Security-Policy (with per-request nonces), X-Content-Type-Options, Referrer-Policy, Permissions-Policy (disabling all sensitive browser APIs), and Cross-Origin-Opener-Policy. Sensitive configuration values (API keys, passwords) are stored with the `is_sensitive` flag, triggering display masking and preventing accidental exposure in API responses.

### 8.4 Access Control

The GraphQL security middleware enforces structural constraints on all incoming queries: maximum depth (10, production 8), maximum complexity (1000, production 800), maximum aliases (15), maximum query size (10KB), and maximum batch operations (5, production 3). Introspection is disabled in production to prevent schema enumeration. Rate limiting is implemented through Redis-backed token bucket counters with five tiers: AUTH (5/minute), MUTATION (30/minute), QUERY (120/minute), HEARTBEAT (60/minute), and UPLOAD (10/hour). All security violations are recorded as SecurityEvent entries with severity classification. The system implements automatic session timeout (30-minute server-side rolling session, 30-minute client-side inactivity detection triggering automatic logout).

---

## 9. Implementation Details

### 9.1 Frontend Architecture

The frontend is structured as a single-page application with 38 page components organised into four route groups: auth (4 pages), member (18 pages), admin (16 pages), and error handling (1 page). All page components are lazy-loaded through `React.lazy()` with a `Suspense` fallback, enabling code-splitting that reduces the initial bundle size. The application bootstrap stack comprises `React.StrictMode → ApolloProvider → BrowserRouter → ThemeProvider → App`, establishing the GraphQL client, routing context, and theme context for all descendant components.

The component library comprises three tiers: (i) **layout components** (AppLayout, AdminLayout, AuthLayout, Header, Sidebar) providing structural scaffolding; (ii) **auth guard components** (ProtectedRoute, AdminRoute, PermissionGuard) enforcing access control at the routing level; and (iii) **20+ UI components** (Avatar, Badge, Button, Card, DataTable, Modal, Pagination, SearchInput, Spinner, StarRating, Tabs, Tooltip, etc.) forming a reusable design system. Styling is implemented through Tailwind CSS with a custom design token system using CSS custom properties, enabling theme switching between light and dark modes via the `ThemeProvider` context.

### 9.2 Backend Architecture

The backend follows a layered package structure within each bounded context: `domain/models.py` (entity definitions and domain logic), `application/services.py` (use case orchestration), `infrastructure/` (repository implementations, external service adapters), and `presentation/` (GraphQL types, queries, mutations). This separation ensures domain logic remains independent of framework concerns.

The middleware pipeline processes requests in the following order: Django SecurityMiddleware → CorsMiddleware → SessionMiddleware → CommonMiddleware → CsrfViewMiddleware → AuthenticationMiddleware → MessageMiddleware → XFrameOptionsMiddleware → RequestLoggingMiddleware (assigns 8-character request ID, logs timing) → SecurityHeadersMiddleware (injects CSP with nonce, security headers) → GraphQLSecurityMiddleware (validates depth, complexity, aliases, size, batch count) → RateLimitingMiddleware (Redis-backed token bucket) → ExceptionHandlerMiddleware (maps domain exceptions to HTTP status codes).

### 9.3 API Design

The GraphQL schema is composed through Python multiple inheritance, with each bounded context contributing its query and mutation classes to the root schema. The root schema additionally exposes a `health` query returning `"ok"` for load balancer probing. Authentication-exempt operations (token obtain, verify, refresh) are explicitly whitelisted in the `JWT_ALLOW_ANY_CLASSES` configuration. All other operations require a valid JWT.

Pagination follows a flat, offset-based model (not the Relay cursor specification) with configurable page sizes. The Apollo Client implements custom `flatConnectionPagination` functions that merge paginated results by `keyArgs` (e.g., `[query, categoryId, authorId, language]` for book queries), enabling efficient cache utilisation across filtered views.

### 9.4 Database Implementation

Database migrations are managed through Django's migration framework, which generates version-controlled migration files from model changes. The PostgreSQL database is augmented with two extensions: `pgvector` (installed via `CREATE EXTENSION vector`) for embedding storage and similarity operations, and `pg_trgm` (installed via `CREATE EXTENSION pg_trgm`) for trigram-based fuzzy matching. The embedding column is stored as a JSON field at the application level (as Django does not natively support pgvector types), with raw SQL queries executed through Django's `connection.cursor()` for cosine similarity computation.

---

## 10. Testing Strategy

### 10.1 Testing Methodology

The testing strategy employs pytest as the test runner, integrated with Django through `pytest-django`. Tests are organised within each bounded context's `tests/` directory, following the same modular structure as the production code. The test configuration uses a dedicated settings profile (`nova.settings.test`) that substitutes PostgreSQL with an in-memory SQLite database for execution speed and replaces the Argon2 password hasher with MD5 for rapid credential verification.

### 10.2 Test Levels

**Unit tests** (marked with `@pytest.mark.unit`) validate individual domain model methods, service functions, and utility helpers in isolation. **Integration tests** (marked with `@pytest.mark.integration`) verify end-to-end workflows including GraphQL mutation execution, database persistence, event emission, and cross-context interactions. **AI-specific tests** (marked with `@pytest.mark.ai`) validate machine learning pipeline components including embedding computation, recommendation generation, and search result quality. Tests marked with `@pytest.mark.slow` are excluded from the default test suite and executed separately in CI pipelines.

### 10.3 Validation Strategy

Input validation is tested at multiple levels: (i) model-level validation through Django's `full_clean()` method, ensuring field constraints (max_length, choices, validators) are enforced; (ii) GraphQL resolver-level validation through mutation tests that verify rejection of invalid inputs with appropriate error messages; (iii) middleware-level validation through tests that verify query depth limiting, complexity rejection, alias counting, and rate limiting enforcement.

### 10.4 Data Integrity Verification

Data integrity is validated through: (i) constraint enforcement tests verifying that unique constraints (`unique_together`, conditional unique constraints) correctly prevent duplicate records; (ii) referential integrity tests verifying that `on_delete` cascades, SET_NULL handlers, and PROTECT constraints function as designed; (iii) optimistic concurrency tests verifying that `save_with_version_check` rejects stale updates; (iv) soft deletion tests verifying that `SoftDeletableManager` correctly filters deleted records from default query sets while preserving them in `all_with_deleted()` queries.

Test infrastructure includes `factory-boy` for declarative test data factories, `faker` for realistic synthetic data, `freezegun` for temporal determinism, `responses` for HTTP mock servers, and `pytest-mock` for dependency injection. Parallel test execution is supported through `pytest-xdist`.

---

## 11. Design Decisions and Justifications

### 11.1 Architecture Decisions

**Domain-Driven Design (DDD)** was selected because the system spans multiple complex business domains (library operations, digital content, gamification, AI/ML, HR, asset management) that benefit from explicit domain boundary enforcement. The bounded context pattern prevents the domain model from becoming a monolithic, tightly-coupled entity graph, enabling independent evolution of each context's internal implementation without cascading changes. The four-layer architecture within each context (domain, application, infrastructure, presentation) ensures that business logic remains portable and framework-independent — the domain layer has no dependency on Django, GraphQL, or any infrastructure concern.

**GraphQL over REST** was chosen because library systems involve heavily nested data structures (books with authors, categories, copies, reviews, digital assets, recommendations) that would require multiple REST round-trips to assemble. GraphQL's client-specified data shape eliminates over-fetching (requesting only needed fields) and under-fetching (retrieving nested data in a single request), improving both network efficiency and frontend development velocity. Additionally, GraphQL's strong typing and introspection provide self-documenting API contracts.

### 11.2 Technology Selection Justification

**Django** was selected for its mature ORM (eliminating manual SQL construction while supporting raw SQL when needed for pgvector operations), built-in security middleware (CSRF, XSS, clickjacking protection), migration framework (version-controlled schema evolution), and administrative interface. Its synchronous request model aligns well with the database-heavy workload, while CPU-intensive AI tasks are offloaded to Celery workers.

**React with TypeScript** was selected for the frontend due to its component-based architecture (enabling creation of a reusable design system), strong type safety (preventing runtime type errors), extensive ecosystem (Apollo Client, React Router, Zustand, Framer Motion), and industry-standard developer tooling. Vite was chosen over Create React App for its order-of-magnitude faster HMR performance.

**PostgreSQL** was selected over alternatives (MySQL, MongoDB) for its extension ecosystem — specifically pgvector for embedding storage and pg_trgm for fuzzy matching — which enables the hybrid search engine to operate entirely within the database layer, eliminating the operational complexity of a separate search infrastructure (Elasticsearch, Meilisearch).

### 11.3 Database Design Reasoning

**UUID primary keys** were selected to prevent sequential ID enumeration attacks, to support potential future horizontal scaling (no sequence coordination required), and to enable client-side ID generation for optimistic UI updates. The trade-off of slightly larger index sizes (16 bytes vs. 8 bytes for bigint) is acceptable given the security and architectural benefits.

**Soft deletion** (via `SoftDeletableModel`) was implemented for entities where historical data must be preserved for audit, analytics, and referential integrity (Users, Books, BookCopies, DigitalAssets, Members). The `SoftDeletableManager` transparently filters deleted records from default querysets while preserving access through `all_with_deleted()` for administrative recovery.

**Optimistic concurrency control** (via `VersionedModel`) was implemented for the Book entity to prevent lost updates in concurrent editing scenarios. The `save_with_version_check` method accepts an expected version number and raises an exception if the stored version has been incremented by a concurrent transaction, prompting the user to refresh and retry.

### 11.4 Scalability Considerations

The architecture supports horizontal scalability through several mechanisms: (i) stateless JWT authentication enables load balancing across multiple application instances without session affinity; (ii) Redis-backed caching, session storage, and rate limiting enable shared state across instances; (iii) Celery task queue distribution across five dedicated queues enables independent worker scaling per workload type (intelligence tasks can be scaled independently of circulation tasks); (iv) database connection pooling (`CONN_MAX_AGE=600` in production) reduces connection establishment overhead; (v) the event bus pattern decouples event producers from consumers, enabling additional consumers to be added without modifying producers.

### 11.5 Maintainability Considerations

Long-term maintainability is ensured through: (i) the DDD bounded context organisation, which enables teams to work on independent modules with minimal coordination; (ii) the four-layer architecture within each context, ensuring that framework changes (e.g., migrating from Graphene to Strawberry) affect only the presentation and infrastructure layers; (iii) comprehensive audit logging, providing full operational visibility for debugging and compliance; (iv) structured JSON logging with correlation IDs (request_id), enabling distributed log aggregation and tracing; (v) the `SystemSetting` entity, enabling runtime configuration changes without code deployment; (vi) the AI provider factory pattern, enabling swapping of AI providers (Ollama → OpenAI → Gemini) without modifying consuming code; and (vii) the comprehensive test infrastructure with factory-based data generation, temporal determinism, and parallel execution support.

---

*This document serves as the comprehensive technical reference for the Nova Smart Library Management Ecosystem, suitable for direct conversion into a university-level thesis report. All architectural descriptions, entity definitions, and workflow explanations are derived from the actual system implementation and accurately reflect the production codebase.*
