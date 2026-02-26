# 11 — Frontend Architecture

> React 18, Apollo Client, Zustand state management, Tailwind design system, and component library

---

## 1. Frontend Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **UI Framework** | React | 18.3 |
| **Router** | React Router DOM | 6 |
| **API Client** | Apollo Client | 3.11 |
| **State Management** | Zustand | 5.0 |
| **Type System** | TypeScript | 5.7 |
| **Build Tool** | Vite | 6.0 |
| **Styling** | Tailwind CSS | 3.4 |
| **Component Library** | Headless UI + Heroicons | 2 |
| **Charting** | Chart.js + react-chartjs-2 | 4 |
| **Animation** | Framer Motion | 11 |
| **Forms** | React Hook Form + Zod | 7 + 3 |
| **Sanitization** | DOMPurify | 3 |
| **Testing** | Vitest + Testing Library | 2 + 16 |

---

## 2. Application Bootstrap

```mermaid
graph TB
    Entry["main.tsx"]
    
    subgraph "Provider Stack"
        direction TB
        StrictMode["React.StrictMode"]
        Apollo["ApolloProvider<br/>client = apolloClient"]
        Router["BrowserRouter"]
        Theme["ThemeProvider<br/>dark / light / system"]
    end

    subgraph "Root Components"
        App["App.tsx<br/>Route Configuration"]
        Toaster["Toaster<br/>react-hot-toast<br/>top-right, 4s"]
    end

    Entry --> StrictMode --> Apollo --> Router --> Theme
    Theme --> App
    Theme --> Toaster
```

---

## 3. Routing Architecture

### 3.1 Route Tree

```mermaid
graph TB
    Root["BrowserRouter"]
    
    subgraph "Auth Routes (AuthLayout)"
        Login["/login<br/>LoginPage"]
        Register["/register<br/>RegisterPage"]
        Forgot["/forgot-password<br/>ForgotPasswordPage"]
        Reset["/reset-password<br/>ForgotPasswordPage"]
    end

    subgraph "Member Routes (ProtectedRoute → AppLayout)"
        Dashboard["/dashboard<br/>DashboardPage"]
        Catalog["/catalog<br/>CatalogPage"]
        BookDetail["/catalog/:bookId<br/>BookDetailPage"]
        Search["/search<br/>SearchPage"]
        Borrows["/borrows<br/>MyBorrowsPage"]
        Reservations["/reservations<br/>MyReservationsPage"]
        Fines["/fines<br/>MyFinesPage"]
        Library["/library<br/>DigitalLibraryPage"]
        Reader["/reader/:assetId<br/>ReaderPage"]
        Audio["/listen/:assetId<br/>AudiobookPlayerPage"]
        Profile["/profile<br/>ProfilePage"]
        Achievements["/achievements<br/>AchievementsPage"]
        Leaderboard["/leaderboard<br/>LeaderboardPage"]
        KP["/kp-center<br/>KnowledgePointsPage"]
        Recs["/recommendations<br/>RecommendationsPage"]
        Notifications["/notifications<br/>NotificationsPage"]
        Insights["/insights<br/>ReadingInsightsPage"]
    end

    subgraph "Admin Routes (AdminRoute → AdminLayout)"
        ADash["/admin/dashboard<br/>AdminDashboardPage"]
        AUsers["/admin/users<br/>AdminUsersPage"]
        ABooks["/admin/books<br/>AdminBooksPage"]
        AAuthors["/admin/authors<br/>AdminAuthorsPage"]
        ADigital["/admin/digital<br/>AdminDigitalPage"]
        ACirc["/admin/circulation<br/>AdminCirculationPage"]
        AAnalytics["/admin/analytics<br/>AdminAnalyticsPage"]
        AAI["/admin/ai-config<br/>AdminAIConfigPage"]
        AAudit["/admin/audit<br/>AdminAuditPage"]
        AAssets["/admin/assets<br/>AdminAssetsPage"]
        AEmps["/admin/employees<br/>AdminEmployeesPage"]
        AJobs["/admin/jobs<br/>AdminEmployeesPage"]
        ARoles["/admin/roles<br/>AdminRolesPage"]
        AMembers["/admin/members<br/>AdminMembersPage"]
        ASettings["/admin/settings<br/>AdminSettingsPage"]
        ASMTP["/admin/smtp<br/>AdminSmtpPage"]
    end

    NotFound["* → NotFoundPage"]

    Root --> Login
    Root --> Register
    Root --> Forgot
    Root --> Reset
    Root --> Dashboard
    Root --> Catalog
    Root --> BookDetail
    Root --> Search
    Root --> Borrows
    Root --> Reservations
    Root --> Fines
    Root --> Library
    Root --> Reader
    Root --> Audio
    Root --> Profile
    Root --> Achievements
    Root --> Leaderboard
    Root --> KP
    Root --> Recs
    Root --> Notifications
    Root --> Insights
    Root --> ADash
    Root --> AUsers
    Root --> ABooks
    Root --> AAuthors
    Root --> ADigital
    Root --> ACirc
    Root --> AAnalytics
    Root --> AAI
    Root --> AAudit
    Root --> AAssets
    Root --> AEmps
    Root --> AJobs
    Root --> ARoles
    Root --> AMembers
    Root --> ASettings
    Root --> ASMTP
    Root --> NotFound
```

**All pages are lazy-loaded** via `React.lazy()` with `<Suspense fallback={<LoadingScreen />}>`.

### 3.2 Route Guards

```mermaid
graph LR
    subgraph "Guard Hierarchy"
        direction LR
        Protected["ProtectedRoute<br/>isAuthenticated check"]
        Admin["AdminRoute<br/>Admin role check"]
        Permission["PermissionGuard<br/>Module-level RBAC check"]
    end

    Protected -->|"wraps"| Admin -->|"wraps"| Permission

    subgraph "Redirects"
        ToLogin["→ /login<br/>(unauthenticated)"]
        ToDash["→ /dashboard<br/>(non-admin)"]
        Forbidden["→ 403 view<br/>(missing permission)"]
    end

    Protected --> ToLogin
    Admin --> ToDash
    Permission --> Forbidden
```

### 3.3 Complete Route Table

#### Auth Routes (Public)

| Path | Component | Layout |
|------|-----------|--------|
| `/login` | `LoginPage` | `AuthLayout` |
| `/register` | `RegisterPage` | `AuthLayout` |
| `/forgot-password` | `ForgotPasswordPage` | `AuthLayout` |
| `/reset-password` | `ForgotPasswordPage` | `AuthLayout` |

#### Member Routes (Protected)

| Path | Component | Category |
|------|-----------|----------|
| `/` | Redirect → `/dashboard` | — |
| `/dashboard` | `DashboardPage` | Dashboard |
| `/catalog` | `CatalogPage` | Catalog |
| `/catalog/:bookId` | `BookDetailPage` | Catalog |
| `/search` | `SearchPage` | Search |
| `/borrows` | `MyBorrowsPage` | Circulation |
| `/reservations` | `MyReservationsPage` | Circulation |
| `/fines` | `MyFinesPage` | Circulation |
| `/library` | `DigitalLibraryPage` | Digital |
| `/reader/:assetId` | `ReaderPage` | Digital |
| `/listen/:assetId` | `AudiobookPlayerPage` | Digital |
| `/profile` | `ProfilePage` | Profile |
| `/achievements` | `AchievementsPage` | Engagement |
| `/leaderboard` | `LeaderboardPage` | Engagement |
| `/kp-center` | `KnowledgePointsPage` | Engagement |
| `/recommendations` | `RecommendationsPage` | Intelligence |
| `/notifications` | `NotificationsPage` | Intelligence |
| `/insights` | `ReadingInsightsPage` | Intelligence |

#### Admin Routes (Protected + RBAC)

| Path | Component | Permission Module |
|------|-----------|-------------------|
| `/admin` | Redirect → `/admin/dashboard` | — |
| `/admin/dashboard` | `AdminDashboardPage` | (none) |
| `/admin/users` | `AdminUsersPage` | `users` |
| `/admin/books` | `AdminBooksPage` | `books` |
| `/admin/authors` | `AdminAuthorsPage` | `authors` |
| `/admin/digital` | `AdminDigitalPage` | `digital_content` |
| `/admin/circulation` | `AdminCirculationPage` | `circulation` |
| `/admin/analytics` | `AdminAnalyticsPage` | `analytics` |
| `/admin/ai-config` | `AdminAIConfigPage` | `ai` |
| `/admin/audit` | `AdminAuditPage` | `audit` |
| `/admin/assets` | `AdminAssetsPage` | `assets` |
| `/admin/employees` | `AdminEmployeesPage` | `employees` |
| `/admin/jobs` | `AdminEmployeesPage` | `employees` |
| `/admin/roles` | `AdminRolesPage` | `roles` |
| `/admin/members` | `AdminMembersPage` | `members` |
| `/admin/settings` | `AdminSettingsPage` | `settings` |
| `/admin/smtp` | `AdminSmtpPage` | `settings` |

---

## 4. State Management

### 4.1 Store Architecture

```mermaid
graph TB
    subgraph "Zustand Stores"
        Auth["useAuthStore<br/>Authentication state"]
        UI["useUIStore<br/>UI state"]
    end

    subgraph "Apollo Cache"
        InMemory["InMemoryCache<br/>GraphQL data cache"]
    end

    subgraph "Persistence"
        LS["localStorage<br/>Manual persistence"]
    end

    Auth --> LS
    UI --> LS
    InMemory --> Auth
```

### 4.2 Auth Store

```mermaid
classDiagram
    class useAuthStore {
        +String accessToken
        +String refreshToken
        +AuthUser user
        +Boolean isAuthenticated
        +Boolean isLoading
        +setAuth(user, accessToken, refreshToken) void
        +setUser(user) void
        +logout() void
        +refreshTokens() Promise~boolean~
        +hydrate() void
    }

    class AuthUser {
        +String id
        +String email
        +String firstName
        +String lastName
        +UserRole role
        +Boolean isVerified
        +String avatarUrl
    }

    useAuthStore --> AuthUser
```

**Persistence keys:**
- `nova_access_token` — JWT access token
- `nova_refresh_token` — JWT refresh token
- `nova_user` — Serialized user object

**Auto-hydration:** `useAuthStore.getState().hydrate()` called on module load.

### 4.3 UI Store

```mermaid
classDiagram
    class useUIStore {
        +Boolean sidebarOpen
        +Boolean sidebarCollapsed
        +Boolean commandPaletteOpen
        +Boolean searchOverlayOpen
        +toggleSidebar() void
        +setSidebarOpen(open) void
        +setSidebarCollapsed(collapsed) void
        +toggleSidebarCollapsed() void
        +toggleCommandPalette() void
        +setSearchOverlayOpen(open) void
        +toggleSearchOverlay() void
    }
```

**Persistence:** Only `sidebarCollapsed` → `localStorage` key `nova-sidebar-collapsed`.

---

## 5. Apollo Client Architecture

### 5.1 Link Chain

```mermaid
graph LR
    Request["GraphQL Request"]
    ErrorLink["Error Link<br/>JWT expiry detection<br/>Auto-refresh + retry"]
    AuthLink["Auth Link<br/>Inject Authorization<br/>Bearer header"]
    HttpLink["HTTP Link<br/>credentials: include<br/>/graphql/"]
    Server["Django Backend"]

    Request --> ErrorLink --> AuthLink --> HttpLink --> Server
```

### 5.2 Token Refresh Flow

```mermaid
sequenceDiagram
    participant App as React App
    participant ErrorLink as Error Link
    participant AuthStore as Auth Store
    participant Server as Backend

    App->>Server: GraphQL Request
    Server-->>ErrorLink: 401 "Signature has expired"
    ErrorLink->>AuthStore: refreshTokens()
    AuthStore->>Server: REFRESH_TOKEN mutation
    
    alt Refresh Success
        Server-->>AuthStore: New access + refresh tokens
        AuthStore->>AuthStore: Update tokens in store + localStorage
        ErrorLink->>Server: Retry original request (new token)
        Server-->>App: Success response
    else Refresh Failure
        Server-->>AuthStore: Error
        AuthStore->>AuthStore: logout() — clear all state
        App->>App: Redirect to /login
    end
```

### 5.3 Cache Configuration

| Type | Key Field | Merge Strategy |
|------|-----------|----------------|
| `BookType` | `id` | Normalize by ID |
| `UserType` | `id` | Normalize by ID |
| `BorrowRecordType` | `id` | Normalize by ID |
| `RecommendationType` | `id` | Normalize by ID |
| `Query.books` | `[query, categoryId, authorId, language]` | Flat pagination |
| `Query.users` | `[role, isActive, search]` | Flat pagination |
| `Query.allBorrows` | `[status, userId]` | Flat pagination |
| `Query.auditLogs` | `[action, resourceType, actorId]` | Flat pagination |

**Default fetch policies:**
- `watchQuery`: `cache-and-network`
- `query`: `cache-first`
- `mutate`: errorPolicy `all`

---

## 6. Component Architecture

### 6.1 Component Tree

```mermaid
graph TB
    subgraph "Layouts"
        AuthLayout["AuthLayout<br/>Login/Register wrapper"]
        AppLayout["AppLayout<br/>Header + Sidebar + Content"]
        AdminLayout["AdminLayout<br/>Admin panel wrapper"]
    end

    subgraph "Navigation"
        Header["Header<br/>Top bar, user menu"]
        Sidebar["Sidebar<br/>Collapsible nav"]
        MobileSidebar["MobileSidebar<br/>Responsive drawer"]
        Breadcrumbs["Breadcrumbs"]
    end

    subgraph "Auth Guards"
        ProtectedRoute["ProtectedRoute"]
        AdminRoute["AdminRoute"]
        PermissionGuard["PermissionGuard"]
    end

    subgraph "UI Design System (20+ components)"
        Avatar["Avatar"]
        Badge["Badge"]
        Button["Button"]
        Card["Card, CardHeader, CardFooter"]
        ConfirmDialog["ConfirmDialog"]
        DataTable["DataTable"]
        Dropdown["Dropdown"]
        EmptyState["EmptyState"]
        Input["Input"]
        Modal["Modal"]
        Pagination["Pagination"]
        ProgressBar["ProgressBar"]
        SafeHtml["SafeHtml"]
        SearchInput["SearchInput"]
        Select["Select"]
        Spinner["Spinner, LoadingScreen"]
        StarRating["StarRating"]
        Tabs["Tabs"]
        Textarea["Textarea"]
        Tooltip["Tooltip"]
    end

    AppLayout --> Header
    AppLayout --> Sidebar
    AppLayout --> MobileSidebar
    AppLayout --> Breadcrumbs
```

### 6.2 Design System Components

| Component | Props | Description |
|-----------|-------|-------------|
| `Avatar` | `src?, initials?, size` | User avatar with fallback initials |
| `Badge` | `variant, children` | Status/label badge |
| `Button` | `variant, size, loading, disabled` | Primary action button |
| `Card` | `children, className` | Content card container |
| `ConfirmDialog` | `open, title, message, onConfirm, onCancel` | Confirmation modal |
| `DataTable` | `columns, data, loading, onSort` | Sortable data table |
| `Dropdown` | `items, trigger` | Dropdown menu |
| `EmptyState` | `icon, title, description, action` | Empty content placeholder |
| `Input` | `label, error, type, ...inputProps` | Form text input |
| `Modal` | `open, onClose, title, size` | Dialog overlay |
| `Pagination` | `page, totalPages, onPageChange` | Page navigation |
| `ProgressBar` | `value, max, color` | Progress indicator |
| `SafeHtml` | `html` | DOMPurify-sanitized HTML renderer |
| `SearchInput` | `value, onChange, placeholder` | Search field with icon |
| `Select` | `options, value, onChange, label` | Dropdown select |
| `Spinner` | `size` | Loading spinner |
| `StarRating` | `rating, onChange?, readonly?` | Star rating display/input |
| `Tabs` | `tabs, activeTab, onChange` | Tab navigation |
| `Textarea` | `label, error, ...props` | Multi-line text input |
| `Tooltip` | `content, children` | Hover tooltip |

---

## 7. GraphQL Operations

### 7.1 Query Files

```mermaid
graph TB
    subgraph "Query Modules (13 files)"
        QAuth["auth.ts<br/>ME"]
        QCatalog["catalog.ts<br/>GET_BOOKS, GET_BOOK,<br/>GET_AUTHORS, GET_CATEGORIES,<br/>GET_BOOK_COPIES"]
        QCirc["circulation.ts<br/>MY_BORROWS, MY_RESERVATIONS,<br/>MY_FINES, ALL_BORROWS,<br/>OVERDUE_BORROWS, ALL_FINES"]
        QAdmin["admin.ts<br/>GET_USERS, GET_USER,<br/>USER_BORROWS, USER_FINES"]
        QDigital["digital.ts<br/>GET_DIGITAL_ASSET,<br/>MY_LIBRARY, MY_SESSIONS"]
        QEngage["engagement.ts<br/>MY_ENGAGEMENT,<br/>MY_ACHIEVEMENTS, LEADERBOARD"]
        QIntel["intelligence.ts<br/>MY_RECOMMENDATIONS,<br/>SEARCH_BOOKS, AI_SEARCH,<br/>LLM_ANALYTICS"]
        QAssets["assets.ts<br/>GET_ASSETS, GET_ASSET_STATS"]
        QHR["hr.ts<br/>GET_DEPARTMENTS,<br/>GET_EMPLOYEES"]
        QGov["governance.ts<br/>AUDIT_LOGS,<br/>SECURITY_EVENTS"]
        QRoles["roles.ts<br/>GET_ROLE_CONFIGS,<br/>MY_PERMISSIONS"]
        QSettings["settings.ts<br/>GET_SYSTEM_SETTINGS"]
        QMembers["members.ts<br/>GET_MEMBERS, GET_MEMBER"]
    end
```

### 7.2 Mutation Files

```mermaid
graph TB
    subgraph "Mutation Modules (12 files)"
        MAuth["auth.ts<br/>LOGIN, REGISTER, LOGOUT,<br/>CHANGE_PASSWORD,<br/>PASSWORD_RESET flow"]
        MCatalog["catalog.ts<br/>CREATE_BOOK, UPDATE_BOOK,<br/>CREATE_AUTHOR, DELETE_BOOK"]
        MCirc["circulation.ts<br/>RESERVE_BOOK, RETURN_BOOK,<br/>RENEW_BORROW, PAY_FINE"]
        MAdmin["admin.ts<br/>ACTIVATE_USER,<br/>CHANGE_USER_ROLE"]
        MDigital["digital.ts<br/>START_READING_SESSION,<br/>ADD_BOOKMARK, ADD_HIGHLIGHT"]
        MIntel["intelligence.ts<br/>GENERATE_RECOMMENDATIONS,<br/>TRIGGER_MODEL_TRAINING"]
        MAssets["assets.ts<br/>CREATE_ASSET,<br/>LOG_MAINTENANCE"]
        MHR["hr.ts<br/>CREATE_EMPLOYEE,<br/>CREATE_JOB_VACANCY"]
        MRoles["roles.ts<br/>CREATE_ROLE_CONFIG,<br/>UPDATE_ROLE_CONFIG"]
        MSettings["settings.ts<br/>UPDATE_SYSTEM_SETTING,<br/>SEND_TEST_EMAIL"]
        MMembers["members.ts<br/>CREATE_MEMBER,<br/>UPDATE_MEMBER"]
    end
```

### 7.3 Operation Count by Module

| Module | Queries | Mutations |
|--------|---------|-----------|
| Auth | 1 | 11 |
| Catalog | 8 | 9 |
| Circulation | 8 | 8 |
| Admin | 7 | 6 |
| Digital | 8 | 9 |
| Engagement | 6 | 0 |
| Intelligence | 22 | 17 |
| Assets | 5 | 6 |
| HR | 6 | 7 |
| Governance | 4 | 0 |
| Roles | 4 | 3 |
| Settings | 1 | 3 |
| Members | 3 | 3 |
| **Total** | **83** | **82** |

---

## 8. Custom Hooks

### 8.1 Hook Inventory

```mermaid
classDiagram
    class useDebounce~T~ {
        +T value
        +number delay = 300
        returns T debouncedValue
    }

    class useDocumentTitle {
        +String title
        sets document.title
        restores on unmount
    }

    class useInfiniteScroll {
        +Boolean hasMore
        +Boolean loading
        +Function onLoadMore
        +number threshold = 100
        returns RefObject sentinelRef
    }

    class useKeyboardShortcut {
        +String key
        +Object modifiers
        +Function handler
        +Boolean enabled
        registers global listener
    }

    class useLocalStorage~T~ {
        +String key
        +T initialValue
        returns T value
        returns Function setter
    }

    class useAutoLogout {
        +number timeoutMs = 1800000
        monitors mousemove keydown touch scroll
        calls logout after 30min
    }

    class usePermissions {
        returns Object permissions
        returns Function can
        returns Function canRead
        returns Function canCreate
        returns Function canUpdate
        returns Function canDelete
    }
```

### 8.2 Permission System

```mermaid
graph TB
    subgraph "Permission Modules (13)"
        Books["books"]
        Authors["authors"]
        Digital["digital_content"]
        Users["users"]
        Employees["employees"]
        Circulation["circulation"]
        Assets["assets"]
        Analytics["analytics"]
        AI["ai"]
        Audit["audit"]
        Settings["settings"]
        Roles["roles"]
        Members["members"]
    end

    subgraph "Actions"
        Create["create"]
        Read["read"]
        Update["update"]
        Delete["delete"]
    end

    subgraph "Hook API"
        Can["can(module, action)"]
        CanRead["canRead(module)"]
        CanCreate["canCreate(module)"]
        CanUpdate["canUpdate(module)"]
        CanDelete["canDelete(module)"]
    end

    Books --> Can
    Create --> Can
    Can --> CanRead
    Can --> CanCreate
    Can --> CanUpdate
    Can --> CanDelete
```

---

## 9. Theme System

### 9.1 Theme Architecture

```mermaid
graph TB
    subgraph "Theme Provider (React Context)"
        ThemeContext["ThemeContext<br/>theme: light | dark | system"]
        SetTheme["setTheme() action"]
    end

    subgraph "Storage"
        LocalStorage["localStorage<br/>key: nova-theme"]
        MediaQuery["prefers-color-scheme<br/>system listener"]
    end

    subgraph "Application"
        HTMLClass["document.documentElement<br/>classList: .light | .dark"]
        CSSVars["CSS Custom Properties<br/>--nova-bg, --nova-surface,<br/>--nova-border, --nova-text"]
        TailwindDark["Tailwind dark: prefix<br/>class strategy"]
    end

    ThemeContext --> LocalStorage
    ThemeContext --> HTMLClass
    MediaQuery --> ThemeContext
    HTMLClass --> CSSVars
    HTMLClass --> TailwindDark
```

### 9.2 Design Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--nova-bg` | `#f8fafc` | `#0f172a` | Page background |
| `--nova-surface` | `#ffffff` | `#1e293b` | Card/panel background |
| `--nova-surface-hover` | `#f1f5f9` | `#334155` | Hover states |
| `--nova-border` | `#e2e8f0` | `#334155` | Borders |
| `--nova-text` | `#0f172a` | `#f1f5f9` | Primary text |
| `--nova-text-secondary` | `#475569` | `#94a3b8` | Secondary text |
| `--nova-text-muted` | `#94a3b8` | `#64748b` | Muted text |

### 9.3 Custom Color Scales

| Scale | Purpose | Range |
|-------|---------|-------|
| `primary` | Blue brand color | 50–950 |
| `accent` | Purple accent color | 50–950 |
| `nova` | Semantic CSS variable tokens | bg, surface, border, text |
| `kp` | Knowledge Points badges | bronze, silver, gold, platinum, diamond |

---

## 10. Build Configuration

### 10.1 Vite Configuration

```mermaid
graph TB
    subgraph "Vite Dev Server"
        Port["Port 3000"]
        Proxy1["/graphql → localhost:8000"]
        Proxy2["/api → localhost:8000"]
        Proxy3["/media → localhost:8000"]
    end

    subgraph "Build Optimization"
        Target["Target: ES2022"]
        Sourcemaps["Sourcemaps: enabled"]
    end

    subgraph "Manual Chunks"
        Vendor["vendor<br/>react, react-dom,<br/>react-router-dom"]
        ApolloChunk["apollo<br/>@apollo/client, graphql"]
        Charts["charts<br/>chart.js, react-chartjs-2"]
        UIChunk["ui<br/>framer-motion,<br/>@headlessui/react,<br/>@heroicons/react"]
    end

    subgraph "Plugins"
        ReactPlugin["@vitejs/plugin-react"]
    end

    subgraph "Resolve"
        Alias["@ → ./src"]
    end
```

### 10.2 TypeScript Configuration

| Setting | Value |
|---------|-------|
| `target` | ES2022 |
| `module` | ESNext |
| `jsx` | react-jsx |
| `strict` | true |
| `paths.@/*` | `./src/*` |

---

## 11. Page Architecture

### 11.1 Page Categories

```mermaid
graph TB
    subgraph "Public Pages (4)"
        P1["LoginPage"]
        P2["RegisterPage"]
        P3["ForgotPasswordPage"]
        P4["ResetPasswordPage"]
    end

    subgraph "Member Pages (18)"
        M1["DashboardPage"]
        M2["CatalogPage"]
        M3["BookDetailPage"]
        M4["SearchPage"]
        M5["MyBorrowsPage"]
        M6["MyReservationsPage"]
        M7["MyFinesPage"]
        M8["DigitalLibraryPage"]
        M9["ReaderPage"]
        M10["AudiobookPlayerPage"]
        M11["ProfilePage"]
        M12["AchievementsPage"]
        M13["LeaderboardPage"]
        M14["KnowledgePointsPage"]
        M15["RecommendationsPage"]
        M16["NotificationsPage"]
        M17["ReadingInsightsPage"]
        M18["NotFoundPage"]
    end

    subgraph "Admin Pages (16)"
        A1["AdminDashboardPage"]
        A2["AdminUsersPage"]
        A3["AdminBooksPage"]
        A4["AdminAuthorsPage"]
        A5["AdminDigitalPage"]
        A6["AdminCirculationPage"]
        A7["AdminAnalyticsPage"]
        A8["AdminAIConfigPage"]
        A9["AdminAuditPage"]
        A10["AdminAssetsPage"]
        A11["AdminEmployeesPage"]
        A12["AdminRolesPage"]
        A13["AdminMembersPage"]
        A14["AdminSettingsPage"]
        A15["AdminSmtpPage"]
        A16["AdminAIModelsPage"]
    end
```

### 11.2 Total: 38 Pages

| Category | Count |
|----------|-------|
| Auth (public) | 4 |
| Member (protected) | 18 |
| Admin (RBAC) | 16 |
| **Total** | **38** |

---

## 12. Security (Client-Side)

### 12.1 XSS Prevention

```mermaid
graph LR
    UGC["User-Generated Content"]
    DOMPurify["DOMPurify<br/>Whitelist: b, i, em, strong,<br/>p, br, h1-h6, a, ul, ol, li,<br/>code, pre, table, etc."]
    SafeHtml["SafeHtml Component<br/>dangerouslySetInnerHTML"]
    StripHtml["stripHtml()<br/>Remove ALL tags"]

    UGC --> DOMPurify --> SafeHtml
    UGC --> StripHtml
```

### 12.2 Auto-Logout

| Setting | Value |
|---------|-------|
| Timeout | 30 minutes (1,800,000 ms) |
| Monitored events | `mousemove`, `keydown`, `touchstart`, `scroll` |
| Action | Clear tokens + redirect to `/login` |

### 12.3 Token Security

| Measure | Implementation |
|---------|---------------|
| Storage | `localStorage` (manual management) |
| Header injection | Apollo `authLink` — `Authorization: Bearer <token>` |
| Auto-refresh | `errorLink` detects expired token → `refreshTokens()` |
| Credential passing | `credentials: 'include'` on HTTP link |

---

## 13. Utility Library

### 13.1 Core Utilities (`lib/utils.ts`)

| Function | Description |
|----------|-------------|
| `cn(...inputs)` | Tailwind class merging (clsx + tailwind-merge) |
| `formatDate(date)` | Format to "MMM d, yyyy" |
| `timeAgo(date)` | Relative time (e.g., "2 hours ago") |
| `formatDateTime(date)` | Format to "MMM d, yyyy HH:mm" |
| `truncate(text, max)` | Truncate with ellipsis |
| `capitalize(str)` | First letter uppercase |
| `formatNumber(n)` | Number with comma separators |
| `formatCurrency(amount, currency?)` | Currency formatting |
| `debounce(fn, ms)` | Debounce function wrapper |
| `getInitials(first?, last?)` | Name initials extraction |
| `kpLevelName(level)` | Level → Bronze/Silver/Gold/Platinum/Diamond |
| `kpLevelClass(level)` | Level → CSS class mapping |
| `riskColor(risk)` | Risk level → Tailwind text color |
| `sleep(ms)` | Async sleep utility |
| `extractGqlError(error)` | Extract readable GraphQL error message |

### 13.2 Constants (`lib/constants.ts`)

| Constant | Value |
|----------|-------|
| `APP_NAME` | `VITE_APP_NAME` or `'Nova Library'` |
| `ROLES` | 6 roles: SUPER_ADMIN, LIBRARIAN, LIBRARY_ASSISTANT, MEMBER, STUDENT, GUEST |
| `ADMIN_ROLES` | SUPER_ADMIN, LIBRARIAN, LIBRARY_ASSISTANT |
| `STAFF_ROLES` | SUPER_ADMIN, LIBRARIAN |
| `BORROW_STATUS` | ACTIVE, RETURNED, OVERDUE, LOST |
| `RESERVATION_STATUS` | PENDING, READY, FULFILLED, CANCELLED, EXPIRED |
| `FINE_STATUS` | PENDING, PAID, WAIVED, OVERDUE |
| `NOTIFICATION_TYPES` | 9 types |
| `TRENDING_PERIODS` | DAILY, WEEKLY, MONTHLY, ALL_TIME |
| `BOOK_LANGUAGES` | 10 languages |
| `ITEMS_PER_PAGE` | 20 |
| `MAX_SEARCH_SUGGESTIONS` | 8 |

---

## 14. Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | 18.3 | UI framework |
| `react-dom` | 18.3 | DOM rendering |
| `react-router-dom` | 6 | Client-side routing |
| `@apollo/client` | 3.11 | GraphQL client |
| `graphql` | — | GraphQL language support |
| `zustand` | 5.0 | State management |
| `chart.js` | 4 | Charting library |
| `react-chartjs-2` | — | React Chart.js wrapper |
| `framer-motion` | 11 | Animations |
| `@headlessui/react` | 2 | Accessible UI primitives |
| `@heroicons/react` | 2 | Icon library |
| `react-hook-form` | 7 | Form management |
| `zod` | 3 | Schema validation |
| `dompurify` | 3 | HTML sanitization |
| `date-fns` | 4 | Date utilities |
| `react-hot-toast` | 2 | Toast notifications |
| `clsx` | — | Class name utility |
| `tailwind-merge` | — | Tailwind class merge |

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `typescript` | 5.7 | Type system |
| `vite` | 6 | Build tool |
| `vitest` | 2 | Test runner |
| `@testing-library/react` | 16 | Component testing |
| `@testing-library/jest-dom` | 6 | DOM assertions |
| `eslint` | 9 | Linting |
| `prettier` | 3 | Code formatting |
| `tailwindcss` | 3.4 | Utility CSS |
| `postcss` | — | CSS processing |
| `@graphql-codegen` | 5 | GraphQL type generation |
