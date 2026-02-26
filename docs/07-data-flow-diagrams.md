# 07 — Data Flow Diagrams

> System-wide data flow patterns, event bus communication, and integration points

---

## 1. High-Level System Data Flow

```mermaid
flowchart TB
    subgraph "External Inputs"
        Browser["Web Browser<br/>(User Interactions)"]
        Scheduler["Celery Beat<br/>(Scheduled Triggers)"]
        LLM["Ollama LLM<br/>(AI Responses)"]
    end

    subgraph "API Layer"
        GraphQL["GraphQL API<br/>/graphql/"]
        REST["REST Upload API<br/>/api/upload/"]
        Streaming["Media Streaming<br/>/media/digital/"]
    end

    subgraph "Processing Layer"
        AuthSvc["Authentication<br/>Service"]
        CatalogSvc["Catalog<br/>Service"]
        CircSvc["Circulation<br/>Service"]
        DigitalSvc["Digital Content<br/>Service"]
        EngSvc["Engagement<br/>Service"]
        IntelSvc["Intelligence<br/>Service"]
        GovSvc["Governance<br/>Service"]
    end

    subgraph "Event System"
        EventBus["Event Bus<br/>(In-Process)"]
    end

    subgraph "Async Processing"
        CeleryQ["Celery Task Queue"]
    end

    subgraph "Data Stores"
        PG[("PostgreSQL<br/>Relational Data")]
        PGV[("pgvector<br/>Embeddings")]
        Redis[("Redis<br/>Cache")]
        FS["File System<br/>media/"]
    end

    Browser -->|"GraphQL queries/mutations"| GraphQL
    Browser -->|"File uploads"| REST
    Browser -->|"Stream requests"| Streaming
    Scheduler -->|"Periodic tasks"| CeleryQ

    GraphQL --> AuthSvc
    GraphQL --> CatalogSvc
    GraphQL --> CircSvc
    GraphQL --> DigitalSvc
    GraphQL --> EngSvc
    GraphQL --> IntelSvc
    GraphQL --> GovSvc

    AuthSvc --> PG
    AuthSvc --> Redis
    CatalogSvc --> PG
    CircSvc --> PG
    DigitalSvc --> PG
    DigitalSvc --> FS
    EngSvc --> PG
    IntelSvc --> PG
    IntelSvc --> PGV
    IntelSvc --> LLM
    GovSvc --> PG

    CircSvc -->|"events"| EventBus
    EventBus -->|"KP awards"| EngSvc
    EventBus -->|"audit log"| GovSvc
    EventBus -->|"notifications"| IntelSvc

    IntelSvc -->|"async tasks"| CeleryQ
    CeleryQ --> PG
    CeleryQ --> PGV
    CeleryQ --> Redis

    REST --> FS
    Streaming --> FS
```

---

## 2. Authentication Data Flow

```mermaid
flowchart LR
    subgraph "Client"
        LoginForm["Login Form"]
        TokenStore["localStorage<br/>accessToken<br/>refreshToken"]
        AuthLink["Apollo Auth Link<br/>Authorization header"]
    end

    subgraph "Server"
        JWT["JWT Middleware<br/>Token Validation"]
        LoginResolver["login Mutation"]
        RefreshResolver["refreshToken Mutation"]
        UserContext["Request User Context"]
    end

    subgraph "Storage"
        UserTable[("User Table")]
        RefreshTable[("RefreshToken Table")]
        RedisSession[("Redis Sessions")]
    end

    LoginForm -->|"email + password"| LoginResolver
    LoginResolver -->|"verify"| UserTable
    LoginResolver -->|"store hash"| RefreshTable
    LoginResolver -->|"tokens"| TokenStore

    TokenStore -->|"Bearer token"| AuthLink
    AuthLink -->|"Authorization header"| JWT
    JWT -->|"decode HS256"| UserContext
    UserContext -->|"user object"| LoginResolver

    TokenStore -->|"refresh token"| RefreshResolver
    RefreshResolver -->|"validate"| RefreshTable
    RefreshResolver -->|"new tokens"| TokenStore
```

---

## 3. Book Lifecycle Data Flow

```mermaid
flowchart TB
    subgraph "Creation"
        Admin["Admin creates book"]
        CreateBook["createBook mutation"]
        BookTable[("Book table")]
        AuthorTable[("Author table")]
        CategoryTable[("Category table")]
        CopyTable[("BookCopy table")]
    end

    subgraph "Enrichment"
        EmbeddingTask["compute_embeddings task"]
        AutoTag["auto_tag_new_books task"]
        SentenceT["Sentence Transformers"]
        PGVector[("pgvector embeddings")]
    end

    subgraph "Discovery"
        Search["Hybrid Search"]
        Recommend["Recommendation Engine"]
        Trending["Trending Computation"]
        AISearch["AI Search (LLM)"]
    end

    subgraph "Circulation"
        Reserve["Reserve Book"]
        Borrow["Borrow Record"]
        Return["Return Book"]
        Fine["Fine Generation"]
    end

    subgraph "Digital"
        DigitalAsset["Digital Asset"]
        ReadSession["Reading Session"]
    end

    subgraph "Analytics"
        BookView["BookView tracking"]
        SearchLog["SearchLog tracking"]
        TrendScore["TrendingBook score"]
    end

    Admin --> CreateBook
    CreateBook --> BookTable
    CreateBook --> AuthorTable
    CreateBook --> CategoryTable
    CreateBook --> CopyTable

    BookTable -->|"new book signal"| EmbeddingTask
    EmbeddingTask --> SentenceT
    SentenceT --> PGVector
    BookTable --> AutoTag

    PGVector --> Search
    PGVector --> Recommend
    BookTable --> Trending
    Search --> AISearch

    BookTable --> Reserve
    Reserve --> Borrow
    Borrow --> Return
    Return --> Fine

    BookTable --> DigitalAsset
    DigitalAsset --> ReadSession

    BookTable --> BookView
    Search --> SearchLog
    Trending --> TrendScore
```

---

## 4. Event Bus Communication Flow

```mermaid
flowchart TB
    subgraph "Event Publishers"
        Circ["Circulation Service"]
        Digital["Digital Content Service"]
        Identity["Identity Service"]
        Catalog["Catalog Service"]
    end

    subgraph "Event Bus"
        EB["EventBus<br/>(In-Process Publisher/Subscriber)"]
    end

    subgraph "Event Types"
        E1["BOOK_BORROWED"]
        E2["BOOK_RETURNED"]
        E3["BOOK_RESERVED"]
        E4["BORROW_OVERDUE"]
        E5["REVIEW_SUBMITTED"]
        E6["READING_SESSION_ENDED"]
        E7["USER_REGISTERED"]
        E8["VERIFICATION_COMPLETED"]
    end

    subgraph "Event Handlers"
        H1["Engagement Handler<br/>Award KP<br/>Check achievements<br/>Update streaks"]
        H2["Governance Handler<br/>Record audit log<br/>Track KP ledger"]
        H3["Notification Handler<br/>Create notifications<br/>Queue delivery"]
        H4["Intelligence Handler<br/>Update recommendations<br/>Recompute trends"]
    end

    Circ -->|"publish"| E1 --> EB
    Circ -->|"publish"| E2 --> EB
    Circ -->|"publish"| E3 --> EB
    Circ -->|"publish"| E4 --> EB
    Catalog -->|"publish"| E5 --> EB
    Digital -->|"publish"| E6 --> EB
    Identity -->|"publish"| E7 --> EB
    Identity -->|"publish"| E8 --> EB

    EB -->|"subscribe"| H1
    EB -->|"subscribe"| H2
    EB -->|"subscribe"| H3
    EB -->|"subscribe"| H4
```

---

## 5. Knowledge Points (KP) Data Flow

```mermaid
flowchart TB
    subgraph "KP Sources"
        Borrow["Book Borrow<br/>+10 KP"]
        Return["Book Return<br/>+5 KP"]
        Review["Review Submit<br/>+15 KP"]
        Streak["Daily Streak Bonus<br/>+5-50 KP"]
        Achievement["Achievement Unlock<br/>varies"]
        DailyLogin["Daily Login<br/>+2 KP"]
        AdminAward["Admin Manual Award<br/>varies"]
    end

    subgraph "Processing"
        EngService["Engagement Service"]
        CalcLevel["Level Calculator<br/>total_kp -> level"]
        CalcTier["Tier Calculator<br/>BRONZE -> DIAMOND"]
        StreakCheck["Streak Checker<br/>Consecutive days"]
        AchievCheck["Achievement Checker<br/>Criteria evaluation"]
    end

    subgraph "Storage"
        KPLedger[("KP Ledger<br/>Transaction log")]
        UserEng[("UserEngagement<br/>Current state")]
        DailyAct[("DailyActivity<br/>Per-day stats")]
        UserAch[("UserAchievement<br/>Unlocked badges")]
    end

    subgraph "Outputs"
        Leaderboard["Leaderboard Query"]
        RankCalc["Rank Calculation<br/>Percentile"]
        Notifications["Notifications<br/>Level up, Achievement unlocked"]
    end

    Borrow --> EngService
    Return --> EngService
    Review --> EngService
    DailyLogin --> EngService
    AdminAward --> EngService

    EngService --> KPLedger
    EngService --> UserEng
    EngService --> DailyAct
    EngService --> CalcLevel
    EngService --> CalcTier
    CalcLevel --> UserEng
    CalcTier --> UserEng

    EngService --> StreakCheck
    StreakCheck -->|"milestone"| Streak
    Streak --> EngService

    EngService --> AchievCheck
    AchievCheck -->|"unlocked"| Achievement
    Achievement --> UserAch

    UserEng --> Leaderboard
    UserEng --> RankCalc
    UserAch --> Notifications
```

---

## 6. Search Data Flow

```mermaid
flowchart LR
    subgraph "Input"
        UserQuery["User Search Query"]
        Filters["Filters<br/>category, author,<br/>language, rating, year"]
    end

    subgraph "Search Engine"
        subgraph "Parallel Search Paths"
            FT["Full-Text Search<br/>tsvector + ts_rank<br/>Weight: 0.45"]
            SM["Semantic Search<br/>pgvector cosine similarity<br/>Weight: 0.35"]
            FZ["Fuzzy Search<br/>pg_trgm trigram matching<br/>Weight: 0.20"]
        end
        Merge["Result Merger<br/>Weighted scoring<br/>Deduplication"]
        Facets["Facet Builder<br/>Categories, Authors,<br/>Languages, Ratings"]
    end

    subgraph "AI Enhancement"
        LLMSearch["LLM Search<br/>Ollama llama3.1"]
        Context["Context Builder<br/>Top N books as context"]
        Answer["Conversational Answer"]
    end

    subgraph "Logging"
        SearchLog[("SearchLog table")]
        BookView[("BookView on click")]
    end

    subgraph "Output"
        Results["Search Results<br/>Ranked list"]
        FacetData["Facet Data"]
        AIAnswer["AI Answer Panel"]
    end

    UserQuery --> FT
    UserQuery --> SM
    UserQuery --> FZ
    Filters --> FT
    Filters --> SM
    Filters --> FZ

    FT --> Merge
    SM --> Merge
    FZ --> Merge
    Merge --> Results
    Merge --> Facets
    Facets --> FacetData

    Merge --> Context
    Context --> LLMSearch
    LLMSearch --> Answer
    Answer --> AIAnswer

    UserQuery --> SearchLog
    Results --> BookView
```

---

## 7. Recommendation Data Flow

```mermaid
flowchart TB
    subgraph "Data Sources"
        BorrowHistory[("Borrow History")]
        ReadingSessions[("Reading Sessions")]
        BookReviews[("Book Reviews")]
        UserPrefs[("User Preferences")]
        BookEmbeddings[("Book Embeddings<br/>pgvector")]
        BookViews[("Book Views")]
    end

    subgraph "Recommendation Engine"
        subgraph "Strategies"
            Collab["Collaborative Filtering<br/>Similar user behavior"]
            ContentBased["Content-Based<br/>Embedding similarity"]
            Trending["Trending Strategy<br/>Popular books"]
            Popular["Popular Strategy<br/>Most borrowed"]
        end

        Hybrid["Hybrid Merger<br/>Score combination"]
        Filter["Post-Filter<br/>Remove read books<br/>Remove dismissed"]
        Rank["Final Ranking"]
    end

    subgraph "Output"
        RecTable[("Recommendation table")]
        Notification["Push Notification"]
        UserUI["Recommendations Page"]
    end

    BorrowHistory --> Collab
    BookReviews --> Collab
    UserPrefs --> ContentBased
    BookEmbeddings --> ContentBased
    BookViews --> Trending
    BorrowHistory --> Popular

    Collab --> Hybrid
    ContentBased --> Hybrid
    Trending --> Hybrid
    Popular --> Hybrid

    Hybrid --> Filter
    Filter --> Rank
    Rank --> RecTable
    RecTable --> Notification
    RecTable --> UserUI
```

---

## 8. Digital Content Streaming Data Flow

```mermaid
flowchart LR
    subgraph "Client"
        Reader["E-book Reader Page"]
        AudioPlayer["Audiobook Player Page"]
    end

    subgraph "API"
        PageView["DigitalAssetPageView<br/>/media/digital/uuid/page/N/"]
        AudioStream["AudiobookStreamView<br/>/media/digital/uuid/audio/"]
        GQL["GraphQL API<br/>Session management"]
    end

    subgraph "Processing"
        SessionMgr["Session Manager"]
        ProgressTracker["Progress Tracker"]
        BookmarkSvc["Bookmark Service"]
        HighlightSvc["Highlight Service"]
    end

    subgraph "Storage"
        MediaFiles["media/<br/>ebooks/ audiobooks/"]
        SessionTable[("ReadingSession")]
        BookmarkTable[("Bookmark")]
        HighlightTable[("Highlight")]
        LibraryTable[("UserLibrary")]
        ActivityTable[("DailyActivity")]
    end

    Reader -->|"page request"| PageView
    PageView --> MediaFiles
    AudioPlayer -->|"stream request"| AudioStream
    AudioStream --> MediaFiles

    Reader -->|"startSession"| GQL --> SessionMgr
    Reader -->|"updateProgress"| GQL --> ProgressTracker
    Reader -->|"addBookmark"| GQL --> BookmarkSvc
    Reader -->|"addHighlight"| GQL --> HighlightSvc

    SessionMgr --> SessionTable
    ProgressTracker --> SessionTable
    ProgressTracker --> LibraryTable
    ProgressTracker --> ActivityTable
    BookmarkSvc --> BookmarkTable
    HighlightSvc --> HighlightTable
```

---

## 9. Audit Trail Data Flow

```mermaid
flowchart TB
    subgraph "All Operations"
        Mutations["All Mutations<br/>(81+ mutations)"]
        Logins["Login/Logout Events"]
        Security["Security Violations"]
        Admin["Admin Operations"]
    end

    subgraph "Audit Processing"
        AuditSvc["Governance Service"]
        Logger["AuditLog Creator"]
        SecLogger["SecurityEvent Creator"]
    end

    subgraph "Audit Storage"
        AuditLog[("AuditLog<br/>actor, action, resource,<br/>changes, IP, status")]
        SecurityEvent[("SecurityEvent<br/>type, severity, IP,<br/>metadata")]
    end

    subgraph "Admin Queries"
        AuditQuery["auditLogs query<br/>(Super Admin)"]
        SecQuery["securityEvents query<br/>(Super Admin)"]
        Dashboard["Admin Dashboard"]
    end

    Mutations -->|"on success/failure"| Logger
    Logins -->|"LOGIN/LOGOUT"| Logger
    Security -->|"BRUTE_FORCE etc."| SecLogger
    Admin -->|"ADMIN_ACTION"| Logger

    Logger --> AuditLog
    SecLogger --> SecurityEvent

    AuditLog --> AuditQuery
    SecurityEvent --> SecQuery
    AuditQuery --> Dashboard
    SecQuery --> Dashboard
```
