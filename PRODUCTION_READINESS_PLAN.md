# Nova Smart Library Management Ecosystem — Production Readiness Plan

**Principal Software Engineer Audit Report**  
**Date:** February 21, 2026  
**Status:** CRITICAL — 60+ bugs identified across backend and frontend  

---

## Executive Summary

A comprehensive audit of the Nova ecosystem has identified **27 backend bugs** and **39 frontend bugs** spanning all 8 bounded contexts. The application is **non-functional** for core user flows:

- **Registration** — completely broken (wrong variable structure)
- **Profile updates** — completely broken (unwrapped input + wrong response path)
- **Catalog/Book listings** — empty (wrong response field names + pagination mismatch)
- **Search** — returns no results (wrong variable names)  
- **Book detail** — no copies, no reviews, no ISBN shown
- **Digital library** — broken progress display, non-working favorites
- **All paginated endpoints** — crash with TypeError (tuple vs dict mismatch)
- **All event publishing** — crash with TypeError (wrong DomainEvent kwargs)

No AI/LLM integration exists beyond local sentence-transformers for embeddings.

---

## Phase 1: Critical Backend Fixes (P0 — Blocks All Functionality)

### 1.1 Fix Pagination (affects EVERY list query)

| File | Issue | Fix |
|------|-------|-----|
| `backend/apps/common/pagination.py` | Returns `(items, page_info)` tuple but callers expect dict with `edges` key | Change return to `{'edges': items, 'page_info': page_info_dict}` |
| All query resolvers | All callers use `page['edges']`, `page['page_info']` | Consistent after pagination fix |

### 1.2 Fix DomainEvent Calls (4 apps broken)

| File | Issue | Fix |
|------|-------|-----|
| `catalog/application/__init__.py` | Uses `aggregate_id=`, `data=` — not valid DomainEvent fields | Change to `payload=`, `metadata=` |
| `circulation/application/__init__.py` | Same | Same |
| `digital_content/application/__init__.py` | Same | Same |
| `engagement/application/__init__.py` | Same | Same |

### 1.3 Fix Exception Constructor Mismatches (Circulation)

| File | Issue | Fix |
|------|-------|-----|
| `circulation/application/__init__.py` | `BookUnavailableError(message=..., code=...)` — wrong kwargs | Use positional args per constructor signature |
| `circulation/application/__init__.py` | `BorrowLimitExceededError(message=..., code=...)` — wrong kwargs | Same |
| `circulation/application/__init__.py` | `UnpaidFinesError(message=..., code=...)` — wrong kwargs | Same |
| `circulation/application/__init__.py` | `NotFoundError(message=..., code=...)` — wrong kwargs | `NotFoundError(resource_type='Book')` |
| `catalog/application/__init__.py` | Same NotFoundError issue | Same fix |

### 1.4 Fix Audit Logging (silently broken)

| File | Issue | Fix |
|------|-------|-----|
| `common/decorators.py` | Imports `governance.application.services` — doesn't exist | Change to `governance.services` |
| `common/decorators.py` | Calls `AuditService.log(actor=user, request=info.context)` — wrong params | Match actual `AuditService.log()` signature |

### 1.5 Fix Token Service Bugs

| File | Issue | Fix |
|------|-------|-----|
| `identity/infrastructure/token_service.py` | `GRAPHENE_JWT` → should be `GRAPHQL_JWT` | Fix config key |
| `identity/infrastructure/token_service.py` | `revoke_token_family(rt.id)` — needs object, not UUID | Pass `rt` directly |
| `identity/infrastructure/token_service.py` | `TokenError(code=...)` — not valid kwarg | Remove `code` param |

### 1.6 Fix Config Key Casing

| File | Issue | Fix |
|------|-------|-----|
| `engagement/domain/models.py` | Uses `'daily_kp_cap'` but setting defines `'DAILY_KP_CAP'` | Normalize to uppercase |
| `engagement/application/__init__.py` | Same casing mismatch across all config keys | Same |
| `circulation/application/__init__.py` | Uses `'borrow_period_days'` but setting defines `'DEFAULT_BORROW_DAYS'` | Match settings keys |
| `circulation/domain/models.py` | Same | Same |

### 1.7 Fix calculate_fine_amount

| File | Issue | Fix |
|------|-------|-----|
| `circulation/application/__init__.py` | Missing `base_rate`, `escalation_tiers` args | Add from `CIRCULATION_CONFIG` |

### 1.8 Fix Validators

| File | Issue | Fix |
|------|-------|-----|
| `identity/application/services.py` | `validate_email_format()` returns bool, not checked | Make validators raise `ValidationError` |
| `common/validators.py` | Same — validators return values | Raise exceptions on failure |

### 1.9 Fix Intelligence Schema Bugs

| File | Issue | Fix |
|------|-------|-----|
| `intelligence/presentation/schema.py` | `ReadingSession.filter(asset_id=...)` — field is `digital_asset` | Change to `digital_asset_id` |
| `intelligence/presentation/schema.py` | `User.filter(role__in=['MEMBER', 'STUDENT'])` — invalid roles | Change to `['USER']` |
| `intelligence/presentation/schema.py` | `asset.title` — no such field | Change to `asset.book.title` |

### 1.10 Fix AdminAwardKP

| File | Issue | Fix |
|------|-------|-----|
| `engagement/presentation/schema.py` | Uses `action='ADMIN_ADJUST'` which has 0 points in weights | Pass explicit points arg through to award |

---

## Phase 2: Critical Frontend Fixes (P0 — Blocks All User Flows)

### 2.1 Registration Page (COMPLETELY BROKEN)

| File | Issue | Fix |
|------|-------|-----|
| `RegisterPage.tsx` | Variables not wrapped in `input` | `variables: { input: { email, password, firstName, lastName } }` |
| `RegisterPage.tsx` | Post-registration redirect to `/auth/login` — route is `/login` | Change to `/login` |
| `RegisterPage.tsx` | Login link points to `/auth/login` | Change to `/login` |
| `LoginPage.tsx` | Register link points to `/auth/register` | Change to `/register` |
| `useAutoLogout.ts` | Redirects to `/auth/login` | Change to `/login` |

### 2.2 Profile Page (COMPLETELY BROKEN)

| File | Issue | Fix |
|------|-------|-----|
| `ProfilePage.tsx` | `updateProfile` variables not wrapped in `input` | Wrap in `{ input: {...} }` |
| `ProfilePage.tsx` | Response accessed as `data?.updateProfile?.user` | Change to `data?.updateProfile` |
| `ProfilePage.tsx` | `changePassword` variables not wrapped in `input` | Wrap in `{ input: {...} }` |

### 2.3 Book Cover Images (ALL MISSING)

| Files | Issue | Fix |
|-------|-------|-----|
| 7 page files | `book.coverImage` | Change to `book.coverImageUrl` |

### 2.4 Author Names (ALL SHOW "undefined")

| Files | Issue | Fix |
|-------|-------|-----|
| 6 page files | `a.name` | Change to `` `${a.firstName} ${a.lastName}` `` |

### 2.5 Catalog Page (EMPTY)

| File | Issue | Fix |
|------|-------|-----|
| `CatalogPage.tsx` | `booksData?.allBooks?.edges` | Change to `booksData?.books?.edges` |
| `CatalogPage.tsx` | `catData?.allCategories` | Change to `catData?.categories` |
| `CatalogPage.tsx` | Sends `search` variable | Change to `query` |
| `CatalogPage.tsx` | Uses `edges.map(e => e.node)` but backend returns flat list | Remove `.node` unwrapping |

### 2.6 Search Page (NO RESULTS)

| File | Issue | Fix |
|------|-------|-----|
| `SearchPage.tsx` | `searchData?.searchBooks` — not an array | Change to `searchData?.searchBooks?.results` |
| `SearchPage.tsx` | Variable `query` for suggest | Change to `prefix` |
| `SearchPage.tsx` | `result.book?.title` | Change to `result.title` (flat structure) |
| `SearchPage.tsx` | `logClick` wrong variables | Match mutation params |

### 2.7 Book Detail Page (BROKEN)

| File | Issue | Fix |
|------|-------|-----|
| `BookDetailPage.tsx` | `book.isbn` | Change to `book.isbn13` |
| `BookDetailPage.tsx` | `copy.copyNumber` / `copy.location` | Change to `copy.barcode` / `copy.shelfLocation` |
| `BookDetailPage.tsx` | `borrowBook({ variables: { bookCopyId } })` | Change to `{ copyId }` |
| `queries/catalog.ts` | `copies: bookCopies(bookId: $id)` nested wrong | Use `copies { ... }` sub-field |
| `queries/catalog.ts` | Missing `reviews` in GET_BOOK | Add reviews sub-query |
| `queries/catalog.ts` | `readingLevel` doesn't exist | Remove from fragment |

### 2.8 Digital Library Page (BROKEN DISPLAY)

| File | Issue | Fix |
|------|-------|-----|
| `DigitalLibraryPage.tsx` | `item.progress` | Change to `item.progressPercent` |
| `DigitalLibraryPage.tsx` | `session.startTime` / `session.endTime` | Change to `session.startedAt` / `session.endedAt` |
| `DigitalLibraryPage.tsx` | `toggleFavorite({ variables: { assetId } })` | Change to `{ digitalAssetId }` |

### 2.9 Other Pages

| File | Issue | Fix |
|------|-------|-----|
| `MyFinesPage.tsx` | `fine.borrow` | Change to `fine.borrowRecord` |
| `DashboardPage.tsx` | `engagement.kpLevel` | Change to `engagement.level` |
| `LeaderboardPage.tsx` | `entry.kpLevel` / `myRank.kpLevel` | Change to `.level` |
| `MyBorrowsPage.tsx` | `{ first: 50 }` | Change to `{ limit: 50 }` |

### 2.10 Apollo Client Token Refresh

| File | Issue | Fix |
|------|-------|-----|
| `lib/apollo.ts` | `errorLink` doesn't return Observable from token refresh | Use `fromPromise()` from `@apollo/client/link/error` |

---

## Phase 3: AI Model Configuration System (P1)

### 3.1 New Database Model: `AIProviderConfig`

```
Fields:
  - provider: SENTENCE_TRANSFORMERS | OLLAMA | GEMINI | OPENAI | HUGGINGFACE
  - model_type: EMBEDDING | CHAT | OCR | FACE
  - model_name: string (e.g. "llama3.1", "gemini-pro")
  - endpoint_url: string (e.g. "http://localhost:11434")
  - api_key_encrypted: string
  - config_json: JSONField (temperature, max_tokens, etc.)
  - is_active: boolean (one active per model_type)
  - health_status: HEALTHY | DEGRADED | OFFLINE
  - last_health_check: datetime
```

### 3.2 Provider Abstraction Layer

```
backend/apps/intelligence/infrastructure/ai_providers/
├── __init__.py          # Factory: get_provider(model_type)
├── base.py              # ABC: EmbeddingProvider, ChatProvider
├── sentence_transformers_provider.py
├── ollama_provider.py   # REST client for Ollama API
├── gemini_provider.py   # Google Generative AI SDK
└── openai_provider.py   # OpenAI-compatible APIs
```

### 3.3 Super Admin Configuration UI

- New admin page: `/admin/ai-configuration`
- Provider selection dropdown (Ollama, Gemini, OpenAI, Local)
- Model name input with validation
- Endpoint URL configuration
- API key management (encrypted storage)
- Health check / test connection button
- Active model indicator per model type

### 3.4 GraphQL Schema Extensions

```graphql
type AIProviderConfigType {
  id: UUID!
  provider: String!
  modelType: String!
  modelName: String!
  endpointUrl: String
  isActive: Boolean!
  healthStatus: String!
  lastHealthCheck: DateTime
}

# Admin mutations
mutation ConfigureAIProvider(input: AIProviderInput!) → AIProviderConfigType
mutation TestAIProvider(providerId: UUID!) → { success, latencyMs, error }
mutation ActivateAIProvider(providerId: UUID!) → { success }

# Admin queries  
query aiProviders(modelType: String) → [AIProviderConfigType]
query aiProviderHealth → [AIProviderHealthType]
```

### 3.5 Ollama Integration Specifics

```python
class OllamaProvider(EmbeddingProvider, ChatProvider):
    """Connects to local Ollama instance for llama3.1"""
    
    def embed_text(self, text: str) -> List[float]:
        # POST http://localhost:11434/api/embeddings
        # model: "nomic-embed-text" or "llama3.1"
        
    def generate(self, prompt: str, system: str = '') -> str:
        # POST http://localhost:11434/api/generate
        # model: "llama3.1"
        # Supports streaming
```

---

## Phase 4: Data Integrity & Seeding (P1)

### 4.1 Run seed_data after all fixes
### 4.2 Add data migration for AI provider defaults
### 4.3 Verify all GraphQL queries with seeded data

---

## Phase 5: Production Hardening (P2)

### 5.1 Security

| Item | Status | Action |
|------|--------|--------|
| SECRET_KEY has fallback default | ⚠️ | Remove default, require env var |
| STATICFILES_DIRS contains STATIC_ROOT | ⚠️ | Separate directories |
| `uuid` PyPI package | ⚠️ | Remove from requirements (stdlib) |
| Digital assets unprotected | ⚠️ | Add `@require_authentication` |
| CORS properly configured | ✅ | Already set |
| JWT rotation | ✅ | Already implemented |
| CSP headers | ✅ | Already set |
| Rate limiting | ✅ | Already configured |

### 5.2 Performance

| Item | Action |
|------|--------|
| Database indexes | Audit all FK fields, add composite indexes for frequent queries |
| Query optimization | Add `select_related`/`prefetch_related` to all resolvers |
| Caching | Add Redis caching for trending, recommendations, search |
| Connection pooling | Configure pgBouncer or django-db-connection-pool |
| Static files | Configure WhiteNoise or CDN |

### 5.3 Observability

| Item | Action |
|------|--------|
| Structured logging | Already implemented with JSON formatter |
| Error tracking | Add Sentry integration |
| APM | Add New Relic or Datadog traces |
| Health checks | Add `/health` and `/readiness` endpoints |
| Metrics | Add Prometheus metrics for key operations |

### 5.4 Deployment

| Item | Action |
|------|--------|
| Docker | Create production Dockerfile + docker-compose |
| CI/CD | GitHub Actions pipeline (lint → test → build → deploy) |
| Database migrations | Automate with zero-downtime strategy |
| Secrets management | Use AWS Secrets Manager or Vault |
| SSL/TLS | Configure HTTPS in production |
| WSGI server | Use Gunicorn with proper worker configuration |

### 5.5 Testing

| Item | Current | Target |
|------|---------|--------|
| Unit tests | Minimal | 80%+ coverage for domain & application layers |
| Integration tests | None | GraphQL endpoint tests for all queries/mutations |
| E2E tests | None | Playwright tests for critical user flows |
| Load tests | None | k6 scripts for API endpoints |

---

## Phase 6: Feature Completeness (P2)

### 6.1 Missing Features
- Server-side logout (revoke refresh token)
- Backward pagination support
- Email verification flow (SMTP integration)
- Password reset flow
- File upload for covers, ebooks, audiobooks
- Real-time notifications (WebSocket/SSE)
- Export/reporting for admin

### 6.2 Frontend Polish
- Loading skeletons for all pages
- Error boundaries with retry
- Offline indicator
- Responsive design audit
- Accessibility (WCAG 2.1 AA)
- i18n support

---

## Implementation Priority

| Priority | Phase | Estimated Effort | Impact |
|----------|-------|-----------------|--------|
| **P0** | Phase 1 (Backend fixes) | 3-4 days | Unblocks all functionality |
| **P0** | Phase 2 (Frontend fixes) | 3-4 days | All pages become functional |
| **P1** | Phase 3 (AI Configuration) | 5-7 days | AI model management |
| **P1** | Phase 4 (Data/Seeding) | 1 day | Verified working state |
| **P2** | Phase 5 (Production) | 2-3 weeks | Production deployment |
| **P2** | Phase 6 (Features) | 3-4 weeks | Feature complete |

**Total estimated effort:** 6-8 weeks to production-ready state.

---

## Next Steps

1. ✅ Audit complete
2. 🔨 Begin Phase 1 & 2 fixes (in progress)
3. 📐 Design AI provider architecture
4. 🧪 Run full test suite after fixes
5. 📦 Dockerize and deploy
