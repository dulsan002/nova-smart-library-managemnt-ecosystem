# 08 — API Reference

> Complete GraphQL API reference — 85+ queries, 81+ mutations, all types across 10 bounded contexts

---

## 1. API Overview

| Metric | Count |
|--------|-------|
| **Total Queries** | 85+ |
| **Total Mutations** | 81+ |
| **DjangoObjectTypes** | 41 |
| **ObjectTypes (virtual)** | 38+ |
| **Bounded Contexts** | 10 |
| **Endpoint** | `POST /graphql/` |
| **Authentication** | JWT Bearer token |
| **Protocol** | GraphQL over HTTP |

---

## 2. Identity API

### 2.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `me` | — | `UserType` | Required | Current authenticated user |
| `user` | `id: UUID!` | `UserType` | Admin/Librarian | Get user by ID |
| `users` | `first: Int, after: String, role: String, isActive: Boolean, search: String` | `UserConnectionType` | Admin/Librarian | Paginated user list |
| `myVerificationRequests` | — | `[VerificationRequestType]` | Required | User's verification history |
| `pendingVerifications` | — | `[VerificationRequestType]` | Admin/Librarian | Pending verification queue |
| `roleConfigs` | — | `[RoleConfigType]` | Super Admin | All RBAC role configurations |
| `roleConfig` | `id: UUID!` | `RoleConfigType` | Super Admin | Single role config |
| `availableModules` | — | `[ModuleInfoType]` | Super Admin | Available permission modules |
| `myPermissions` | — | `GenericScalar` | Required | Current user's module-action map |
| `members` | `first: Int, after: String, status: String, membershipType: String, search: String` | `MemberConnectionType` | Admin/Librarian | Paginated library members |
| `member` | `id: UUID!` | `MemberType` | Admin/Librarian | Single member |

### 2.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `registerUser` | `input: RegisterInput!` | `AuthPayloadType` | Public | Register new user |
| `registerWithNic` | `input: NicRegisterInput!` | `AuthPayloadType` | Public | Register with NIC OCR |
| `verifyNic` | `input: NicVerifyInput!` | `NICVerificationResultType` | Public | Standalone NIC verify |
| `login` | `input: LoginInput!` | `AuthPayloadType` | Public | Authenticate user |
| `refreshToken` | `refreshToken: String!` | `TokenPairType` | Public | Refresh JWT tokens |
| `logout` | `refreshTokenHash: String, revokeAll: Boolean` | `Boolean` | Required | Logout / revoke tokens |
| `updateProfile` | `input: UpdateProfileInput!` | `UserType` | Required | Update own profile |
| `changePassword` | `input: ChangePasswordInput!` | `Boolean` | Required | Change own password |
| `submitVerification` | `idDocumentPath: String!, selfiePath: String` | `VerificationRequestType` | Required | Submit AI verification |
| `requestPasswordReset` | `email: String!` | `PasswordResetResponseType` | Public | Request OTP email |
| `verifyResetOtp` | `sessionToken: String!, otp: String!` | `OtpVerifyResponseType` | Public | Verify 6-digit OTP |
| `confirmPasswordReset` | `sessionToken: String!, newPassword: String!` | `Boolean` | Public | Set new password |
| `activateUser` | `userId: UUID!` | `UserType` | Admin | Activate user account |
| `deactivateUser` | `userId: UUID!` | `UserType` | Admin | Deactivate user account |
| `changeUserRole` | `userId: UUID!, newRole: String!` | `UserType` | Admin | Change user role |
| `adminUpdateUser` | `userId: UUID!, input: AdminUpdateUserInput!` | `UserType` | Admin | Admin update any user |
| `adminCreateUser` | `input: AdminCreateUserInput!` | `UserType` | Admin | Create user (bypass OCR) |
| `createRoleConfig` | `roleKey: String!, displayName: String!, permissions: GenericScalar!` | `RoleConfigType` | Super Admin | Create RBAC role |
| `updateRoleConfig` | `id: UUID!, displayName: String, permissions: GenericScalar` | `RoleConfigType` | Super Admin | Update RBAC role |
| `deleteRoleConfig` | `id: UUID!` | `Boolean` | Super Admin | Delete non-system role |
| `createMember` | `input: CreateMemberInput!` | `MemberType` | Admin/Librarian | Create library member |
| `updateMember` | `id: UUID!, input: UpdateMemberInput!` | `MemberType` | Admin/Librarian | Update member |
| `deleteMember` | `id: UUID!` | `Boolean` | Admin/Librarian | Soft-delete member |

### 2.3 Types

```graphql
type UserType {
  id: UUID!
  email: String!
  firstName: String!
  lastName: String!
  role: String!
  isActive: Boolean!
  isVerified: Boolean!
  phone: String
  dateOfBirth: Date
  address: String
  avatar: String
  nicNumber: String
  verificationStatus: String!
  dateJoined: DateTime!
  lastLogin: DateTime
}

type AuthPayloadType {
  user: UserType!
  accessToken: String!
  refreshToken: String!
}

type RoleConfigType {
  id: UUID!
  roleKey: String!
  displayName: String!
  permissions: GenericScalar!
  isSystem: Boolean!
}

type MemberType {
  id: UUID!
  user: UserType!
  membershipId: String!
  membershipType: String!
  status: String!
  startDate: Date!
  expiryDate: Date
  autoRenew: Boolean!
}

type VerificationRequestType {
  id: UUID!
  user: UserType!
  requestType: String!
  status: String!
  extractedData: GenericScalar
  confidenceScore: Float
  rejectionReason: String
  reviewedBy: UserType
  reviewedAt: DateTime
}
```

---

## 3. Catalog API

### 3.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `book` | `id: UUID!` | `BookType` | Public | Book by ID |
| `bookByIsbn` | `isbn: String!` | `BookType` | Public | Book by ISBN-10 or ISBN-13 |
| `books` | `first: Int, after: String, query: String, categoryId: UUID, authorId: UUID, language: String, availableOnly: Boolean, orderBy: String` | `BookConnectionType` | Public | Paginated book list |
| `authors` | `search: String, limit: Int` | `[AuthorType]` | Public | Author list |
| `author` | `id: UUID!` | `AuthorType` | Public | Author by ID |
| `categories` | `rootOnly: Boolean` | `[CategoryType]` | Public | Category tree |
| `category` | `id: UUID!` | `CategoryType` | Public | Category by ID |
| `bookCopies` | `bookId: UUID!, status: String` | `[BookCopyType]` | Public | Physical copies of a book |

### 3.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `createBook` | `input: BookInput!` | `BookType` | Admin/Librarian | Create book |
| `updateBook` | `bookId: UUID!, input: BookInput!` | `BookType` | Admin/Librarian | Update book |
| `deleteBook` | `bookId: UUID!` | `Boolean` | Admin/Librarian | Soft-delete (blocks if active borrows) |
| `addBookCopy` | `input: BookCopyInput!` | `BookCopyType` | Admin/Librarian | Add physical copy |
| `createAuthor` | `input: AuthorInput!` | `AuthorType` | Admin/Librarian | Create author |
| `updateAuthor` | `authorId: UUID!, input: AuthorInput!` | `AuthorType` | Admin/Librarian | Update author |
| `deleteAuthor` | `authorId: UUID!` | `Boolean` | Admin/Librarian | Delete (blocks if has books) |
| `createCategory` | `input: CategoryInput!` | `CategoryType` | Admin/Librarian | Create category |
| `submitBookReview` | `bookId: UUID!, rating: Int!, title: String, content: String` | `BookReviewType` | Required | Submit review |

### 3.3 Key Types

```graphql
type BookType {
  id: UUID!
  title: String!
  subtitle: String
  isbn10: String
  isbn13: String
  description: String
  language: String!
  pageCount: Int
  publisher: String
  publicationDate: Date
  coverImage: String
  edition: String
  averageRating: Decimal!
  totalRatings: Int!
  totalBorrows: Int!
  authors: [AuthorType!]!
  categories: [CategoryType!]!
  availableCopies: Int!
  totalCopies: Int!
  reviews: [BookReviewType!]!
  digitalAssets: [DigitalAssetType!]!
}

type AuthorType {
  id: UUID!
  name: String!
  biography: String
  birthDate: Date
  deathDate: Date
  nationality: String
  photo: String
  website: String
  bookCount: Int!
}

type CategoryType {
  id: UUID!
  name: String!
  slug: String!
  description: String
  parent: CategoryType
  children: [CategoryType!]!
  icon: String
}
```

---

## 4. Circulation API

### 4.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `myBorrows` | `status: String, limit: Int` | `[BorrowRecordType]` | Required | User's borrows |
| `myReservations` | — | `[ReservationType]` | Required | User's active reservations |
| `myFines` | `status: String` | `[FineType]` | Required | User's fines |
| `myReservationBan` | — | `ReservationBanType` | Required | Active reservation ban |
| `borrowRecord` | `id: UUID!` | `BorrowRecordType` | Staff | Single borrow record |
| `allBorrows` | `first: Int, after: String, status: String, userId: UUID` | `BorrowConnectionType` | Staff | All borrows paginated |
| `overdueBorrows` | `limit: Int` | `[BorrowRecordType]` | Staff | Overdue list |
| `pendingPickups` | `limit: Int` | `[ReservationType]` | Staff | Ready reservations |
| `userBorrows` | `userId: UUID!, status: String, limit: Int` | `[BorrowRecordType]` | Admin/Librarian | Any user's borrows |
| `userFines` | `userId: UUID!, status: String` | `[FineType]` | Admin/Librarian | Any user's fines |
| `userReservations` | `userId: UUID!` | `[ReservationType]` | Admin/Librarian | Any user's reservations |
| `allFines` | `status: String, limit: Int` | `[FineType]` | Staff | All system fines |

### 4.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `reserveBook` | `bookId: UUID!` | `ReservationType` | Required | Reserve book (auto-assigns if available) |
| `confirmPickup` | `reservationId: UUID!` | `BorrowRecordType` | Staff | Staff confirms pickup |
| `returnBook` | `borrowId: UUID!, condition: String` | `BorrowRecordType` | Staff | Process return |
| `renewBorrow` | `borrowId: UUID!` | `BorrowRecordType` | Required | Renew borrow period |
| `cancelReservation` | `reservationId: UUID!` | `Boolean` | Required | Cancel own reservation |
| `payFine` | `fineId: UUID!, amount: Decimal!` | `FineType` | Required | Pay fine |
| `waiveFine` | `fineId: UUID!` | `FineType` | Staff | Waive fine |
| `liftReservationBan` | `banId: UUID!` | `Boolean` | Staff | Lift reservation ban |

### 4.3 Key Types

```graphql
type BorrowRecordType {
  id: UUID!
  user: UserType!
  book: BookType!
  bookCopy: BookCopyType!
  status: String!
  borrowedAt: DateTime!
  dueDate: DateTime!
  returnedAt: DateTime
  renewalCount: Int!
  maxRenewals: Int!
  conditionAtBorrow: String!
  conditionAtReturn: String
  isOverdue: Boolean!
  canRenew: Boolean!
  daysRemaining: Int
}

type ReservationType {
  id: UUID!
  user: UserType!
  book: BookType!
  bookCopy: BookCopyType
  status: String!
  reservedAt: DateTime!
  expiresAt: DateTime
  queuePosition: Int!
}

type FineType {
  id: UUID!
  user: UserType!
  borrowRecord: BorrowRecordType
  fineType: String!
  amount: Decimal!
  paidAmount: Decimal!
  status: String!
  description: String
  issuedAt: DateTime!
  paidAt: DateTime
  remainingAmount: Decimal!
}
```

---

## 5. Digital Content API

### 5.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `digitalAsset` | `id: UUID!` | `DigitalAssetType` | Public | Asset by ID |
| `digitalAssetsForBook` | `bookId: UUID!` | `[DigitalAssetType]` | Public | Assets for book |
| `allDigitalAssets` | `assetType: String` | `[DigitalAssetType]` | Public | All assets |
| `myLibrary` | `favoritesOnly: Boolean` | `[UserLibraryType]` | Required | User's digital library |
| `myReadingSessions` | `status: String, limit: Int` | `[ReadingSessionType]` | Required | Reading sessions |
| `activeSession` | `digitalAssetId: UUID!` | `ReadingSessionType` | Required | Active session |
| `myBookmarks` | `digitalAssetId: UUID` | `[BookmarkType]` | Required | User's bookmarks |
| `myHighlights` | `digitalAssetId: UUID` | `[HighlightType]` | Required | User's highlights |

### 5.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `startReadingSession` | `digitalAssetId: UUID!, sessionType: String!, deviceType: String` | `ReadingSessionType` | Required | Start session |
| `endReadingSession` | `sessionId: UUID!` | `ReadingSessionType` | Required | End session |
| `updateReadingProgress` | `sessionId: UUID!, progressPercent: Float!, position: String` | `ReadingSessionType` | Required | Update progress |
| `addBookmark` | `digitalAssetId: UUID!, title: String!, position: String!, note: String, color: String` | `BookmarkType` | Required | Add bookmark |
| `addHighlight` | `digitalAssetId: UUID!, text: String!, positionStart: String!, positionEnd: String!, color: String, note: String` | `HighlightType` | Required | Add highlight |
| `toggleFavorite` | `digitalAssetId: UUID!` | `UserLibraryType` | Required | Toggle favorite |
| `uploadDigitalAsset` | `bookId: UUID!, assetType: String!, filePath: String!, ...` | `DigitalAssetType` | Admin | Upload asset |
| `updateDigitalAsset` | `digitalAssetId: UUID!, ...` | `DigitalAssetType` | Admin | Update asset |
| `deleteDigitalAsset` | `digitalAssetId: UUID!` | `Boolean` | Admin | Delete asset |

---

## 6. Engagement API

### 6.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `myEngagement` | — | `UserEngagementType` | Required | KP profile |
| `myAchievements` | — | `[UserAchievementType]` | Required | Earned achievements |
| `myDailyActivity` | `days: Int` | `[DailyActivityType]` | Required | Activity log |
| `myRank` | — | `UserRankType` | Required | Rank/percentile |
| `allAchievements` | `category: String` | `[AchievementType]` | Public | Available achievements |
| `leaderboard` | `limit: Int` | `[LeaderboardEntryType]` | Public | Top KP earners |
| `userEngagement` | `userId: UUID!` | `UserEngagementType` | Admin/Librarian | Any user's engagement |
| `userAchievements` | `userId: UUID!` | `[UserAchievementType]` | Admin/Librarian | Any user's achievements |

### 6.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `adminAwardKp` | `userId: UUID!, points: Int!, reason: String!, dimension: String` | `UserEngagementType` | Super Admin | Manual KP adjustment |

---

## 7. Intelligence API

### 7.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `myRecommendations` | `limit: Int, strategy: String` | `[RecommendationType]` | Required | Personalized recommendations |
| `myPreferences` | — | `UserPreferenceType` | Required | Reading preferences |
| `trendingBooks` | `period: String, limit: Int` | `[TrendingBookType]` | Public | Trending books |
| `trendingSearches` | `limit: Int, days: Int` | `[TrendingSearchType]` | Public | Popular searches |
| `aiModels` | `modelType: String` | `[AIModelVersionType]` | Super Admin | AI model versions |
| `searchAnalytics` | `limit: Int` | `[SearchLogType]` | Admin/Librarian | Search logs |
| `searchBooks` | `query: String!, page: Int, pageSize: Int, category: String, author: String, language: String, minRating: Float, yearFrom: Int, yearTo: Int, digitalOnly: Boolean, availableOnly: Boolean` | `SearchResponseType` | Public | Hybrid search |
| `autoSuggest` | `prefix: String!, limit: Int` | `[AutoSuggestType]` | Public | Typeahead suggestions |
| `overduePredictions` | `limit: Int` | `[OverduePredictionType]` | Admin/Librarian | ML overdue risk |
| `demandForecasts` | `limit: Int` | `[DemandForecastType]` | Admin/Librarian | Book demand forecast |
| `churnPredictions` | `limit: Int` | `[ChurnPredictionType]` | Admin/Librarian | User churn prediction |
| `collectionGaps` | `minSeverity: String` | `[CollectionGapType]` | Admin/Librarian | Collection gap analysis |
| `myNotifications` | `limit: Int, unreadOnly: Boolean` | `[NotificationType]` | Required | User notifications |
| `notificationCount` | — | `NotificationCountType` | Required | Unread count by type |
| `myReadingSpeed` | — | `ReadingSpeedType` | Required | Reading speed analysis |
| `mySessionPatterns` | — | `SessionPatternType` | Required | Session pattern |
| `myEngagementHeatmap` | `days: Int` | `EngagementHeatmapType` | Required | Activity heatmap |
| `myCompletionPredictions` | — | `[CompletionPredictionType]` | Required | Book completion predictions |
| `recommendationMetrics` | `k: Int` | `RecommendationMetricsType` | Super Admin | Model evaluation |
| `aiProviderConfigs` | `capability: String, activeOnly: Boolean` | `[AIProviderConfigType]` | Super Admin | AI provider configs |
| `aiProviderConfig` | `id: UUID!` | `AIProviderConfigType` | Super Admin | Single provider |
| `llmAnalytics` | — | `LLMAnalyticsType` | Admin/Librarian | LLM-powered analytics |
| `aiSearch` | `query: String!` | `AISearchResponseType` | Public | AI conversational search |
| `myBrowseHistory` | `limit: Int` | `[BookViewType]` | Required | Book view history |

### 7.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `generateRecommendations` | — | `Boolean` | Required | Trigger async generation |
| `clickRecommendation` | `recommendationId: UUID!` | `RecommendationType` | Required | Record click |
| `dismissRecommendation` | `recommendationId: UUID!` | `Boolean` | Required | Dismiss recommendation |
| `updatePreferences` | `preferredCategories: [UUID], preferredAuthors: [UUID], ...` | `UserPreferenceType` | Required | Update preferences |
| `recomputePreferenceVector` | — | `Boolean` | Required | Recompute embedding |
| `activateAiModel` | `modelId: UUID!` | `AIModelVersionType` | Super Admin | Activate model |
| `markNotificationRead` | `notificationId: UUID!` | `Boolean` | Required | Mark read |
| `markAllNotificationsRead` | — | `Boolean` | Required | Mark all read |
| `logSearchClick` | `searchLogId: UUID!, clickedBookId: UUID!` | `Boolean` | Public | Log search click |
| `logBookView` | `bookId: UUID!, source: String!, durationSeconds: Int` | `Boolean` | Public | Log book view |
| `triggerModelTraining` | `pipeline: String!` | `PipelineResultType` | Super Admin | Trigger ML training |
| `triggerEmbeddingComputation` | `batchSize: Int` | `PipelineResultType` | Super Admin | Batch embedding |
| `createAiProviderConfig` | `provider: String!, capability: String!, ...` | `AIProviderConfigType` | Super Admin | Create provider |
| `updateAiProviderConfig` | `configId: UUID!, ...` | `AIProviderConfigType` | Super Admin | Update provider |
| `deleteAiProviderConfig` | `configId: UUID!` | `Boolean` | Super Admin | Delete provider |
| `activateAiProviderConfig` | `configId: UUID!` | `AIProviderConfigType` | Super Admin | Activate provider |
| `testAiProviderConfig` | `configId: UUID!` | `Boolean` | Super Admin | Health check |
| `generateAiResponse` | `prompt: String!, systemPrompt: String, capability: String` | `String` | Super Admin | Test generation |

### 7.3 Key Types

```graphql
type SearchResponseType {
  results: [SearchResultType!]!
  facets: [SearchFacetType!]!
  total: Int!
  page: Int!
  pageSize: Int!
  searchTime: Float
  query: String!
}

type SearchResultType {
  book: BookType!
  score: Float!
  highlights: [String]
}

type AISearchResponseType {
  answer: String
  sources: [AISearchSourceType]
  modelUsed: String
  error: String
}

type AISearchSourceType {
  bookId: UUID!
  title: String!
  subtitle: String
  authors: [String]
  categories: [String]
  isbn: String
  rating: Float
  availableCopies: Int
  totalCopies: Int
  totalBorrows: Int
}

type RecommendationType {
  id: UUID!
  book: BookType!
  score: Float!
  strategy: String!
  reason: String
  isClicked: Boolean!
  isDismissed: Boolean!
  generatedAt: DateTime!
}

type LLMAnalyticsType {
  summary: String
  modelUsed: String
  generatedAt: DateTime
  error: String
}
```

---

## 8. Governance API

### 8.1 Queries (No Mutations — Append-Only)

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `auditLogs` | `first: Int, after: String, action: String, resourceType: String, actorId: UUID` | `AuditLogConnectionType` | Super Admin | Paginated audit logs |
| `securityEvents` | `severity: String, eventType: String, resolved: Boolean, limit: Int` | `[SecurityEventType]` | Super Admin | Security events |
| `kpLedger` | `userId: UUID, action: String, limit: Int` | `[KPLedgerType]` | Admin/Librarian | KP transactions |
| `myKpHistory` | `limit: Int` | `[KPLedgerType]` | Required | Own KP history |

---

## 9. Asset Management API

### 9.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `assetCategories` | — | `[AssetCategoryType]` | Staff | All categories |
| `assets` | `status: String, categoryId: UUID, search: String, limit: Int` | `[AssetType]` | Staff | Asset list |
| `asset` | `id: UUID!` | `AssetType` | Staff | Asset by ID |
| `assetStats` | — | `AssetStatsType` | Admin/Librarian | Statistics |
| `maintenanceLogs` | `assetId: UUID!, limit: Int` | `[MaintenanceLogType]` | Admin/Librarian | Maintenance history |

### 9.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `createAssetCategory` | `name: String!, slug: String!, ...` | `AssetCategoryType` | Admin | Create category |
| `createAsset` | `assetTag: String!, name: String!, categoryId: UUID!, ...` | `AssetType` | Admin | Create asset |
| `updateAsset` | `id: UUID!, ...` | `AssetType` | Admin | Update asset |
| `deleteAsset` | `id: UUID!` | `Boolean` | Admin | Delete asset |
| `logMaintenance` | `assetId: UUID!, ...` | `MaintenanceLogType` | Admin | Log maintenance |
| `disposeAsset` | `assetId: UUID!, ...` | `AssetDisposalType` | Admin | Dispose asset |

---

## 10. HR API

### 10.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `departments` | `isActive: Boolean` | `[DepartmentType]` | Admin/Librarian | Department list |
| `department` | `id: UUID!` | `DepartmentType` | Admin/Librarian | Department by ID |
| `employees` | `departmentId: UUID, status: String, search: String, limit: Int` | `[EmployeeType]` | Admin/Librarian | Employee list |
| `employee` | `id: UUID!` | `EmployeeType` | Admin/Librarian | Employee by ID |
| `jobVacancies` | `status: String, departmentId: UUID, limit: Int` | `[JobVacancyType]` | Required | Job vacancies |
| `jobVacancy` | `id: UUID!` | `JobVacancyType` | Required | Vacancy by ID |
| `jobApplications` | `vacancyId: UUID, status: String, limit: Int` | `[JobApplicationType]` | Admin/Librarian | Applications |
| `hrStats` | — | `HRStatsType` | Admin/Librarian | HR statistics |

### 10.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `createDepartment` | `name: String!, code: String!, ...` | `DepartmentType` | Admin | Create department |
| `updateDepartment` | `id: UUID!, ...` | `DepartmentType` | Admin | Update department |
| `createEmployee` | `userId: UUID!, employeeId: String!, ...` | `EmployeeType` | Admin | Create employee |
| `updateEmployee` | `id: UUID!, ...` | `EmployeeType` | Admin | Update employee |
| `createJobVacancy` | `title: String!, departmentId: UUID!, ...` | `JobVacancyType` | Admin | Create vacancy |
| `updateJobVacancy` | `id: UUID!, ...` | `JobVacancyType` | Admin | Update vacancy |
| `submitJobApplication` | `vacancyId: UUID!, ...` | `JobApplicationType` | Required | Apply for job |
| `updateApplicationStatus` | `id: UUID!, status: String!, ...` | `JobApplicationType` | Admin | Review application |

---

## 11. Settings API

### 11.1 Queries

| Query | Arguments | Returns | Auth | Description |
|-------|-----------|---------|------|-------------|
| `systemSettings` | `category: String` | `[SystemSettingType]` | Super Admin | All settings |
| `systemSetting` | `key: String!` | `SystemSettingType` | Super Admin | Single setting |

### 11.2 Mutations

| Mutation | Arguments | Returns | Auth | Description |
|---------|-----------|---------|------|-------------|
| `updateSystemSetting` | `key: String!, value: String!` | `SystemSettingType` | Super Admin | Update setting |
| `syncDefaultSettings` | — | `Boolean` | Super Admin | Ensure defaults exist |
| `sendTestEmail` | `toEmail: String!` | `Boolean` | Super Admin | Test SMTP |

---

## 12. Pagination Pattern

All paginated queries use cursor-based pagination:

```graphql
type BookConnectionType {
  edges: [BookEdgeType!]!
  pageInfo: PageInfoType!
  totalCount: Int!
}

type BookEdgeType {
  node: BookType!
  cursor: String!
}

type PageInfoType {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

**Usage:**
```graphql
query {
  books(first: 20, after: "cursor_value") {
    edges {
      node { id title }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

---

## 13. Authentication Patterns

### Public Endpoints (No Auth Required)
- `book`, `books`, `authors`, `categories`, `searchBooks`, `aiSearch`, `trendingBooks`, `leaderboard`, `allAchievements`, `jobVacancies`, `autoSuggest`
- `registerUser`, `login`, `requestPasswordReset`, `verifyResetOtp`, `confirmPasswordReset`

### Authenticated Endpoints (Any Logged-In User)
- All `my*` queries (`myBorrows`, `myRecommendations`, etc.)
- `reserveBook`, `renewBorrow`, `payFine`, `submitBookReview`
- `startReadingSession`, `addBookmark`, `addHighlight`

### Staff Endpoints (Librarian + Admin + Super Admin)
- `allBorrows`, `overdueBorrows`, `pendingPickups`
- `confirmPickup`, `returnBook`, `waiveFine`
- `assets`, `assetCategories`

### Admin Endpoints (Admin + Super Admin)
- User management: `activateUser`, `deactivateUser`, `changeUserRole`
- HR, Assets, Engagement admin queries

### Super Admin Only
- `auditLogs`, `securityEvents`
- `roleConfigs`, RBAC mutations
- `systemSettings`, Settings mutations
- AI model/provider management
