# 01 — Architecture Overview

> System Architecture, Design Principles, Technology Stack, and Deployment Topology

---

## 1. Design Philosophy

Nova Smart Library Management Ecosystem follows **Domain-Driven Design (DDD)** principles with clean architecture patterns:

| Principle | Implementation |
|-----------|---------------|
| **Bounded Contexts** | 10 independent domain modules with clear boundaries |
| **Layered Architecture** | Each context has `domain/`, `application/`, `infrastructure/`, `presentation/` layers |
| **CQRS-like Separation** | Queries and mutations separated at the GraphQL schema level |
| **Event-Driven** | Central event bus for cross-context communication |
| **Soft Deletes** | `SoftDeletableModel` with `is_deleted` flag and custom manager |
| **Optimistic Concurrency** | `VersionedModel` with auto-incrementing `version` field |
| **Repository Pattern** | Domain services encapsulate data access logic |
| **Single Responsibility** | Each module owns its models, services, and API surface |

---

## 2. System Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        SPA["React 18 SPA<br/>TypeScript 5.7 + Vite 6"]
        SPA -->|"Apollo Client<br/>GraphQL over HTTP"| GW
    end

    subgraph "API Gateway Layer"
        GW["Django GraphQL Endpoint<br/>/graphql/"]
        MW1["RequestLoggingMiddleware"]
        MW2["SecurityHeadersMiddleware"]
        MW3["GraphQLSecurityMiddleware<br/>Depth · Complexity · Aliases"]
        MW4["RateLimitingMiddleware<br/>Token Bucket per IP/User"]
        MW5["ExceptionHandlerMiddleware"]
        GW --> MW1 --> MW2 --> MW3 --> MW4 --> MW5
    end

    subgraph "Application Layer — Bounded Contexts"
        direction LR
        BC1["Identity<br/>Users · Auth · RBAC"]
        BC2["Catalog<br/>Books · Authors · Categories"]
        BC3["Circulation<br/>Borrows · Reservations · Fines"]
        BC4["Digital Content<br/>E-books · Audiobooks · Sessions"]
        BC5["Engagement<br/>KP · Achievements · Streaks"]
        BC6["Intelligence<br/>Search · Recommendations · AI"]
        BC7["Governance<br/>Audit · Security · KP Ledger"]
        BC8["Asset Mgmt<br/>Assets · Maintenance"]
        BC9["HR<br/>Employees · Jobs"]
        BC10["Common<br/>Base Models · Utilities"]
    end

    MW5 --> BC1
    MW5 --> BC2
    MW5 --> BC3
    MW5 --> BC4
    MW5 --> BC5
    MW5 --> BC6
    MW5 --> BC7
    MW5 --> BC8
    MW5 --> BC9

    subgraph "Infrastructure Layer"
        PG[("PostgreSQL 15+<br/>+ pgvector extension<br/>Port 5433")]
        RD[("Redis<br/>Cache DB0 · Sessions DB1<br/>Celery Broker DB3")]
        CL["Celery Workers<br/>5 queues · 12 periodic tasks"]
        OL["Ollama LLM Server<br/>llama3.1 · Port 11434"]
        ST["Sentence Transformers<br/>all-MiniLM-L6-v2"]
        FS["File Storage<br/>media/ directory"]
    end

    BC1 --> PG
    BC2 --> PG
    BC3 --> PG
    BC4 --> PG
    BC5 --> PG
    BC6 --> PG
    BC6 --> OL
    BC6 --> ST
    BC7 --> PG
    BC8 --> PG
    BC9 --> PG
    BC1 --> RD
    BC6 --> CL
    BC3 --> CL
    BC5 --> CL
    CL --> RD
    BC4 --> FS
    BC1 --> FS
```

---

## 3. Bounded Context Map

The system is organized into 10 bounded contexts, each responsible for a specific business domain:

```mermaid
graph LR
    subgraph "Core Domain"
        Catalog["Catalog<br/>Books · Authors<br/>Categories · Copies"]
        Circulation["Circulation<br/>Borrows · Reservations<br/>Fines · Returns"]
        Identity["Identity<br/>Users · Members<br/>Auth · RBAC"]
    end

    subgraph "Supporting Domain"
        Digital["Digital Content<br/>E-books · Audiobooks<br/>Reading Sessions"]
        Engagement["Engagement<br/>Knowledge Points<br/>Achievements · Streaks"]
        Intelligence["Intelligence<br/>AI Search · Recommendations<br/>Predictive Analytics"]
    end

    subgraph "Generic Domain"
        Governance["Governance<br/>Audit Logs<br/>Security Events"]
        Assets["Asset Management<br/>Physical Assets<br/>Maintenance"]
        HR["HR<br/>Employees · Departments<br/>Job Vacancies"]
        Common["Common<br/>Base Models · Event Bus<br/>Utilities"]
    end

    Circulation -->|"borrows books from"| Catalog
    Circulation -->|"borrows by"| Identity
    Digital -->|"digital version of"| Catalog
    Engagement -->|"tracks activity of"| Identity
    Engagement -->|"awards KP for"| Circulation
    Intelligence -->|"searches"| Catalog
    Intelligence -->|"recommends to"| Identity
    Intelligence -->|"analyzes"| Circulation
    Governance -->|"audits all"| Identity
    Governance -->|"tracks KP"| Engagement
    HR -->|"links to"| Identity
    Common -.->|"base for all"| Catalog
    Common -.->|"base for all"| Circulation
    Common -.->|"base for all"| Identity
```

---

## 4. DDD Layer Architecture (per Bounded Context)

Each bounded context follows a 4-layer architecture:

```mermaid
graph TB
    subgraph "Presentation Layer"
        Schema["schema.py<br/>GraphQL Types · Queries · Mutations"]
        Views["views.py<br/>REST endpoints (where needed)"]
    end

    subgraph "Application Layer"
        Services["services.py<br/>Use Case Orchestration"]
        DTOs["DTOs / Input Types"]
    end

    subgraph "Domain Layer"
        Models["models.py<br/>Entities · Value Objects"]
        DomainSvc["Domain Services<br/>Business Rules"]
        Events["events.py<br/>Domain Events"]
    end

    subgraph "Infrastructure Layer"
        Repos["repositories.py<br/>Data Access"]
        External["External Services<br/>LLM · OCR · Face Recognition"]
        Tasks["tasks.py<br/>Celery Async Tasks"]
    end

    Schema --> Services
    Views --> Services
    Services --> Models
    Services --> DomainSvc
    Services --> Events
    DomainSvc --> Models
    Services --> Repos
    Services --> External
    Services --> Tasks
    Repos --> Models
```

---

## 5. Technology Stack Detail

### 5.1 Backend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | Django 6.0.2 | HTTP handling, ORM, admin |
| API Layer | Graphene-Django 3.x | GraphQL schema and resolvers |
| Authentication | django-graphql-jwt | JWT-based auth (HS256) |
| Password Hashing | Argon2 (primary) + PBKDF2 | Secure password storage |
| Database | PostgreSQL 15+ | Relational data storage |
| Vector Store | pgvector | Book embedding storage and similarity search |
| Cache | Redis (django-redis) | Query caching, session storage |
| Task Queue | Celery 5.3+ (Redis broker) | Async background tasks |
| Embedding Model | sentence-transformers (all-MiniLM-L6-v2) | 384-dim book embeddings |
| ML Framework | scikit-learn | Recommendation, prediction models |
| LLM | Ollama (llama3.1) | Conversational AI, analytics |
| OCR | pytesseract + Pillow | ID document text extraction |
| Face Recognition | face-recognition + OpenCV | Identity verification |
| NLP | NLTK | Text processing, tokenization |
| ASGI Server | Uvicorn | Production async server |

### 5.2 Frontend Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | React 18.3 | Component-based UI |
| Language | TypeScript 5.7 | Type-safe JavaScript |
| Build Tool | Vite 6.0 | HMR dev server and bundler |
| GraphQL Client | Apollo Client 3.11 | Query, mutation, cache management |
| State Management | Zustand 5.0 | Lightweight client state |
| CSS Framework | Tailwind CSS 3.4 | Utility-first styling |
| Form Management | react-hook-form 7.54 + Zod | Form validation |
| Animations | Framer Motion 11.15 | UI animations |
| Charts | Chart.js 4.4 + react-chartjs-2 | Data visualization |
| UI Components | Headless UI 2.2 + Heroicons 2.2 | Accessible primitives |
| Routing | React Router DOM 6.28 | Client-side routing |
| Notifications | react-hot-toast 2.4 | Toast messages |
| Security | DOMPurify 3.3 | XSS prevention |
| Testing | Vitest + Testing Library | Unit and component tests |

### 5.3 Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Database | PostgreSQL on port 5433 | Primary data store |
| Cache | Redis on port 6379 (DB 0, 1, 3) | Caching, sessions, Celery broker |
| LLM Server | Ollama on port 11434 | Local AI model hosting |
| Dev Server | Vite on port 3000 | Frontend dev with HMR |
| Backend Server | Django on port 8000 | API serving |
| File Storage | Local `media/` directory | Uploads, covers, digital assets |

---

## 6. Deployment Topology

```mermaid
graph TB
    subgraph "Client"
        Browser["Web Browser"]
    end

    subgraph "Frontend Server"
        Vite["Vite Dev Server<br/>:3000"]
        Proxy["Proxy Rules<br/>/graphql → :8000<br/>/api → :8000<br/>/media → :8000"]
    end

    subgraph "Backend Server"
        Django["Django + Uvicorn<br/>:8000"]
        GraphQL["GraphQL Endpoint<br/>/graphql/"]
        Admin["Django Admin<br/>/nova-admin-panel/"]
        Health["/healthz/"]
        Upload["/api/upload/verification/"]
        Media["/media/digital/..."]
    end

    subgraph "Workers"
        CeleryDefault["Celery Worker<br/>default queue"]
        CeleryEngagement["Celery Worker<br/>engagement queue"]
        CeleryIntelligence["Celery Worker<br/>intelligence queue"]
        CeleryVerification["Celery Worker<br/>verification queue"]
        CeleryMaintenance["Celery Worker<br/>maintenance queue"]
        CeleryBeat["Celery Beat<br/>Periodic Scheduler"]
    end

    subgraph "Data Stores"
        PG[("PostgreSQL<br/>:5433")]
        Redis[("Redis<br/>:6379")]
    end

    subgraph "AI Services"
        Ollama["Ollama<br/>:11434<br/>llama3.1"]
    end

    Browser --> Vite
    Vite --> Proxy --> Django
    Django --> GraphQL
    Django --> PG
    Django --> Redis
    Django --> Ollama
    CeleryDefault --> PG
    CeleryDefault --> Redis
    CeleryIntelligence --> Ollama
    CeleryIntelligence --> PG
    CeleryBeat --> Redis
```

---

## 7. Module Dependency Matrix

| Module | Depends On | Depended By |
|--------|-----------|-------------|
| **Common** | — | All modules |
| **Identity** | Common | Circulation, Engagement, Intelligence, Governance, HR |
| **Catalog** | Common | Circulation, Digital Content, Intelligence |
| **Circulation** | Common, Identity, Catalog | Engagement, Intelligence, Governance |
| **Digital Content** | Common, Identity, Catalog | Engagement, Intelligence |
| **Engagement** | Common, Identity | Governance |
| **Intelligence** | Common, Identity, Catalog, Circulation, Digital Content | — |
| **Governance** | Common, Identity, Engagement | — |
| **Asset Management** | Common | — |
| **HR** | Common, Identity | — |

---

## 8. Key Design Patterns

| Pattern | Where Used | Purpose |
|---------|-----------|---------|
| **Repository** | Domain services in each context | Data access abstraction |
| **Factory** | AI Provider Factory | Dynamic provider selection |
| **Strategy** | Recommendation Engine | Collaborative / Content-based / Hybrid |
| **Observer / Event Bus** | `common/event_bus.py` | Cross-context event propagation |
| **Decorator** | `common/decorators.py` | Auth, caching, rate limiting |
| **Template Method** | Abstract base models | Common lifecycle behavior |
| **Middleware Chain** | Django middleware stack | Request/response processing |
| **CQRS** | GraphQL Query vs. Mutation | Read/write separation |
| **Optimistic Locking** | `VersionedModel` | Concurrent update safety |
| **Soft Delete** | `SoftDeletableModel` | Non-destructive data removal |
