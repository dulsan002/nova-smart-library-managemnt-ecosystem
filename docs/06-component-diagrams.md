# 06 — Component Diagrams

> Backend and frontend component architecture diagrams showing module boundaries, dependencies, and communication patterns

---

## 1. Full System Component Overview

```mermaid
graph TB
    subgraph "Client Tier"
        subgraph "React SPA"
            Pages["Pages (38)"]
            Components["UI Components (34)"]
            Stores["Zustand Stores (2)"]
            Hooks["Custom Hooks (7)"]
            GQLLayer["GraphQL Layer<br/>24 query/mutation files"]
            ApolloClient["Apollo Client<br/>InMemoryCache"]
        end
    end

    subgraph "API Tier"
        subgraph "Django Application"
            Middleware["Middleware Stack (5 custom)"]
            subgraph "GraphQL Schema"
                RootQuery["Root Query<br/>10 context queries"]
                RootMutation["Root Mutation<br/>9 context mutations"]
            end
            subgraph "Bounded Contexts (10)"
                Identity["Identity"]
                Catalog["Catalog"]
                Circulation["Circulation"]
                DigitalContent["Digital Content"]
                Engagement["Engagement"]
                Intelligence["Intelligence"]
                Governance["Governance"]
                AssetMgmt["Asset Management"]
                HR["HR"]
                Common["Common"]
            end
        end
    end

    subgraph "Worker Tier"
        CeleryBeat["Celery Beat<br/>12 periodic tasks"]
        CeleryWorkers["Celery Workers<br/>5 queues"]
    end

    subgraph "Data Tier"
        PostgreSQL[("PostgreSQL<br/>+ pgvector")]
        Redis[("Redis<br/>Cache + Broker")]
    end

    subgraph "AI Tier"
        Ollama["Ollama LLM<br/>llama3.1"]
        SentenceTransformers["Sentence Transformers<br/>all-MiniLM-L6-v2"]
    end

    Pages --> Components
    Pages --> Hooks
    Pages --> GQLLayer
    GQLLayer --> ApolloClient
    Stores --> ApolloClient
    ApolloClient -->|"HTTP POST"| Middleware
    Middleware --> RootQuery
    Middleware --> RootMutation
    RootQuery --> Identity
    RootQuery --> Catalog
    RootQuery --> Circulation
    RootQuery --> DigitalContent
    RootQuery --> Engagement
    RootQuery --> Intelligence
    RootQuery --> Governance
    RootQuery --> AssetMgmt
    RootQuery --> HR
    RootMutation --> Identity
    RootMutation --> Catalog
    RootMutation --> Circulation
    RootMutation --> DigitalContent
    RootMutation --> Engagement
    RootMutation --> Intelligence
    RootMutation --> AssetMgmt
    RootMutation --> HR
    Intelligence --> Ollama
    Intelligence --> SentenceTransformers
    CeleryBeat --> CeleryWorkers
    CeleryWorkers --> Redis
    CeleryWorkers --> PostgreSQL
    Identity --> PostgreSQL
    Catalog --> PostgreSQL
    Circulation --> PostgreSQL
    Intelligence --> PostgreSQL
    Identity --> Redis
```

---

## 2. Backend — Bounded Context Internal Structure

```mermaid
graph TB
    subgraph "Each Bounded Context"
        subgraph "presentation/"
            Schema["schema.py<br/>GraphQL Types<br/>Queries & Mutations"]
            Views["views.py<br/>REST endpoints"]
        end

        subgraph "application/"
            AppServices["services.py<br/>Use Case Orchestration"]
        end

        subgraph "domain/"
            Models["models.py<br/>Domain Entities"]
            DomainServices["services.py<br/>Business Rules"]
            Events["events.py<br/>Domain Events"]
            Enums["enums.py<br/>Value Objects"]
        end

        subgraph "infrastructure/"
            Repos["repositories.py<br/>Data Access"]
            External["External Integrations"]
            Tasks["tasks.py<br/>Async Tasks"]
            Signals["signals.py<br/>Django Signals"]
        end

        subgraph "tests/"
            UnitTests["test_models.py"]
            IntTests["test_services.py"]
            APITests["test_schema.py"]
        end

        Admin["admin.py<br/>Django Admin"]
        Apps["apps.py<br/>App Config"]
        Migrations["migrations/<br/>DB Migrations"]
    end

    Schema --> AppServices
    Views --> AppServices
    AppServices --> Models
    AppServices --> DomainServices
    AppServices --> Events
    DomainServices --> Models
    AppServices --> Repos
    AppServices --> External
    AppServices --> Tasks
    Signals --> AppServices
```

---

## 3. Frontend — Component Architecture

```mermaid
graph TB
    subgraph "Entry Point"
        Main["main.tsx<br/>ApolloProvider + Router"]
        App["App.tsx<br/>Route Definitions"]
    end

    subgraph "Layout Components"
        AuthLayout["AuthLayout<br/>Login/Register shell"]
        AppLayout["AppLayout<br/>Member shell"]
        AdminLayout["AdminLayout<br/>Admin shell"]
        Header["Header"]
        Sidebar["Sidebar"]
        MobileSidebar["MobileSidebar"]
        Breadcrumbs["Breadcrumbs"]
    end

    subgraph "Route Guards"
        ProtectedRoute["ProtectedRoute<br/>Auth check"]
        AdminRoute["AdminRoute<br/>Admin check"]
        PermissionGuard["PermissionGuard<br/>RBAC check"]
    end

    subgraph "Page Components (38)"
        AuthPages["Auth Pages (4)<br/>Login, Register,<br/>ForgotPassword, Reset"]
        MemberPages["Member Pages (16)<br/>Dashboard, Catalog,<br/>Borrows, Digital, etc."]
        AdminPages["Admin Pages (16)<br/>Dashboard, Users,<br/>Books, Analytics, etc."]
        NotFound["NotFoundPage"]
    end

    subgraph "UI Component Library (21)"
        FormControls["Form Controls<br/>Button, Input, Select,<br/>Textarea, SearchInput"]
        DataDisplay["Data Display<br/>Card, Badge, Avatar,<br/>DataTable, StarRating,<br/>ProgressBar"]
        Feedback["Feedback<br/>Spinner, Modal,<br/>ConfirmDialog, EmptyState"]
        Navigation["Navigation<br/>Tabs, Dropdown,<br/>Tooltip, Pagination"]
        Security["SafeHtml<br/>DOMPurify wrapper"]
    end

    subgraph "State Management"
        AuthStore["authStore<br/>user, tokens, auth state"]
        UIStore["uiStore<br/>sidebar, search overlay"]
    end

    subgraph "Data Layer"
        ApolloConfig["apollo.ts<br/>Client configuration"]
        Queries["13 query files"]
        Mutations["11 mutation files"]
    end

    subgraph "Hooks"
        UseDebounce["useDebounce"]
        UseInfiniteScroll["useInfiniteScroll"]
        UsePermissions["usePermissions"]
        UseAutoLogout["useAutoLogout"]
        UseDocTitle["useDocumentTitle"]
        UseLocalStorage["useLocalStorage"]
        UseKeyboard["useKeyboardShortcut"]
    end

    Main --> App
    App --> AuthLayout
    App --> AppLayout
    App --> AdminLayout
    AppLayout --> ProtectedRoute
    AdminLayout --> AdminRoute
    AdminRoute --> PermissionGuard
    AuthLayout --> AuthPages
    ProtectedRoute --> MemberPages
    PermissionGuard --> AdminPages
    AppLayout --> Header
    AppLayout --> Sidebar
    AppLayout --> MobileSidebar
    MemberPages --> FormControls
    MemberPages --> DataDisplay
    MemberPages --> Feedback
    AdminPages --> FormControls
    AdminPages --> DataDisplay
    AdminPages --> Navigation
    MemberPages --> Queries
    MemberPages --> Mutations
    AdminPages --> Queries
    AdminPages --> Mutations
    Queries --> ApolloConfig
    Mutations --> ApolloConfig
    ProtectedRoute --> AuthStore
    AdminRoute --> AuthStore
    PermissionGuard --> UsePermissions
```

---

## 4. Middleware Pipeline Component

```mermaid
graph LR
    Request["HTTP Request"] --> MW1

    subgraph "Django Middleware Stack"
        MW1["SecurityMiddleware<br/>(Django built-in)"]
        MW2["CorsMiddleware<br/>(django-cors-headers)"]
        MW3["SessionMiddleware"]
        MW4["CommonMiddleware"]
        MW5["CsrfViewMiddleware"]
        MW6["AuthenticationMiddleware"]
        MW7["MessageMiddleware"]
        MW8["XFrameOptionsMiddleware"]
        MW9["RequestLoggingMiddleware<br/>(custom)"]
        MW10["SecurityHeadersMiddleware<br/>(custom)"]
        MW11["GraphQLSecurityMiddleware<br/>(custom)"]
        MW12["RateLimitingMiddleware<br/>(custom)"]
        MW13["ExceptionHandlerMiddleware<br/>(custom)"]
    end

    MW1 --> MW2 --> MW3 --> MW4 --> MW5 --> MW6 --> MW7 --> MW8 --> MW9 --> MW10 --> MW11 --> MW12 --> MW13

    MW13 --> View["GraphQL View<br/>/ REST View"]
    View --> Response["HTTP Response"]
```

---

## 5. Intelligence Module — AI/ML Components

```mermaid
graph TB
    subgraph "Intelligence Bounded Context"
        subgraph "Presentation"
            IntelSchema["schema.py<br/>85+ query/mutation resolvers"]
        end

        subgraph "Infrastructure"
            subgraph "Search"
                SearchEngine["SearchEngine<br/>Hybrid Search<br/>(fulltext + semantic + fuzzy)"]
                LLMSearch["LLM Search Service<br/>Conversational AI search"]
            end

            subgraph "Recommendation"
                RecEngine["RecommendationEngine<br/>Collaborative + Content-based"]
            end

            subgraph "Analytics"
                Predictive["PredictiveAnalytics<br/>Overdue, Demand, Churn"]
                ContentAnalysis["ContentAnalysis<br/>Auto-tagging, Reading Level"]
                ReadingBehavior["ReadingBehavior<br/>Speed, Patterns, Heatmap"]
                LLMAnalytics["LLM Analytics<br/>Natural language insights"]
            end

            subgraph "Verification"
                OCR["OCR Service<br/>pytesseract"]
                Face["Face Service<br/>face-recognition"]
            end

            subgraph "AI Providers"
                Factory["AI Provider Factory"]
                OllamaProvider["Ollama Provider"]
                OpenAIProvider["OpenAI Provider"]
                GeminiProvider["Gemini Provider"]
                LocalProvider["Local Transformers"]
            end

            subgraph "Pipeline"
                Training["Training Pipeline"]
                Evaluation["Model Evaluation<br/>Precision, Recall, NDCG"]
                Notifications["Notification Engine"]
            end

            Tasks["Celery Tasks"]
            Signals["Django Signals"]
        end
    end

    subgraph "External"
        Ollama["Ollama Server<br/>llama3.1"]
        ST["Sentence Transformers<br/>all-MiniLM-L6-v2"]
        PGVector[("pgvector<br/>Book embeddings")]
    end

    IntelSchema --> SearchEngine
    IntelSchema --> LLMSearch
    IntelSchema --> RecEngine
    IntelSchema --> Predictive
    IntelSchema --> ReadingBehavior
    IntelSchema --> LLMAnalytics

    SearchEngine --> ST
    SearchEngine --> PGVector
    LLMSearch --> Factory
    LLMAnalytics --> Factory
    Factory --> OllamaProvider
    Factory --> OpenAIProvider
    Factory --> GeminiProvider
    Factory --> LocalProvider
    OllamaProvider --> Ollama
    RecEngine --> PGVector
    Tasks --> RecEngine
    Tasks --> Training
    Tasks --> SearchEngine
    Training --> Evaluation
```

---

## 6. Celery Task Queue Components

```mermaid
graph TB
    subgraph "Celery Beat Scheduler"
        Beat["Celery Beat<br/>Periodic Task Scheduler"]
    end

    subgraph "Task Queues"
        Q1["default queue"]
        Q2["engagement queue"]
        Q3["intelligence queue"]
        Q4["verification queue"]
        Q5["maintenance queue"]
    end

    subgraph "Periodic Tasks"
        T1["deliver_notifications<br/>every 5 min"]
        T2["evaluate_daily_streaks<br/>daily"]
        T3["refresh_recommendations<br/>every 6h"]
        T4["predict_overdue_risks<br/>every 4h"]
        T5["analyze_churn_risks<br/>weekly"]
        T6["auto_tag_new_books<br/>every 12h"]
        T7["compute_embeddings<br/>every 6h"]
        T8["compute_trending<br/>every 3h"]
        T9["weekly_model_training<br/>weekly"]
        T10["detect_overdue<br/>every hour"]
        T11["cleanup_sessions<br/>every 15 min"]
    end

    Beat --> T1 --> Q1
    Beat --> T2 --> Q2
    Beat --> T3 --> Q3
    Beat --> T4 --> Q3
    Beat --> T5 --> Q3
    Beat --> T6 --> Q3
    Beat --> T7 --> Q3
    Beat --> T8 --> Q3
    Beat --> T9 --> Q3
    Beat --> T10 --> Q5
    Beat --> T11 --> Q5

    subgraph "Workers"
        W1["Worker 1<br/>default"]
        W2["Worker 2<br/>engagement"]
        W3["Worker 3<br/>intelligence"]
        W4["Worker 4<br/>verification"]
        W5["Worker 5<br/>maintenance"]
    end

    Q1 --> W1
    Q2 --> W2
    Q3 --> W3
    Q4 --> W4
    Q5 --> W5

    subgraph "Broker"
        Redis[("Redis DB 3")]
    end

    W1 --> Redis
    W2 --> Redis
    W3 --> Redis
    W4 --> Redis
    W5 --> Redis
```

---

## 7. Apollo Client Component Architecture

```mermaid
graph TB
    subgraph "Apollo Client"
        subgraph "Link Chain"
            ErrorLink["Error Link<br/>JWT expiry detection<br/>Token refresh + retry"]
            AuthLink["Auth Link<br/>Inject Bearer token"]
            HttpLink["HTTP Link<br/>/graphql/<br/>credentials: include"]
        end

        subgraph "Cache"
            InMemoryCache["InMemoryCache"]
            TypePolicies["Type Policies<br/>BookType, UserType,<br/>BorrowRecordType, etc."]
            CacheKeys["Cache Keys<br/>id field for all types"]
        end

        subgraph "Default Options"
            WatchQuery["watchQuery<br/>cache-and-network"]
            QueryDefault["query<br/>cache-first"]
            MutateDefault["mutate<br/>errorPolicy: all"]
        end
    end

    ErrorLink --> AuthLink --> HttpLink

    subgraph "Consumer Components"
        UseQuery["useQuery hooks"]
        UseMutation["useMutation hooks"]
        UseLazyQuery["useLazyQuery hooks"]
    end

    UseQuery --> InMemoryCache
    UseMutation --> InMemoryCache
    UseLazyQuery --> InMemoryCache
    InMemoryCache --> TypePolicies
```

---

## 8. Database Component Layout

```mermaid
graph TB
    subgraph "PostgreSQL Database"
        subgraph "Identity Tables"
            T1["identity_user"]
            T2["identity_roleconfig"]
            T3["identity_member"]
            T4["identity_verificationrequest"]
            T5["identity_refreshtoken"]
            T6["identity_passwordresettoken"]
        end

        subgraph "Catalog Tables"
            T7["catalog_book"]
            T8["catalog_author"]
            T9["catalog_category"]
            T10["catalog_bookcopy"]
            T11["catalog_bookreview"]
            T12["catalog_book_authors"]
            T13["catalog_book_categories"]
        end

        subgraph "Circulation Tables"
            T14["circulation_borrowrecord"]
            T15["circulation_reservation"]
            T16["circulation_reservationban"]
            T17["circulation_fine"]
        end

        subgraph "Digital Content Tables"
            T18["digital_content_digitalasset"]
            T19["digital_content_readingsession"]
            T20["digital_content_bookmark"]
            T21["digital_content_highlight"]
            T22["digital_content_userlibrary"]
        end

        subgraph "Engagement Tables"
            T23["engagement_userengagement"]
            T24["engagement_achievement"]
            T25["engagement_userachievement"]
            T26["engagement_dailyactivity"]
        end

        subgraph "Intelligence Tables"
            T27["intelligence_recommendation"]
            T28["intelligence_userpreference"]
            T29["intelligence_searchlog"]
            T30["intelligence_aimodelversion"]
            T31["intelligence_aiproviderconfig"]
            T32["intelligence_trendingbook"]
            T33["intelligence_bookview"]
        end

        subgraph "Governance Tables"
            T34["governance_auditlog"]
            T35["governance_securityevent"]
            T36["governance_kpledger"]
        end

        subgraph "Asset Management Tables"
            T37["asset_management_assetcategory"]
            T38["asset_management_asset"]
            T39["asset_management_maintenancelog"]
            T40["asset_management_assetdisposal"]
        end

        subgraph "HR Tables"
            T41["hr_department"]
            T42["hr_employee"]
            T43["hr_jobvacancy"]
            T44["hr_jobapplication"]
        end

        subgraph "Common Tables"
            T45["common_systemsetting"]
        end

        subgraph "Extensions"
            PGVector["pgvector<br/>Vector similarity search"]
            PGTrgm["pg_trgm<br/>Fuzzy text matching"]
            FTS["Full-text Search<br/>tsvector + ts_rank"]
        end
    end
```
