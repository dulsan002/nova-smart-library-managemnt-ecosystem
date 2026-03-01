# Nova Smart Library Management Ecosystem

> **AI-Powered Full-Stack Library Management Platform** built with Django (GraphQL) + React (TypeScript)

A comprehensive digital library system featuring book catalog management, physical/digital circulation, AI-powered search & recommendations, gamification, identity verification (OCR + face recognition), and full admin dashboards — designed using **Domain-Driven Design (DDD)** principles.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Seed the Database](#4-seed-the-database)
  - [5. Run the Application](#5-run-the-application)
- [Environment Variables](#environment-variables)
- [Available Scripts](#available-scripts)
- [GraphQL API](#graphql-api)
- [Authentication](#authentication)
- [Bounded Contexts (Modules)](#bounded-contexts-modules)
- [AI/ML Features](#aiml-features)
- [Celery Background Tasks](#celery-background-tasks)
- [Testing](#testing)
- [Seeded Test Accounts](#seeded-test-accounts)
- [Useful URLs](#useful-urls)
- [Custom Middleware](#custom-middleware)
- [Troubleshooting](#troubleshooting)
- [Project Conventions](#project-conventions)

---

## Tech Stack

| Layer               | Technology                          |
| ------------------- | ----------------------------------- |
| **Backend**         | Django 4.2, Graphene-Django (GraphQL) |
| **Frontend**        | React 18, TypeScript 5.7, Vite 6   |
| **Database**        | PostgreSQL 15+ with pgvector        |
| **Cache / Broker**  | Redis 5+                            |
| **Task Queue**      | Celery 5.3                          |
| **State Mgmt**      | Zustand + Apollo Client             |
| **CSS**             | Tailwind CSS 3.4                    |
| **Auth**            | JWT (graphql-jwt, HS256)            |
| **AI/ML**           | scikit-learn, sentence-transformers, Ollama (LLM) |
| **OCR**             | pytesseract + Pillow                |
| **Face Recognition**| face-recognition + OpenCV           |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     React SPA (Vite + TS)                       │
│          Apollo Client │ Zustand │ TailwindCSS │ React Router   │
└──────────────────────────────┬──────────────────────────────────┘
                               │  GraphQL (POST /graphql/)
┌──────────────────────────────▼──────────────────────────────────┐
│                    Django Backend (DDD)                          │
│  ┌───────────┐ ┌──────────┐ ┌────────────┐ ┌────────────────┐  │
│  │ Identity   │ │ Catalog  │ │Circulation │ │Digital Content │  │
│  ├───────────┤ ├──────────┤ ├────────────┤ ├────────────────┤  │
│  │Engagement │ │Intelligence│ │Governance │ │Asset Management│  │
│  ├───────────┤ ├──────────┤ ├────────────┤ ├────────────────┤  │
│  │    HR     │ │  Common  │ │            │ │                │  │
│  └───────────┘ └──────────┘ └────────────┘ └────────────────┘  │
│                                                                  │
│  Middleware: Security Headers │ Rate Limiting │ GQL Depth Guard  │
└──────┬─────────────┬──────────────┬─────────────────────────────┘
       │             │              │
  ┌────▼────┐  ┌─────▼─────┐  ┌────▼─────┐
  │PostgreSQL│  │   Redis   │  │  Celery  │
  │+ pgvector│  │Cache/Queue│  │ Workers  │
  └─────────┘  └───────────┘  └──────────┘
```

Each Django app follows the **DDD layered architecture**:

```
apps/<context>/
├── domain/          # Models, value objects, business rules
├── application/     # Service layer (use cases)
├── infrastructure/  # Repositories, external adapters
├── presentation/    # GraphQL types, queries, mutations
├── tests/           # Unit & integration tests
└── migrations/      # Database migrations
```

---

## Project Structure

```
nova-smart-library-managemnt-ecosystem/
├── backend/
│   ├── manage.py                  # Django entry point
│   ├── celery_app.py              # Celery configuration
│   ├── conftest.py                # Shared pytest fixtures
│   ├── pytest.ini                 # Pytest configuration
│   ├── .env                       # Backend environment variables (not in git)
│   ├── requirements/
│   │   ├── base.txt               # Core dependencies
│   │   ├── dev.txt                # Development tools (debug toolbar, linters)
│   │   ├── test.txt               # Testing dependencies
│   │   └── prod.txt               # Production (gunicorn, sentry, S3)
│   ├── nova/                      # Django project package
│   │   ├── settings/
│   │   │   ├── base.py            # Shared settings (all environments)
│   │   │   ├── development.py     # Dev overrides (DEBUG, port 5433)
│   │   │   ├── production.py      # Production (SSL, Sentry, Gunicorn)
│   │   │   └── test.py            # Test (SQLite in-memory, fast hasher)
│   │   ├── middleware/            # 5 custom middleware
│   │   ├── schema.py             # Root GraphQL schema
│   │   └── urls.py               # URL routing
│   ├── apps/
│   │   ├── identity/             # Users, roles, JWT, verification
│   │   ├── catalog/              # Books, authors, categories, reviews
│   │   ├── circulation/          # Borrowing, reservations, fines
│   │   ├── digital_content/      # eBooks, audiobooks, reading sessions
│   │   ├── engagement/           # Knowledge Points, achievements, streaks
│   │   ├── intelligence/         # AI search, recommendations, analytics
│   │   ├── governance/           # Audit logs, security events
│   │   ├── asset_management/     # Physical library assets
│   │   ├── hr/                   # Departments, employees, vacancies
│   │   └── common/               # Shared utilities, base models, event bus
│   ├── logs/                     # Application log files (git-ignored)
│   ├── media/                    # Uploaded files (git-ignored)
│   └── templates/                # Email & HTML templates
│
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── vite.config.ts             # Vite config (dev server port 3000, proxy)
│   ├── tailwind.config.ts         # Tailwind theme customization
│   ├── tsconfig.json
│   ├── .env                       # Frontend env variables (not in git)
│   └── src/
│       ├── App.tsx                 # Root component with routing
│       ├── main.tsx                # Entry point
│       ├── components/
│       │   ├── ui/                 # 20+ reusable UI components
│       │   ├── auth/               # ProtectedRoute, PermissionGuard
│       │   └── layout/             # AppLayout, AdminLayout, Sidebar, Header
│       ├── pages/
│       │   ├── auth/               # Login, Register, ForgotPassword, Reset
│       │   ├── catalog/            # CatalogPage, BookDetailPage
│       │   ├── circulation/        # MyBorrows, MyReservations, MyFines
│       │   ├── digital/            # DigitalLibrary, Reader, AudiobookPlayer
│       │   ├── engagement/         # Achievements, KnowledgePoints, Leaderboard
│       │   ├── intelligence/       # Recommendations, Insights, Notifications
│       │   └── admin/              # 16 admin dashboard pages
│       ├── graphql/
│       │   ├── queries/            # 13 query modules
│       │   └── mutations/          # 11 mutation modules
│       ├── hooks/                  # useAutoLogout, useDebounce, usePermissions...
│       ├── stores/                 # authStore, uiStore (Zustand)
│       └── lib/                    # Apollo client, constants, security, utils
│
├── .gitignore
└── README.md
```

---

## Prerequisites

Ensure you have the following installed on your machine:

| Tool                | Version  | Purpose                              |
| ------------------- | -------- | ------------------------------------ |
| **Python**          | 3.11+    | Backend runtime                      |
| **Node.js**         | 18+      | Frontend runtime                     |
| **npm**             | 9+       | Frontend package manager             |
| **PostgreSQL**      | 15+      | Primary database                     |
| **Redis**           | 5+       | Caching, sessions, Celery broker     |
| **Tesseract OCR**   | 4+       | ID document text extraction (optional) |
| **Ollama**          | Latest   | Local LLM for AI features (optional) |

### Install System Dependencies (Ubuntu/Debian)

```bash
# PostgreSQL & Redis
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server

# Tesseract OCR (for ID verification features)
sudo apt install tesseract-ocr

# Python build dependencies (required for face-recognition package)
sudo apt install cmake build-essential libdlib-dev
```

### Install System Dependencies (macOS)

```bash
brew install postgresql redis tesseract cmake
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/nova-smart-library-managemnt-ecosystem.git
cd nova-smart-library-managemnt-ecosystem
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows

# Install dependencies (dev includes linters + testing tools)
pip install -r requirements/dev.txt
```

#### Create the `.env` file

Create `backend/.env` with the following content (adjust values as needed):

```dotenv
# Django
DJANGO_SETTINGS_MODULE=nova.settings.development
DJANGO_SECRET_KEY=dev-secret-key-not-for-production-use-change-me-in-prod-12345678
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Admin panel URL path
DJANGO_ADMIN_URL=nova-admin-panel/

# Database (PostgreSQL) — adjust port if yours runs on 5432
DATABASE_NAME=nova_db
DATABASE_USER=nova_user
DATABASE_PASSWORD=nova_password
DATABASE_HOST=localhost
DATABASE_PORT=5433
DATABASE_SSL_MODE=prefer

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/0
REDIS_SESSION_URL=redis://localhost:6379/1
REDIS_CELERY_URL=redis://localhost:6379/3

# Celery
CELERY_BROKER_URL=redis://localhost:6379/3
CELERY_RESULT_BACKEND=redis://localhost:6379/3

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_SIGNING_KEY=dev-jwt-signing-key-not-for-production

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173

# AI Configuration
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
FACE_RECOGNITION_TOLERANCE=0.6
OCR_LANGUAGE=eng
RECOMMENDATION_CACHE_TTL=86400

# Rate Limiting
RATE_LIMIT_DEFAULT=100/hour
RATE_LIMIT_AUTH=5/minute
RATE_LIMIT_UPLOAD=10/hour

# Account Security
ACCOUNT_MAX_FAILED_ATTEMPTS=5

# GraphQL Security
GQL_MAX_DEPTH=10
GQL_MAX_COMPLEXITY=1000

# Email (dev uses console backend — emails print to terminal)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

#### Set Up PostgreSQL

```bash
# Start PostgreSQL if not already running
sudo systemctl start postgresql

# Create user and database
sudo -u postgres psql <<SQL
CREATE USER nova_user WITH PASSWORD 'nova_password';
CREATE DATABASE nova_db OWNER nova_user;
ALTER USER nova_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE nova_db TO nova_user;
\c nova_db
CREATE EXTENSION IF NOT EXISTS vector;
SQL
```

> **Important:** The development config uses PostgreSQL on port **5433**. If your PostgreSQL runs on the default port **5432**, update `DATABASE_PORT=5432` in `backend/.env`.

#### Run Migrations

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

Create `frontend/.env` if it doesn't exist:

```dotenv
VITE_GRAPHQL_URL=http://localhost:8000/graphql/
VITE_APP_NAME=Nova Library
VITE_APP_VERSION=1.0.0
```

### 4. Seed the Database

The project includes a comprehensive seed command that populates the database with realistic test data across all 10 modules:

```bash
cd backend
source .venv/bin/activate
python manage.py seed_data
```

This creates:
- **Admin, Librarian, Assistant** accounts
- **20 patron users** with full profiles
- **Books, authors, categories** with relationships
- **Borrowing records, reservations, fines**
- **Digital assets** (eBooks, audiobooks)
- **Engagement data** (Knowledge Points, achievements, streaks)
- **And more across all modules...**

| Seed Option                             | Description             |
| --------------------------------------- | ----------------------- |
| `python manage.py seed_data`            | Full seed               |
| `python manage.py seed_data --flush`    | Wipe DB and re-seed     |
| `python manage.py seed_data --minimal`  | Minimal dataset only    |

### 5. Run the Application

You need **3 terminals** to run the full stack (4 if using Celery with Redis):

#### Terminal 1 — Backend (Django)

```bash
cd backend
source .venv/bin/activate
python manage.py runserver
```

The server starts at **http://localhost:8000**.

#### Terminal 2 — Frontend (Vite)

```bash
cd frontend
npm run dev
```

The dev server starts at **http://localhost:3000** and proxies API requests to Django.

#### Terminal 3 — Redis (if not running as a service)

```bash
redis-server
```

#### Terminal 4 — Celery Worker (optional)

```bash
cd backend
source .venv/bin/activate
celery -A celery_app worker -l info -Q default,engagement,intelligence,verification,maintenance
```

> **Note:** If Redis is not available, the development settings **automatically fall back** to in-memory caching and synchronous Celery (tasks run inline). You can develop without Redis.

---

## Available Scripts

### Backend

| Command                                      | Description                                     |
| -------------------------------------------- | ----------------------------------------------- |
| `python manage.py runserver`                 | Start Django dev server (port 8000)             |
| `python manage.py migrate`                   | Apply database migrations                       |
| `python manage.py seed_data`                 | Populate database with test data                |
| `python manage.py seed_data --flush`         | Wipe DB and re-seed                             |
| `python manage.py createsuperuser`           | Create Django admin superuser                   |
| `python manage.py compute_embeddings`        | Generate AI embeddings for all books            |
| `python manage.py train_models`              | Train AI/ML recommendation models               |
| `python manage.py predict_overdue`           | Run overdue risk predictions                    |
| `python manage.py refresh_trending`          | Refresh trending book rankings                  |
| `python manage.py auto_tag_books`            | Auto-tag books using AI                         |
| `python manage.py detect_duplicates`         | Detect duplicate catalog entries                |
| `python manage.py analyze_churn`             | Analyze user churn risk                         |
| `python manage.py compute_reading_levels`    | Compute book reading difficulty levels          |
| `pytest`                                      | Run all backend tests                           |
| `pytest --cov`                                | Run tests with coverage                         |
| `pytest -m unit`                              | Run only unit tests                             |
| `pytest -m integration`                       | Run only integration tests                      |

### Frontend

| Command                | Description                          |
| ---------------------- | ------------------------------------ |
| `npm run dev`          | Start Vite dev server (port 3000)    |
| `npm run build`        | Build for production                 |
| `npm run preview`      | Preview production build             |
| `npm run lint`         | Run ESLint                           |
| `npm run lint:fix`     | Auto-fix lint issues                 |
| `npm run format`       | Format code with Prettier            |
| `npm run type-check`   | TypeScript type checking             |
| `npm run test`         | Run tests (Vitest)                   |
| `npm run test:watch`   | Run tests in watch mode              |
| `npm run test:coverage`| Coverage report                      |
| `npm run codegen`      | Generate GraphQL TypeScript types    |

### Celery

| Command                                                                    | Description                     |
| -------------------------------------------------------------------------- | ------------------------------- |
| `celery -A celery_app worker -l info -Q default,engagement,intelligence,verification,maintenance` | Start worker (all queues) |
| `celery -A celery_app beat -l info`                                       | Start periodic task scheduler   |

---

## GraphQL API

The entire API is served through a **single endpoint**: `POST /graphql/`

### Interactive Explorer (GraphiQL)

When `DEBUG=True`, visit **http://localhost:8000/graphql/** in your browser to access the **GraphiQL IDE** — an interactive playground where you can explore the schema, write queries, and test mutations with auto-complete.

### Example: Login

```graphql
mutation {
  tokenAuth(email: "admin@nova.local", password: "NovaTest@2026") {
    token
    refreshToken
    user {
      id
      email
      firstName
      role
    }
  }
}
```

### Example: Search Books

```graphql
query {
  books(search: "python", first: 10) {
    edges {
      node {
        id
        title
        isbn
        authors {
          name
        }
        averageRating
      }
    }
  }
}
```

### Using the Token

Include the JWT in the `Authorization` header for all authenticated requests:

```
Authorization: Bearer <your-token>
```

---

## Authentication

| Setting                | Value                        |
| ---------------------- | ---------------------------- |
| **Method**             | JWT (JSON Web Tokens)        |
| **Access Token TTL**   | 15 minutes                   |
| **Refresh Token TTL**  | 7 days                       |
| **Password Hashing**   | Argon2 (production-grade)    |
| **Account Lockout**    | After 5 failed attempts      |
| **Roles**              | `SUPER_ADMIN`, `LIBRARIAN`, `ASSISTANT`, `USER` |

---

## Bounded Contexts (Modules)

| Context              | Description                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------- |
| **Identity**         | User registration (email-based), JWT auth, role-based access (RBAC), ID verification via OCR + face recognition, password reset via OTP |
| **Catalog**          | Books, authors, categories (hierarchical), physical copies with barcode/condition tracking, book reviews & ratings, AI embedding vectors |
| **Circulation**      | Borrow → return lifecycle, reservations with pickup deadlines, automatic fines (overdue/lost/damage), reservation bans for no-shows, anti-abuse tracking |
| **Digital Content**  | eBooks (EPUB/PDF) and audiobooks (MP3), page-by-page reading, audio streaming, bookmarks, highlights, progress tracking |
| **Engagement**       | Knowledge Points (KP) gamification across 5 dimensions, daily streaks, 10 levels, achievements/badges with 5 rarity tiers, leaderboards, daily KP cap (200) |
| **Intelligence**     | Hybrid AI search (keyword + semantic), 7 recommendation strategies, trending books, predictive overdue analytics, book auto-tagging, LLM-powered insights (Ollama) |
| **Governance**       | Immutable audit logging, security event tracking (failed logins, brute force detection), KP transaction ledger (append-only) |
| **Asset Management** | Physical library assets (furniture, equipment, computers), maintenance scheduling, depreciation tracking, disposal records |
| **HR**               | Departments, employee management (linked to users), job vacancies, application pipeline with recruitment stages |
| **Common**           | Shared base models (`TimeStampedModel`, `UUIDModel`, `SoftDeletableModel`), domain event bus, validators, sanitizers, pagination, email service, system settings |

---

## AI/ML Features

| Feature                   | Technology                 | Description                                    |
| ------------------------- | -------------------------- | ---------------------------------------------- |
| **Semantic Search**       | sentence-transformers      | Vector similarity search using book embeddings (pgvector) |
| **Recommendations**       | scikit-learn               | 7 strategies: content-based, collaborative, hybrid, trending, new arrivals, similar readers, for-you |
| **Overdue Prediction**    | scikit-learn               | Predicts which active borrows are likely to become overdue |
| **Book Auto-Tagging**     | NLP (nltk)                 | Automatically assigns tags based on book content |
| **LLM Insights**          | Ollama (llama3.1)          | Natural language book insights, Q&A, summaries  |
| **Face Recognition**      | face-recognition + OpenCV  | User identity verification during registration  |
| **OCR**                   | pytesseract                | ID document text extraction for verification    |
| **Churn Analysis**        | scikit-learn               | Identifies users at risk of becoming inactive    |

> **Note:** All AI features **degrade gracefully** — the application works fully without Ollama or pre-trained models. Run `python manage.py compute_embeddings` and `python manage.py train_models` to enable AI features.

---

## Celery Background Tasks

Periodic tasks run automatically via Celery Beat:

| Task                          | Frequency     | Queue          |
| ----------------------------- | ------------- | -------------- |
| Detect overdue transactions   | Every 1 hour  | maintenance    |
| Cleanup expired sessions      | Every 15 min  | maintenance    |
| Evaluate daily streaks        | Daily         | engagement     |
| Refresh recommendations       | Every 6 hours | intelligence   |
| Predict overdue risks         | Every 4 hours | intelligence   |
| Compute book embeddings       | Every 6 hours | intelligence   |
| Compute trending books        | Every 3 hours | intelligence   |
| Auto-tag new books            | Every 12 hours| intelligence   |
| Deliver notifications         | Every 5 min   | default        |
| Analyze churn risks           | Weekly        | intelligence   |
| Weekly model training         | Weekly        | intelligence   |

**Celery Queues:** `default`, `engagement`, `intelligence`, `verification`, `maintenance`

---

## Testing

### Backend

```bash
cd backend
source .venv/bin/activate

pytest                          # Run all tests
pytest --cov                    # With coverage report
pytest -m unit                  # Unit tests only
pytest -m integration           # Integration tests only
pytest -m "not slow"            # Skip slow tests
pytest apps/catalog/tests/      # Tests for a specific module
pytest -x                       # Stop on first failure
```

Test environment uses: SQLite in-memory (fast), MD5 hasher (fast), synchronous Celery, disabled rate limiting, suppressed logging.

Shared test fixtures are in `backend/conftest.py` — includes factories for users, books, authors, categories, borrow records, and engagement profiles.

### Frontend

```bash
cd frontend

npm run test                    # Run all tests
npm run test:watch              # Watch mode
npm run test:coverage           # With coverage report
```

---

## Seeded Test Accounts

After running `python manage.py seed_data`, these accounts are available:

| Role          | Email                    | Password          |
| ------------- | ------------------------ | ----------------- |
| Super Admin   | `admin@nova.local`       | `NovaTest@2026`   |
| Librarian     | `librarian@nova.local`   | `NovaTest@2026`   |
| Assistant     | `assistant@nova.local`   | `NovaTest@2026`   |
| Patron (User) | `alice@nova.local`      | `NovaTest@2026`   |

> 20 additional patron users are also created. Check the seed command output for all emails.

---

## Useful URLs

| URL                                     | Description                        |
| --------------------------------------- | ---------------------------------- |
| http://localhost:3000                    | Frontend (React SPA)               |
| http://localhost:8000/graphql/           | GraphQL API + GraphiQL IDE         |
| http://localhost:8000/nova-admin-panel/  | Django Admin panel                 |
| http://localhost:8000/healthz/           | Health check (for load balancers)  |

---

## Custom Middleware

The backend includes 5 custom security/utility middleware layers:

| Middleware                | Purpose                                                    |
| ------------------------- | ---------------------------------------------------------- |
| **RequestLogging**        | Logs every request with unique ID, user, path, response time |
| **SecurityHeaders**       | Adds X-Content-Type-Options, CSP, HSTS, X-Frame-Options, Referrer-Policy |
| **GraphQLSecurity**       | Query depth limiting (max 10), complexity analysis (max 1000), introspection control (DEBUG only), batch request limiting |
| **RateLimiting**          | Redis-backed per-IP and per-user rate limiting — multi-tier: Auth (5/min), Mutations (30/min), Queries (120/min), Uploads (10/hr) |
| **ExceptionHandler**      | Maps domain exceptions to proper HTTP status codes, prevents stack trace leaks in production |

---

## Troubleshooting

### "Redis not available" warning on startup

**This is fine for development.** The app automatically falls back to in-memory caching and synchronous Celery. Background tasks execute inline instead of asynchronously. No features are lost.

### PostgreSQL connection refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check which port it's using
sudo -u postgres psql -c "SHOW port;"

# If port is 5432 (default), update DATABASE_PORT in backend/.env to 5432
```

### pgvector extension not found

```bash
# Install pgvector (adjust PostgreSQL version as needed)
sudo apt install postgresql-15-pgvector

# Enable it on the database
sudo -u postgres psql -d nova_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Database reset (development only)

```bash
sudo -u postgres psql -c "DROP DATABASE nova_db; CREATE DATABASE nova_db OWNER nova_user;"
sudo -u postgres psql -d nova_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
cd backend && python manage.py migrate && python manage.py seed_data
```

### Frontend proxy errors / CORS issues

The Vite dev server proxies `/graphql`, `/api`, and `/media` to `localhost:8000`. Ensure the Django backend is running first.

### face-recognition installation fails

Requires `dlib` which needs `cmake`:

```bash
sudo apt install cmake build-essential
pip install dlib
pip install face-recognition
```

### Tesseract not found

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

---

## Project Conventions

| Area            | Convention                                                          |
| --------------- | ------------------------------------------------------------------- |
| **Backend**     | PEP 8, enforced with `flake8` + `black` + `isort`                  |
| **Frontend**    | TypeScript strict mode, ESLint + Prettier                           |
| **Architecture** | DDD bounded contexts — cross-context communication via event bus   |
| **API**         | GraphQL only (REST used only for file uploads + health check)       |
| **Auth**        | All GraphQL operations require JWT unless explicitly public         |
| **Git**         | Feature branches, conventional commits encouraged                   |
| **Logging**     | 4 rotating log files: general, error, security, audit               |

---

## License

This project is for educational and demonstration purposes.
