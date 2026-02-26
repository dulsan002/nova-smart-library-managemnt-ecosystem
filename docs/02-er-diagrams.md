# 02 — Entity-Relationship Diagrams

> Complete ER diagrams for all 38 concrete models + 4 abstract base models across 10 bounded contexts

---

## 1. Complete System ER Overview

This high-level diagram shows all entities and their cross-context relationships:

```mermaid
erDiagram
    User ||--o{ BorrowRecord : "borrows"
    User ||--o{ Reservation : "reserves"
    User ||--o{ Fine : "owes"
    User ||--o{ BookReview : "writes"
    User ||--o{ ReadingSession : "reads"
    User ||--o{ UserLibrary : "has library"
    User ||--o{ UserEngagement : "has engagement"
    User ||--o{ UserAchievement : "earns"
    User ||--o{ DailyActivity : "logs activity"
    User ||--o{ Recommendation : "receives"
    User ||--o{ UserPreference : "configures"
    User ||--o{ SearchLog : "searches"
    User ||--o{ BookView : "views"
    User ||--o{ AuditLog : "triggers"
    User ||--o{ SecurityEvent : "causes"
    User ||--o{ KPLedger : "earns KP"
    User ||--o{ VerificationRequest : "requests"
    User ||--o{ Member : "has membership"
    User ||--o{ Employee : "is employee"
    User ||--o{ ReservationBan : "may be banned"

    Book ||--o{ BookCopy : "has copies"
    Book ||--o{ BookReview : "has reviews"
    Book ||--o{ BorrowRecord : "is borrowed"
    Book ||--o{ Reservation : "is reserved"
    Book ||--o{ DigitalAsset : "has digital"
    Book ||--o{ Recommendation : "is recommended"
    Book ||--o{ TrendingBook : "trends"
    Book ||--o{ BookView : "is viewed"
    Book }o--o{ Author : "written by"
    Book }o--o{ Category : "categorized in"

    BookCopy ||--o{ BorrowRecord : "copy lent"

    DigitalAsset ||--o{ ReadingSession : "has sessions"
    DigitalAsset ||--o{ Bookmark : "has bookmarks"
    DigitalAsset ||--o{ Highlight : "has highlights"
    DigitalAsset ||--o{ UserLibrary : "in library"

    Category ||--o{ Category : "has children"

    Achievement ||--o{ UserAchievement : "awarded as"

    Department ||--o{ Employee : "employs"
    Department ||--o{ JobVacancy : "posts"
    JobVacancy ||--o{ JobApplication : "receives"

    AssetCategory ||--o{ Asset : "categorizes"
    Asset ||--o{ MaintenanceLog : "maintained"
    Asset ||--o{ AssetDisposal : "disposed"
```

---

## 2. Common Module — Abstract Base Models

These abstract models are inherited across all bounded contexts:

```mermaid
erDiagram
    TimeStampedModel {
        datetime created_at "auto_now_add"
        datetime updated_at "auto_now"
    }

    UUIDModel {
        uuid id "Primary Key - UUID4"
    }

    SoftDeletableModel {
        boolean is_deleted "default false"
        datetime deleted_at "nullable"
    }

    VersionedModel {
        integer version "default 1 - auto-increment on save"
    }

    SystemSetting {
        uuid id "PK"
        string key "unique, max 100"
        text value "setting value"
        string value_type "str, int, float, bool, json"
        string category "general, circulation, engagement, ai, notification, security"
        text description "nullable"
        boolean is_secret "default false"
        datetime created_at
        datetime updated_at
    }
```

---

## 3. Identity Context

```mermaid
erDiagram
    User {
        uuid id "PK - UUID4"
        string email "unique, max 255"
        string password "Argon2 hashed"
        string first_name "max 150"
        string last_name "max 150"
        string role "SUPER_ADMIN, ADMIN, LIBRARIAN, MEMBER"
        boolean is_active "default true"
        boolean is_verified "default false"
        boolean is_staff "default false"
        boolean is_superuser "default false"
        string phone "nullable, max 20"
        date date_of_birth "nullable"
        text address "nullable"
        string avatar "nullable, upload to avatars/"
        string nic_number "nullable, unique, max 20"
        json nic_data "nullable"
        float face_encoding "nullable"
        string verification_status "UNVERIFIED, PENDING, VERIFIED, REJECTED"
        datetime date_joined "auto_now_add"
        datetime last_login "nullable"
        integer failed_login_attempts "default 0"
        datetime locked_until "nullable"
        datetime created_at
        datetime updated_at
    }

    RoleConfig {
        uuid id "PK"
        string role_key "unique, max 50"
        string display_name "max 100"
        json permissions "module to actions map"
        boolean is_system "default false"
        datetime created_at
        datetime updated_at
    }

    Member {
        uuid id "PK"
        uuid user_id "FK to User, unique"
        string membership_id "unique, max 20"
        string membership_type "STANDARD, PREMIUM, STUDENT, SENIOR, STAFF"
        string status "ACTIVE, SUSPENDED, EXPIRED, CANCELLED"
        date start_date
        date expiry_date "nullable"
        text notes "nullable"
        boolean auto_renew "default true"
        boolean is_deleted "default false"
        datetime deleted_at "nullable"
        datetime created_at
        datetime updated_at
    }

    VerificationRequest {
        uuid id "PK"
        uuid user_id "FK to User"
        string request_type "NIC_ONLY, NIC_FACE, AI_VERIFICATION"
        string status "PENDING, APPROVED, REJECTED"
        string id_document "upload path"
        string selfie "nullable, upload path"
        json extracted_data "nullable"
        float confidence_score "nullable"
        text rejection_reason "nullable"
        uuid reviewed_by_id "nullable FK to User"
        datetime reviewed_at "nullable"
        datetime created_at
        datetime updated_at
    }

    RefreshToken {
        uuid id "PK"
        uuid user_id "FK to User"
        string token_hash "unique, max 255"
        datetime expires_at
        boolean is_revoked "default false"
        string device_info "nullable, max 500"
        string ip_address "nullable"
        datetime created_at
    }

    PasswordResetToken {
        uuid id "PK"
        uuid user_id "FK to User"
        string session_token "unique, max 255"
        string otp_hash "max 255"
        boolean otp_verified "default false"
        integer attempts "default 0"
        datetime expires_at
        datetime created_at
    }

    User ||--o| Member : "has"
    User ||--o{ VerificationRequest : "submits"
    User ||--o{ RefreshToken : "has tokens"
    User ||--o{ PasswordResetToken : "resets password"
    User ||--o{ RoleConfig : "has role via role_key"
```

---

## 4. Catalog Context

```mermaid
erDiagram
    Book {
        uuid id "PK"
        string title "max 500, indexed"
        string subtitle "nullable, max 500"
        string isbn_10 "nullable, unique, max 10"
        string isbn_13 "nullable, unique, max 13"
        text description "nullable"
        string language "max 50, default English"
        integer page_count "nullable"
        string publisher "nullable, max 300"
        date publication_date "nullable"
        string cover_image "nullable, upload to covers/"
        string edition "nullable, max 100"
        decimal average_rating "max 5.00, default 0"
        integer total_ratings "default 0"
        integer total_borrows "default 0"
        json table_of_contents "nullable"
        string embedding_status "PENDING, COMPUTING, COMPUTED, FAILED"
        boolean is_deleted "default false"
        datetime deleted_at "nullable"
        integer version "optimistic lock"
        datetime created_at
        datetime updated_at
    }

    Author {
        uuid id "PK"
        string name "max 300"
        text biography "nullable"
        date birth_date "nullable"
        date death_date "nullable"
        string nationality "nullable, max 100"
        string photo "nullable, upload to authors/"
        string website "nullable"
        datetime created_at
        datetime updated_at
    }

    Category {
        uuid id "PK"
        string name "unique, max 200"
        string slug "unique, max 200"
        text description "nullable"
        uuid parent_id "nullable, self FK"
        string icon "nullable, max 50"
        integer sort_order "default 0"
        datetime created_at
        datetime updated_at
    }

    BookCopy {
        uuid id "PK"
        uuid book_id "FK to Book"
        string barcode "unique, max 50"
        string status "AVAILABLE, BORROWED, RESERVED, MAINTENANCE, LOST, DAMAGED"
        string condition "NEW, GOOD, FAIR, POOR, DAMAGED"
        string location "nullable, max 200"
        string shelf_number "nullable, max 50"
        date acquisition_date "nullable"
        decimal price "nullable"
        text notes "nullable"
        datetime created_at
        datetime updated_at
    }

    BookReview {
        uuid id "PK"
        uuid book_id "FK to Book"
        uuid user_id "FK to User"
        integer rating "1-5"
        string title "nullable, max 200"
        text content "nullable"
        boolean is_approved "default true"
        datetime created_at
        datetime updated_at
    }

    Book }o--o{ Author : "book_authors M2M"
    Book }o--o{ Category : "book_categories M2M"
    Book ||--o{ BookCopy : "has copies"
    Book ||--o{ BookReview : "has reviews"
    Category ||--o{ Category : "parent-child"
```

---

## 5. Circulation Context

```mermaid
erDiagram
    BorrowRecord {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid book_id "FK to Book"
        uuid book_copy_id "FK to BookCopy"
        uuid reservation_id "nullable FK to Reservation"
        string status "ACTIVE, RETURNED, OVERDUE, LOST"
        datetime borrowed_at "auto_now_add"
        datetime due_date
        datetime returned_at "nullable"
        integer renewal_count "default 0"
        integer max_renewals "default 2"
        string condition_at_borrow "book condition"
        string condition_at_return "nullable"
        text notes "nullable"
        datetime created_at
        datetime updated_at
    }

    Reservation {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid book_id "FK to Book"
        uuid book_copy_id "nullable FK to BookCopy"
        string status "PENDING, READY, FULFILLED, CANCELLED, EXPIRED"
        datetime reserved_at "auto_now_add"
        datetime expires_at "nullable"
        datetime notified_at "nullable"
        integer queue_position "default 0"
        text cancellation_reason "nullable"
        datetime created_at
        datetime updated_at
    }

    ReservationBan {
        uuid id "PK"
        uuid user_id "FK to User, unique"
        string reason "max 500"
        datetime banned_at "auto_now_add"
        datetime expires_at "nullable"
        uuid banned_by_id "FK to User"
        boolean is_active "default true"
        datetime created_at
        datetime updated_at
    }

    Fine {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid borrow_record_id "nullable FK to BorrowRecord"
        string fine_type "OVERDUE, DAMAGE, LOST, OTHER"
        decimal amount "max 99999.99"
        decimal paid_amount "default 0"
        string status "PENDING, PARTIAL, PAID, WAIVED"
        text description "nullable"
        datetime issued_at "auto_now_add"
        datetime paid_at "nullable"
        uuid waived_by_id "nullable FK to User"
        text waiver_reason "nullable"
        datetime created_at
        datetime updated_at
    }

    BorrowRecord }o--|| User : "borrowed by"
    BorrowRecord }o--|| Book : "book"
    BorrowRecord }o--|| BookCopy : "specific copy"
    BorrowRecord }o--o| Reservation : "from reservation"
    Reservation }o--|| User : "reserved by"
    Reservation }o--|| Book : "reserved book"
    Reservation }o--o| BookCopy : "assigned copy"
    ReservationBan }o--|| User : "banned user"
    Fine }o--|| User : "fined user"
    Fine }o--o| BorrowRecord : "related borrow"
```

---

## 6. Digital Content Context

```mermaid
erDiagram
    DigitalAsset {
        uuid id "PK"
        uuid book_id "FK to Book"
        string asset_type "EBOOK, AUDIOBOOK, PDF, EPUB"
        string file_path "max 500"
        integer file_size "bytes, nullable"
        string mime_type "nullable, max 100"
        string format_details "nullable, max 200"
        integer duration_seconds "nullable, for audio"
        integer total_pages "nullable, for ebooks"
        string language "nullable, max 50"
        boolean is_active "default true"
        integer download_count "default 0"
        datetime created_at
        datetime updated_at
    }

    ReadingSession {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid digital_asset_id "FK to DigitalAsset"
        string session_type "READING, LISTENING"
        string device_type "nullable, max 50"
        string status "ACTIVE, PAUSED, COMPLETED"
        float progress_percent "default 0"
        string current_position "nullable, max 100"
        datetime started_at "auto_now_add"
        datetime ended_at "nullable"
        integer duration_seconds "default 0"
        integer pages_read "default 0"
        datetime created_at
        datetime updated_at
    }

    Bookmark {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid digital_asset_id "FK to DigitalAsset"
        string title "max 200"
        string position "max 100"
        text note "nullable"
        string color "nullable, max 20"
        datetime created_at
        datetime updated_at
    }

    Highlight {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid digital_asset_id "FK to DigitalAsset"
        text text "highlighted text"
        string position_start "max 100"
        string position_end "max 100"
        string color "nullable, max 20"
        text note "nullable"
        datetime created_at
        datetime updated_at
    }

    UserLibrary {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid digital_asset_id "FK to DigitalAsset"
        boolean is_favorite "default false"
        float last_progress "default 0"
        string last_position "nullable, max 100"
        datetime last_accessed "nullable"
        datetime added_at "auto_now_add"
        datetime created_at
        datetime updated_at
    }

    DigitalAsset }o--|| Book : "digital of"
    ReadingSession }o--|| User : "read by"
    ReadingSession }o--|| DigitalAsset : "reading"
    Bookmark }o--|| User : "owned by"
    Bookmark }o--|| DigitalAsset : "in asset"
    Highlight }o--|| User : "owned by"
    Highlight }o--|| DigitalAsset : "in asset"
    UserLibrary }o--|| User : "in library of"
    UserLibrary }o--|| DigitalAsset : "asset entry"
```

---

## 7. Engagement Context

```mermaid
erDiagram
    UserEngagement {
        uuid id "PK"
        uuid user_id "FK to User, unique"
        integer total_kp "default 0"
        integer level "default 1"
        integer books_read "default 0"
        integer reviews_written "default 0"
        integer reading_streak "default 0"
        integer longest_streak "default 0"
        date last_activity_date "nullable"
        integer total_reading_time "minutes, default 0"
        string reading_tier "BRONZE, SILVER, GOLD, PLATINUM, DIAMOND"
        json dimension_scores "nullable"
        datetime created_at
        datetime updated_at
    }

    Achievement {
        uuid id "PK"
        string name "unique, max 200"
        string slug "unique, max 200"
        text description
        string icon "nullable, max 100"
        string category "READING, SOCIAL, STREAK, EXPLORATION, MILESTONE"
        string tier "BRONZE, SILVER, GOLD, PLATINUM"
        integer kp_reward "default 0"
        json criteria "achievement unlock rules"
        boolean is_active "default true"
        integer sort_order "default 0"
        datetime created_at
        datetime updated_at
    }

    UserAchievement {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid achievement_id "FK to Achievement"
        datetime earned_at "auto_now_add"
        integer progress "default 100"
        text context "nullable"
        datetime created_at
        datetime updated_at
    }

    DailyActivity {
        uuid id "PK"
        uuid user_id "FK to User"
        date activity_date
        integer pages_read "default 0"
        integer reading_minutes "default 0"
        integer books_completed "default 0"
        integer reviews_written "default 0"
        integer kp_earned "default 0"
        integer sessions_count "default 0"
        json activity_details "nullable"
        datetime created_at
        datetime updated_at
    }

    UserEngagement }o--|| User : "profile of"
    UserAchievement }o--|| User : "earned by"
    UserAchievement }o--|| Achievement : "instance of"
    DailyActivity }o--|| User : "activity of"
```

---

## 8. Intelligence Context

```mermaid
erDiagram
    Recommendation {
        uuid id "PK"
        uuid user_id "FK to User"
        uuid book_id "FK to Book"
        float score "0.0-1.0"
        string strategy "COLLABORATIVE, CONTENT_BASED, HYBRID, TRENDING, POPULAR"
        string reason "max 500, nullable"
        boolean is_clicked "default false"
        boolean is_dismissed "default false"
        datetime generated_at "auto_now_add"
        datetime expires_at "nullable"
        datetime created_at
        datetime updated_at
    }

    UserPreference {
        uuid id "PK"
        uuid user_id "FK to User, unique"
        json preferred_categories "nullable"
        json preferred_authors "nullable"
        json preferred_languages "nullable"
        string reading_pace "SLOW, MODERATE, FAST"
        string content_length_pref "SHORT, MEDIUM, LONG, ANY"
        json topic_interests "nullable"
        boolean notify_new_releases "default true"
        boolean notify_recommendations "default true"
        json preference_vector "nullable - embedding"
        datetime created_at
        datetime updated_at
    }

    SearchLog {
        uuid id "PK"
        uuid user_id "nullable FK to User"
        string query "max 500"
        integer results_count "default 0"
        float search_time_ms "nullable"
        string search_type "FULLTEXT, SEMANTIC, HYBRID, FUZZY"
        json filters_used "nullable"
        uuid clicked_book_id "nullable FK to Book"
        datetime created_at
    }

    AIModelVersion {
        uuid id "PK"
        string model_type "RECOMMENDATION, EMBEDDING, PREDICTION, NLP"
        string version_tag "max 100"
        string model_path "nullable, max 500"
        json metrics "nullable - evaluation scores"
        json parameters "nullable - hyperparameters"
        boolean is_active "default false"
        datetime trained_at "nullable"
        integer training_duration "seconds, nullable"
        integer training_samples "nullable"
        datetime created_at
        datetime updated_at
    }

    AIProviderConfig {
        uuid id "PK"
        string provider "OLLAMA, OPENAI, GEMINI, LOCAL_TRANSFORMERS"
        string capability "TEXT_GENERATION, EMBEDDING, CLASSIFICATION"
        string model_name "max 200"
        string api_endpoint "nullable, max 500"
        string api_key "nullable, encrypted, max 500"
        json extra_config "nullable"
        boolean is_active "default false"
        integer priority "default 0"
        integer max_tokens "default 2048"
        float temperature "default 0.7"
        datetime last_health_check "nullable"
        boolean is_healthy "default true"
        datetime created_at
        datetime updated_at
    }

    TrendingBook {
        uuid id "PK"
        uuid book_id "FK to Book, unique-per-period"
        string period "DAILY, WEEKLY, MONTHLY"
        float trend_score "default 0"
        integer view_count "default 0"
        integer borrow_count "default 0"
        integer search_count "default 0"
        integer review_count "default 0"
        datetime computed_at "auto_now"
        datetime created_at
        datetime updated_at
    }

    BookView {
        uuid id "PK"
        uuid user_id "nullable FK to User"
        uuid book_id "FK to Book"
        string source "CATALOG, SEARCH, RECOMMENDATION, TRENDING, DIRECT"
        integer duration_seconds "nullable"
        datetime viewed_at "auto_now_add"
        datetime created_at
    }

    Recommendation }o--|| User : "for user"
    Recommendation }o--|| Book : "recommends book"
    UserPreference }o--|| User : "preferences of"
    SearchLog }o--o| User : "searched by"
    TrendingBook }o--|| Book : "trending book"
    BookView }o--o| User : "viewed by"
    BookView }o--|| Book : "book viewed"
```

---

## 9. Governance Context

```mermaid
erDiagram
    AuditLog {
        uuid id "PK"
        uuid actor_id "nullable FK to User"
        string action "CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, ADMIN_ACTION"
        string resource_type "max 100"
        string resource_id "nullable, max 100"
        json changes "nullable - old/new values"
        string ip_address "nullable"
        string user_agent "nullable, max 500"
        string status "SUCCESS, FAILURE"
        text error_message "nullable"
        datetime created_at
    }

    SecurityEvent {
        uuid id "PK"
        string event_type "BRUTE_FORCE, SUSPICIOUS_ACCESS, RATE_LIMIT_EXCEEDED, INVALID_TOKEN, DATA_BREACH_ATTEMPT"
        string severity "LOW, MEDIUM, HIGH, CRITICAL"
        uuid user_id "nullable FK to User"
        string ip_address "nullable"
        text description
        json metadata "nullable"
        boolean is_resolved "default false"
        uuid resolved_by_id "nullable FK to User"
        datetime resolved_at "nullable"
        text resolution_notes "nullable"
        datetime created_at
    }

    KPLedger {
        uuid id "PK"
        uuid user_id "FK to User"
        string action "BOOK_BORROW, BOOK_RETURN, REVIEW_SUBMIT, STREAK_BONUS, ACHIEVEMENT, DAILY_LOGIN, ADMIN_AWARD, PENALTY"
        integer points "can be negative"
        integer balance_after
        text description "nullable"
        string dimension "nullable - KNOWLEDGE, ENGAGEMENT, CONTRIBUTION, EXPLORATION"
        uuid reference_id "nullable"
        string reference_type "nullable, max 100"
        datetime created_at
    }

    AuditLog }o--o| User : "actor"
    SecurityEvent }o--o| User : "related user"
    KPLedger }o--|| User : "user"
```

---

## 10. Asset Management Context

```mermaid
erDiagram
    AssetCategory {
        uuid id "PK"
        string name "max 200"
        string slug "unique, max 200"
        text description "nullable"
        datetime created_at
        datetime updated_at
    }

    Asset {
        uuid id "PK"
        string asset_tag "unique, max 50"
        string name "max 300"
        uuid category_id "FK to AssetCategory"
        string status "ACTIVE, MAINTENANCE, RETIRED, DISPOSED"
        string condition "NEW, GOOD, FAIR, POOR, DAMAGED"
        string location "nullable, max 200"
        string serial_number "nullable, max 100"
        string manufacturer "nullable, max 200"
        string model_number "nullable, max 100"
        date purchase_date "nullable"
        decimal purchase_price "nullable"
        decimal current_value "nullable"
        date warranty_expiry "nullable"
        text notes "nullable"
        datetime created_at
        datetime updated_at
    }

    MaintenanceLog {
        uuid id "PK"
        uuid asset_id "FK to Asset"
        string maintenance_type "PREVENTIVE, CORRECTIVE, INSPECTION"
        text description
        date performed_date
        decimal cost "nullable"
        string performed_by "max 200"
        date next_maintenance_date "nullable"
        text notes "nullable"
        datetime created_at
        datetime updated_at
    }

    AssetDisposal {
        uuid id "PK"
        uuid asset_id "FK to Asset, unique"
        string disposal_method "SOLD, DONATED, RECYCLED, DISCARDED"
        date disposal_date
        decimal disposal_value "nullable"
        text reason
        string approved_by "max 200"
        text notes "nullable"
        datetime created_at
        datetime updated_at
    }

    AssetCategory ||--o{ Asset : "categorizes"
    Asset ||--o{ MaintenanceLog : "maintained"
    Asset ||--o| AssetDisposal : "disposed"
```

---

## 11. HR Context

```mermaid
erDiagram
    Department {
        uuid id "PK"
        string name "max 200"
        string code "unique, max 20"
        text description "nullable"
        uuid head_id "nullable FK to Employee"
        boolean is_active "default true"
        datetime created_at
        datetime updated_at
    }

    Employee {
        uuid id "PK"
        uuid user_id "FK to User, unique"
        string employee_id "unique, max 20"
        uuid department_id "FK to Department"
        string position "max 200"
        string status "ACTIVE, ON_LEAVE, SUSPENDED, TERMINATED"
        date hire_date
        date termination_date "nullable"
        decimal salary "nullable"
        string employment_type "FULL_TIME, PART_TIME, CONTRACT, INTERN"
        string emergency_contact "nullable, max 200"
        string emergency_phone "nullable, max 20"
        text notes "nullable"
        datetime created_at
        datetime updated_at
    }

    JobVacancy {
        uuid id "PK"
        string title "max 300"
        uuid department_id "FK to Department"
        text description
        text requirements "nullable"
        string employment_type "FULL_TIME, PART_TIME, CONTRACT, INTERN"
        decimal salary_min "nullable"
        decimal salary_max "nullable"
        string status "OPEN, CLOSED, ON_HOLD, FILLED"
        date deadline "nullable"
        integer positions_available "default 1"
        datetime created_at
        datetime updated_at
    }

    JobApplication {
        uuid id "PK"
        uuid vacancy_id "FK to JobVacancy"
        string applicant_name "max 200"
        string applicant_email "max 255"
        string applicant_phone "nullable, max 20"
        string resume_path "nullable, max 500"
        text cover_letter "nullable"
        string status "SUBMITTED, REVIEWING, SHORTLISTED, INTERVIEWED, OFFERED, REJECTED, WITHDRAWN"
        text notes "nullable"
        uuid reviewed_by_id "nullable FK to User"
        datetime reviewed_at "nullable"
        datetime created_at
        datetime updated_at
    }

    Department ||--o{ Employee : "has employees"
    Department ||--o{ JobVacancy : "has vacancies"
    Department }o--o| Employee : "head"
    Employee }o--|| User : "linked user"
    JobVacancy ||--o{ JobApplication : "receives"
```

---

## 12. Cross-Context Relationship Summary

| Relationship | From Context | To Context | Cardinality | Description |
|-------------|-------------|------------|-------------|-------------|
| User → BorrowRecord | Identity | Circulation | 1:N | User borrows books |
| User → Reservation | Identity | Circulation | 1:N | User reserves books |
| User → Fine | Identity | Circulation | 1:N | User owes fines |
| User → BookReview | Identity | Catalog | 1:N | User writes reviews |
| User → ReadingSession | Identity | Digital Content | 1:N | User reads digitally |
| User → UserEngagement | Identity | Engagement | 1:1 | User engagement profile |
| User → Recommendation | Identity | Intelligence | 1:N | User gets recommendations |
| User → AuditLog | Identity | Governance | 1:N | User actions audited |
| User → Employee | Identity | HR | 1:1 | User is an employee |
| User → Member | Identity | Identity | 1:1 | User has membership |
| Book → BookCopy | Catalog | Catalog | 1:N | Book has physical copies |
| Book → DigitalAsset | Catalog | Digital Content | 1:N | Book has digital versions |
| Book → BorrowRecord | Catalog | Circulation | 1:N | Book is borrowed |
| Book → Reservation | Catalog | Circulation | 1:N | Book is reserved |
| Book → Recommendation | Catalog | Intelligence | 1:N | Book is recommended |
| Book → TrendingBook | Catalog | Intelligence | 1:N | Book trends |
| BookCopy → BorrowRecord | Catalog | Circulation | 1:N | Copy is lent |
| DigitalAsset → ReadingSession | Digital Content | Digital Content | 1:N | Asset has sessions |
| Achievement → UserAchievement | Engagement | Engagement | 1:N | Achievement instances |
| Department → Employee | HR | HR | 1:N | Department has employees |
| AssetCategory → Asset | Asset Mgmt | Asset Mgmt | 1:N | Category has assets |
