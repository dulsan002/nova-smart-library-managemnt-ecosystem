# 09 — Security Architecture

> Authentication, authorization, RBAC, middleware pipeline, security headers, rate limiting, and threat mitigation

---

## 1. Security Architecture Overview

```mermaid
graph TB
    subgraph "Client Security"
        DOMPurify["DOMPurify<br/>XSS Prevention"]
        SafeHtml["SafeHtml Component<br/>HTML Sanitization"]
        TokenStorage["Token Storage<br/>localStorage"]
        AutoLogout["Auto-Logout<br/>30 min inactivity"]
    end

    subgraph "Transport Security"
        HTTPS["HTTPS / TLS<br/>(Production)"]
        CORS["CORS Headers<br/>django-cors-headers"]
        CSRF["CSRF Exemption<br/>(JWT-based auth)"]
    end

    subgraph "API Security Layer"
        RateLimit["Rate Limiting<br/>Token Bucket per IP/User"]
        QuerySecurity["GraphQL Security<br/>Depth, Complexity, Size"]
        SecurityHeaders["Security Headers<br/>CSP, XSS, COOP, CORP"]
        ExceptionHandler["Exception Handler<br/>No stack trace leaking"]
    end

    subgraph "Authentication"
        JWT["JWT Authentication<br/>HS256, 15 min access"]
        Argon2["Argon2 Password Hashing"]
        AccountLock["Account Lockout<br/>5 attempts, exponential backoff"]
        RefreshTokens["Refresh Tokens<br/>7 day lifetime, hashed storage"]
    end

    subgraph "Authorization"
        RBAC["Role-Based Access Control"]
        PermissionGuard["Permission Guards<br/>Module-level actions"]
        OwnershipCheck["Ownership Checks<br/>User can only access own data"]
    end

    subgraph "Audit & Monitoring"
        AuditLog["Audit Logging<br/>All mutations tracked"]
        SecurityEvents["Security Events<br/>Brute force, suspicious access"]
        RequestLog["Request Logging<br/>Every request with timing"]
    end

    DOMPurify --> HTTPS
    TokenStorage --> HTTPS
    HTTPS --> CORS
    CORS --> RateLimit
    RateLimit --> SecurityHeaders
    SecurityHeaders --> QuerySecurity
    QuerySecurity --> JWT
    JWT --> RBAC
    RBAC --> PermissionGuard
    RBAC --> OwnershipCheck
    PermissionGuard --> AuditLog
    AuditLog --> SecurityEvents
```

---

## 2. Authentication Flow

### 2.1 JWT Token Architecture

```mermaid
graph LR
    subgraph "Token Lifecycle"
        Login["Login<br/>(email + password)"] -->|"generates"| AT["Access Token<br/>15 min TTL<br/>HS256"]
        Login -->|"generates"| RT["Refresh Token<br/>7 day TTL<br/>SHA256 hashed in DB"]
        AT -->|"expired"| Refresh["Refresh Flow"]
        Refresh -->|"new tokens"| AT2["New Access Token"]
        Refresh -->|"new tokens"| RT2["New Refresh Token"]
        RT -->|"revoked on refresh"| Revoked["Old Token Revoked"]
    end

    subgraph "Storage"
        AT -->|"stored in"| LS["localStorage<br/>nova_access_token"]
        RT -->|"stored in"| LS2["localStorage<br/>nova_refresh_token"]
        RT -->|"hash stored in"| DB[("RefreshToken table")]
    end

    subgraph "Usage"
        LS -->|"injected by"| AuthLink["Apollo Auth Link<br/>Authorization: Bearer ..."]
    end
```

### 2.2 Password Security

| Feature | Implementation |
|---------|---------------|
| **Hashing Algorithm** | Argon2 (primary), PBKDF2 (fallback) |
| **Minimum Length** | 10 characters |
| **Django Validators** | `UserAttributeSimilarityValidator`, `MinimumLengthValidator`, `CommonPasswordValidator`, `NumericPasswordValidator` |
| **Failed Login Tracking** | `failed_login_attempts` counter on User model |
| **Account Lockout** | After 5 failures, exponential backoff (`locked_until`) |
| **Password Reset** | 3-step OTP flow (request → verify → confirm) |
| **OTP Security** | SHA256 hashed, 5 attempt limit, time-limited expiry |

### 2.3 Account Lockout Mechanism

```mermaid
stateDiagram-v2
    [*] --> Active
    Active --> Attempt1 : Failed login
    Attempt1 --> Attempt2 : Failed login
    Attempt2 --> Attempt3 : Failed login
    Attempt3 --> Attempt4 : Failed login
    Attempt4 --> Locked : 5th failed login
    Locked --> Active : Lock expires (exponential backoff)
    Active --> Active : Successful login (reset counter)

    note right of Locked
        SecurityEvent created
        Exponential backoff applied
        locked_until calculated
    end note
```

---

## 3. Authorization — RBAC System

### 3.1 Role Hierarchy

```mermaid
graph TB
    SA["SUPER_ADMIN<br/>Full system access"]
    A["ADMIN<br/>User management + all modules"]
    L["LIBRARIAN<br/>Catalog + Circulation + Content"]
    M["MEMBER<br/>Browse + Borrow + Read"]

    SA --> A
    A --> L
    L --> M
```

### 3.2 Permission Model

```mermaid
classDiagram
    class RoleConfig {
        +String role_key
        +String display_name
        +JSON permissions
        +Boolean is_system
        +has_permission(module, action) Boolean
    }

    class PermissionEntry {
        +String module
        +List~String~ actions
    }

    RoleConfig "1" --> "*" PermissionEntry : contains

    note for RoleConfig "permissions format:\n{\n  'users': ['read', 'create', 'update', 'delete'],\n  'books': ['read', 'create'],\n  'circulation': ['read']\n}"
```

### 3.3 Permission Modules

| Module | Actions | Description |
|--------|---------|-------------|
| `users` | read, create, update, delete | User management |
| `books` | read, create, update, delete | Book catalog |
| `authors` | read, create, update, delete | Author management |
| `circulation` | read, create, update, delete | Borrow/return/fines |
| `digital_content` | read, create, update, delete | E-books/audiobooks |
| `analytics` | read | Analytics dashboards |
| `ai` | read, create, update, delete | AI configuration |
| `audit` | read | Audit log access |
| `assets` | read, create, update, delete | Physical assets |
| `employees` | read, create, update, delete | HR management |
| `roles` | read, create, update, delete | RBAC configuration |
| `members` | read, create, update, delete | Library members |
| `settings` | read, update | System settings |

### 3.4 Frontend Permission Enforcement

```mermaid
graph TB
    subgraph "Route Level"
        ProtectedRoute["ProtectedRoute<br/>checks isAuthenticated"]
        AdminRoute["AdminRoute<br/>checks admin/librarian role"]
        PermissionGuard["PermissionGuard<br/>checks module permissions"]
    end

    subgraph "Data Level"
        UsePermissions["usePermissions() hook"]
        MyPermissions["MY_PERMISSIONS query"]
        CanCheck["can(module, action) method"]
    end

    subgraph "UI Level"
        ConditionalRender["Conditional rendering<br/>based on can() result"]
        DisabledButtons["Disabled buttons<br/>for unauthorized actions"]
    end

    ProtectedRoute --> AdminRoute
    AdminRoute --> PermissionGuard
    PermissionGuard --> UsePermissions
    UsePermissions --> MyPermissions
    MyPermissions --> CanCheck
    CanCheck --> ConditionalRender
    CanCheck --> DisabledButtons
```

---

## 4. Middleware Security Pipeline

### 4.1 GraphQL Security Middleware

| Check | Limit | Purpose |
|-------|-------|---------|
| **Query Size** | 10,240 bytes | Prevent resource exhaustion |
| **Batch Size** | 5 operations | Prevent batch attacks |
| **Query Depth** | 10 levels | Prevent deep nesting attacks |
| **Query Complexity** | 1,000 points | Prevent expensive queries |
| **Aliases** | 15 max | Prevent alias-based amplification |
| **Introspection** | Disabled in production | Hide schema from attackers |

**Field Cost Configuration:**
| Field | Cost |
|-------|------|
| Default field | 1 |
| `searchBooks` | 10 |
| `semanticSearch` | 15 |
| `books` (paginated) | 5 |
| `users` (paginated) | 5 |
| `allBorrows` (paginated) | 5 |

### 4.2 Rate Limiting

```mermaid
graph TB
    subgraph "Rate Limit Tiers"
        Auth["Auth Tier<br/>Login, Register, Password Reset<br/>Strict limits"]
        Mutation["Mutation Tier<br/>Create, Update, Delete<br/>Moderate limits"]
        Query["Query Tier<br/>Read operations<br/>Relaxed limits"]
        Heartbeat["Heartbeat Tier<br/>Health checks<br/>High-frequency allowed"]
        Upload["Upload Tier<br/>File uploads<br/>Strict limits"]
    end

    subgraph "Implementation"
        TokenBucket["Token Bucket Algorithm<br/>Redis-backed"]
        IPBased["Per-IP Tracking"]
        UserBased["Per-User Tracking<br/>(if authenticated)"]
    end

    Auth --> TokenBucket
    Mutation --> TokenBucket
    Query --> TokenBucket
    TokenBucket --> IPBased
    TokenBucket --> UserBased
```

### 4.3 Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer information |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Restrict browser APIs |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'nonce-{random}'` | Prevent code injection |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolate browsing context |
| `Cross-Origin-Resource-Policy` | `same-origin` | Restrict resource sharing |

---

## 5. Data Security

### 5.1 Input Validation & Sanitization

```mermaid
graph LR
    subgraph "Frontend"
        Zod["Zod Schema Validation"]
        DOMPurify["DOMPurify Sanitization"]
        SafeHtml["SafeHtml Component"]
    end

    subgraph "Backend"
        GraphQLValidation["GraphQL Type Validation"]
        DjangoValidation["Django Model Validators"]
        FileSecurity["File Security<br/>python-magic type checking"]
        Sanitizers["Custom Sanitizers<br/>sanitizers.py"]
    end

    Zod -->|"clean data"| GraphQLValidation
    DOMPurify -->|"sanitized HTML"| GraphQLValidation
    GraphQLValidation --> DjangoValidation
    DjangoValidation --> Sanitizers
    DjangoValidation --> FileSecurity
```

### 5.2 File Upload Security

| Check | Implementation |
|-------|---------------|
| **File Type Validation** | `python-magic` MIME type detection |
| **File Size Limits** | Configurable per upload type |
| **Path Traversal Prevention** | Django's `FileSystemStorage` |
| **Virus Scanning** | File security module (`file_security.py`) |
| **Storage Isolation** | Separate directories per type (covers, ebooks, verifications) |

### 5.3 Sensitive Data Protection

| Data | Protection |
|------|-----------|
| Passwords | Argon2 hashing (never stored in plaintext) |
| Refresh tokens | SHA256 hashed before DB storage |
| OTP codes | SHA256 hashed |
| API keys (AI providers) | Stored encrypted in `AIProviderConfig` |
| System settings | `is_secret` flag hides values in API |
| Face encodings | Stored as numeric arrays, not images |
| NIC data | JSON with parsed OCR data |

---

## 6. Security Event Tracking

### 6.1 Event Types

| Event Type | Severity | Trigger |
|-----------|----------|---------|
| `BRUTE_FORCE` | HIGH | 5+ failed login attempts |
| `SUSPICIOUS_ACCESS` | MEDIUM | Unusual access patterns |
| `RATE_LIMIT_EXCEEDED` | LOW | Rate limit hit |
| `INVALID_TOKEN` | MEDIUM | Tampered/expired JWT |
| `DATA_BREACH_ATTEMPT` | CRITICAL | Unauthorized data access attempt |

### 6.2 Audit Log Coverage

```mermaid
graph TB
    subgraph "Tracked Actions"
        CREATE["CREATE<br/>New resources"]
        READ["READ<br/>Sensitive data access"]
        UPDATE["UPDATE<br/>Resource modifications"]
        DELETE["DELETE<br/>Resource deletions"]
        LOGIN["LOGIN<br/>Authentication events"]
        LOGOUT["LOGOUT<br/>Session termination"]
        EXPORT["EXPORT<br/>Data export events"]
        ADMIN["ADMIN_ACTION<br/>Administrative changes"]
    end

    subgraph "Audit Record"
        AuditLog["AuditLog<br/>actor_id<br/>action<br/>resource_type<br/>resource_id<br/>changes (JSON)<br/>ip_address<br/>user_agent<br/>status<br/>error_message"]
    end

    CREATE --> AuditLog
    READ --> AuditLog
    UPDATE --> AuditLog
    DELETE --> AuditLog
    LOGIN --> AuditLog
    LOGOUT --> AuditLog
    EXPORT --> AuditLog
    ADMIN --> AuditLog
```

---

## 7. Exception Handling Security

The `ExceptionHandlerMiddleware` prevents information leakage:

| Exception Type | HTTP Status | Exposed to Client |
|---------------|-------------|-------------------|
| `AuthenticationError` | 401 | Generic auth error message |
| `AuthorizationError` | 403 | "Permission denied" |
| `NotFoundError` | 404 | "Resource not found" |
| `ValidationError` | 400 | Validation details |
| `RateLimitExceeded` | 429 | "Rate limit exceeded" + retry time |
| **Unknown Exception** | 500 | "Internal server error" (NO stack trace) |

---

## 8. Client-Side Security

### 8.1 Auto-Logout

```mermaid
sequenceDiagram
    participant User
    participant Hook as useAutoLogout
    participant Store as authStore
    participant Timer as 30-min Timer

    User->>Hook: Any activity (mouse, key, touch, scroll)
    Hook->>Timer: Reset timer
    Note over Timer: 30 minutes of inactivity
    Timer->>Store: logout()
    Store->>Store: Clear tokens from localStorage
    Store->>Store: Clear Apollo cache
    Store-->>User: Redirect to /login
```

### 8.2 XSS Prevention

| Layer | Tool | Purpose |
|-------|------|---------|
| HTML rendering | `DOMPurify` via `SafeHtml` component | Sanitize all user-generated HTML |
| API responses | GraphQL type system | Prevent injection via typed responses |
| Form inputs | Zod validation + react-hook-form | Validate and sanitize inputs |
| Content Security Policy | CSP header with nonce | Prevent inline script injection |

---

## 9. Security Configuration Summary

```yaml
# JWT
JWT_ACCESS_TOKEN_EXPIRY: 15 minutes
JWT_REFRESH_TOKEN_EXPIRY: 7 days
JWT_ALGORITHM: HS256
JWT_HEADER_PREFIX: Bearer

# Account Security
FAILED_LOGIN_MAX_ATTEMPTS: 5
ACCOUNT_LOCKOUT: Exponential backoff
MIN_PASSWORD_LENGTH: 10

# Rate Limiting
RATE_LIMIT_ENABLED: true (disabled in dev)
RATE_LIMIT_BACKEND: Redis

# GraphQL Security
MAX_QUERY_DEPTH: 10
MAX_QUERY_COMPLEXITY: 1000
MAX_ALIASES: 15
MAX_QUERY_SIZE: 10240 bytes
MAX_BATCH_SIZE: 5

# CORS
CORS_ALLOWED_ORIGINS: [configured per environment]
CORS_ALLOW_CREDENTIALS: true

# Cookies (Production)
SESSION_COOKIE_SECURE: true
CSRF_COOKIE_SECURE: true
SESSION_COOKIE_HTTPONLY: true
```
