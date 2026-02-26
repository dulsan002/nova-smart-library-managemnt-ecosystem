# 04 — Class / UML Diagrams

> UML class diagrams per bounded context showing all attributes, methods, relationships, and inheritance

---

## 1. Abstract Base Classes (Common Module)

```mermaid
classDiagram
    class TimeStampedModel {
        <<abstract>>
        +DateTime created_at
        +DateTime updated_at
    }

    class UUIDModel {
        <<abstract>>
        +UUID id
    }

    class SoftDeletableModel {
        <<abstract>>
        +Boolean is_deleted
        +DateTime deleted_at
        +soft_delete() void
        +restore() void
    }

    class VersionedModel {
        <<abstract>>
        +Integer version
        +save() void
    }

    class SystemSetting {
        +UUID id
        +String key
        +String value
        +String value_type
        +String category
        +String description
        +Boolean is_secret
        +get_typed_value() Any
        +set_typed_value(value) void
    }

    class EventBus {
        <<singleton>>
        -Dict _handlers
        +subscribe(event_type, handler) void
        +publish(event) void
        +clear() void
    }

    UUIDModel --|> TimeStampedModel
    SoftDeletableModel --|> UUIDModel
    VersionedModel --|> UUIDModel
    SystemSetting --|> UUIDModel
```

---

## 2. Identity Context

```mermaid
classDiagram
    class User {
        +UUID id
        +String email
        +String password
        +String first_name
        +String last_name
        +String role
        +Boolean is_active
        +Boolean is_verified
        +Boolean is_staff
        +Boolean is_superuser
        +String phone
        +Date date_of_birth
        +String address
        +String avatar
        +String nic_number
        +JSON nic_data
        +Float face_encoding
        +String verification_status
        +DateTime date_joined
        +DateTime last_login
        +Integer failed_login_attempts
        +DateTime locked_until
        +get_full_name() String
        +is_admin() Boolean
        +is_librarian() Boolean
        +is_member() Boolean
        +is_locked() Boolean
        +record_failed_login() void
        +reset_failed_logins() void
    }

    class RoleConfig {
        +UUID id
        +String role_key
        +String display_name
        +JSON permissions
        +Boolean is_system
        +has_permission(module, action) Boolean
        +get_modules() List
    }

    class Member {
        +UUID id
        +User user
        +String membership_id
        +String membership_type
        +String status
        +Date start_date
        +Date expiry_date
        +String notes
        +Boolean auto_renew
        +is_expired() Boolean
        +is_active_member() Boolean
    }

    class VerificationRequest {
        +UUID id
        +User user
        +String request_type
        +String status
        +String id_document
        +String selfie
        +JSON extracted_data
        +Float confidence_score
        +String rejection_reason
        +User reviewed_by
        +DateTime reviewed_at
        +approve(reviewer) void
        +reject(reviewer, reason) void
    }

    class RefreshToken {
        +UUID id
        +User user
        +String token_hash
        +DateTime expires_at
        +Boolean is_revoked
        +String device_info
        +String ip_address
        +is_expired() Boolean
        +revoke() void
    }

    class PasswordResetToken {
        +UUID id
        +User user
        +String session_token
        +String otp_hash
        +Boolean otp_verified
        +Integer attempts
        +DateTime expires_at
        +verify_otp(otp) Boolean
        +is_expired() Boolean
    }

    User "1" --> "*" Member : has
    User "1" --> "*" VerificationRequest : submits
    User "1" --> "*" RefreshToken : has
    User "1" --> "*" PasswordResetToken : has
    User "*" --> "1" RoleConfig : role_key maps to
```

---

## 3. Catalog Context

```mermaid
classDiagram
    class Book {
        +UUID id
        +String title
        +String subtitle
        +String isbn_10
        +String isbn_13
        +String description
        +String language
        +Integer page_count
        +String publisher
        +Date publication_date
        +String cover_image
        +String edition
        +Decimal average_rating
        +Integer total_ratings
        +Integer total_borrows
        +JSON table_of_contents
        +String embedding_status
        +Boolean is_deleted
        +Integer version
        +available_copies_count() Integer
        +update_rating(new_rating) void
        +increment_borrows() void
        +soft_delete() void
    }

    class Author {
        +UUID id
        +String name
        +String biography
        +Date birth_date
        +Date death_date
        +String nationality
        +String photo
        +String website
        +book_count() Integer
    }

    class Category {
        +UUID id
        +String name
        +String slug
        +String description
        +Category parent
        +String icon
        +Integer sort_order
        +get_children() QuerySet
        +get_ancestors() List
        +is_root() Boolean
    }

    class BookCopy {
        +UUID id
        +Book book
        +String barcode
        +String status
        +String condition
        +String location
        +String shelf_number
        +Date acquisition_date
        +Decimal price
        +String notes
        +is_available() Boolean
        +mark_borrowed() void
        +mark_returned(condition) void
    }

    class BookReview {
        +UUID id
        +Book book
        +User user
        +Integer rating
        +String title
        +String content
        +Boolean is_approved
    }

    Book "*" --> "*" Author : authors
    Book "*" --> "*" Category : categories
    Book "1" --> "*" BookCopy : copies
    Book "1" --> "*" BookReview : reviews
    Category "0..1" --> "*" Category : children
```

---

## 4. Circulation Context

```mermaid
classDiagram
    class BorrowRecord {
        +UUID id
        +User user
        +Book book
        +BookCopy book_copy
        +Reservation reservation
        +String status
        +DateTime borrowed_at
        +DateTime due_date
        +DateTime returned_at
        +Integer renewal_count
        +Integer max_renewals
        +String condition_at_borrow
        +String condition_at_return
        +String notes
        +is_overdue() Boolean
        +can_renew() Boolean
        +renew() void
        +mark_returned(condition) void
        +days_remaining() Integer
    }

    class Reservation {
        +UUID id
        +User user
        +Book book
        +BookCopy book_copy
        +String status
        +DateTime reserved_at
        +DateTime expires_at
        +DateTime notified_at
        +Integer queue_position
        +String cancellation_reason
        +is_expired() Boolean
        +assign_copy(copy) void
        +mark_ready() void
        +fulfill() void
        +cancel(reason) void
    }

    class ReservationBan {
        +UUID id
        +User user
        +String reason
        +DateTime banned_at
        +DateTime expires_at
        +User banned_by
        +Boolean is_active
        +is_expired() Boolean
        +lift() void
    }

    class Fine {
        +UUID id
        +User user
        +BorrowRecord borrow_record
        +String fine_type
        +Decimal amount
        +Decimal paid_amount
        +String status
        +String description
        +DateTime issued_at
        +DateTime paid_at
        +User waived_by
        +String waiver_reason
        +remaining_amount() Decimal
        +pay(amount) void
        +waive(user, reason) void
        +is_fully_paid() Boolean
    }

    BorrowRecord "*" --> "1" User : borrowed by
    BorrowRecord "*" --> "1" Book : of book
    BorrowRecord "*" --> "1" BookCopy : specific copy
    BorrowRecord "0..1" --> "0..1" Reservation : from
    Reservation "*" --> "1" User : by user
    Reservation "*" --> "1" Book : for book
    ReservationBan "0..1" --> "1" User : bans
    Fine "*" --> "1" User : owed by
    Fine "*" --> "0..1" BorrowRecord : for
```

---

## 5. Digital Content Context

```mermaid
classDiagram
    class DigitalAsset {
        +UUID id
        +Book book
        +String asset_type
        +String file_path
        +Integer file_size
        +String mime_type
        +String format_details
        +Integer duration_seconds
        +Integer total_pages
        +String language
        +Boolean is_active
        +Integer download_count
        +is_ebook() Boolean
        +is_audiobook() Boolean
        +increment_downloads() void
    }

    class ReadingSession {
        +UUID id
        +User user
        +DigitalAsset digital_asset
        +String session_type
        +String device_type
        +String status
        +Float progress_percent
        +String current_position
        +DateTime started_at
        +DateTime ended_at
        +Integer duration_seconds
        +Integer pages_read
        +is_active() Boolean
        +end_session() void
        +update_progress(percent, position) void
    }

    class Bookmark {
        +UUID id
        +User user
        +DigitalAsset digital_asset
        +String title
        +String position
        +String note
        +String color
    }

    class Highlight {
        +UUID id
        +User user
        +DigitalAsset digital_asset
        +String text
        +String position_start
        +String position_end
        +String color
        +String note
    }

    class UserLibrary {
        +UUID id
        +User user
        +DigitalAsset digital_asset
        +Boolean is_favorite
        +Float last_progress
        +String last_position
        +DateTime last_accessed
        +DateTime added_at
        +toggle_favorite() void
        +update_progress(progress, position) void
    }

    DigitalAsset "*" --> "1" Book : digital of
    ReadingSession "*" --> "1" User : by
    ReadingSession "*" --> "1" DigitalAsset : reading
    Bookmark "*" --> "1" User : by
    Bookmark "*" --> "1" DigitalAsset : in
    Highlight "*" --> "1" User : by
    Highlight "*" --> "1" DigitalAsset : in
    UserLibrary "*" --> "1" User : library of
    UserLibrary "*" --> "1" DigitalAsset : contains
```

---

## 6. Engagement Context

```mermaid
classDiagram
    class UserEngagement {
        +UUID id
        +User user
        +Integer total_kp
        +Integer level
        +Integer books_read
        +Integer reviews_written
        +Integer reading_streak
        +Integer longest_streak
        +Date last_activity_date
        +Integer total_reading_time
        +String reading_tier
        +JSON dimension_scores
        +award_kp(points) void
        +update_streak() void
        +recalculate_tier() void
        +recalculate_level() void
    }

    class Achievement {
        +UUID id
        +String name
        +String slug
        +String description
        +String icon
        +String category
        +String tier
        +Integer kp_reward
        +JSON criteria
        +Boolean is_active
        +Integer sort_order
        +check_eligibility(user) Boolean
    }

    class UserAchievement {
        +UUID id
        +User user
        +Achievement achievement
        +DateTime earned_at
        +Integer progress
        +String context
    }

    class DailyActivity {
        +UUID id
        +User user
        +Date activity_date
        +Integer pages_read
        +Integer reading_minutes
        +Integer books_completed
        +Integer reviews_written
        +Integer kp_earned
        +Integer sessions_count
        +JSON activity_details
    }

    UserEngagement "1" --> "1" User : profile of
    UserAchievement "*" --> "1" User : earned by
    UserAchievement "*" --> "1" Achievement : instance of
    DailyActivity "*" --> "1" User : activity of
```

---

## 7. Intelligence Context

```mermaid
classDiagram
    class Recommendation {
        +UUID id
        +User user
        +Book book
        +Float score
        +String strategy
        +String reason
        +Boolean is_clicked
        +Boolean is_dismissed
        +DateTime generated_at
        +DateTime expires_at
        +mark_clicked() void
        +dismiss() void
        +is_expired() Boolean
    }

    class UserPreference {
        +UUID id
        +User user
        +JSON preferred_categories
        +JSON preferred_authors
        +JSON preferred_languages
        +String reading_pace
        +String content_length_pref
        +JSON topic_interests
        +Boolean notify_new_releases
        +Boolean notify_recommendations
        +JSON preference_vector
        +update_vector() void
    }

    class SearchLog {
        +UUID id
        +User user
        +String query
        +Integer results_count
        +Float search_time_ms
        +String search_type
        +JSON filters_used
        +Book clicked_book
    }

    class AIModelVersion {
        +UUID id
        +String model_type
        +String version_tag
        +String model_path
        +JSON metrics
        +JSON parameters
        +Boolean is_active
        +DateTime trained_at
        +Integer training_duration
        +Integer training_samples
        +activate() void
        +deactivate() void
    }

    class AIProviderConfig {
        +UUID id
        +String provider
        +String capability
        +String model_name
        +String api_endpoint
        +String api_key
        +JSON extra_config
        +Boolean is_active
        +Integer priority
        +Integer max_tokens
        +Float temperature
        +DateTime last_health_check
        +Boolean is_healthy
        +activate() void
        +health_check() Boolean
    }

    class TrendingBook {
        +UUID id
        +Book book
        +String period
        +Float trend_score
        +Integer view_count
        +Integer borrow_count
        +Integer search_count
        +Integer review_count
        +DateTime computed_at
    }

    class BookView {
        +UUID id
        +User user
        +Book book
        +String source
        +Integer duration_seconds
        +DateTime viewed_at
    }

    class SearchEngine {
        <<service>>
        +search(query, filters) SearchResponse
        +auto_suggest(prefix, limit) List
        -fulltext_search(query) QuerySet
        -semantic_search(query) QuerySet
        -fuzzy_search(query) QuerySet
        -merge_results(results, weights) List
        -build_facets(results) Facets
    }

    class RecommendationEngine {
        <<service>>
        +generate(user) List
        -collaborative_filter(user) List
        -content_based(user) List
        -hybrid(user) List
        -score_and_rank(books) List
    }

    class PredictiveAnalytics {
        <<service>>
        +predict_overdue(borrows) List
        +forecast_demand(books) List
        +predict_churn(users) List
        +analyze_collection_gaps() List
    }

    Recommendation "*" --> "1" User : for
    Recommendation "*" --> "1" Book : recommends
    UserPreference "1" --> "1" User : of
    SearchLog "*" --> "0..1" User : by
    TrendingBook "*" --> "1" Book : book
    BookView "*" --> "0..1" User : by
    BookView "*" --> "1" Book : viewed
    SearchEngine ..> SearchLog : logs
    RecommendationEngine ..> Recommendation : creates
    RecommendationEngine ..> UserPreference : reads
```

---

## 8. Governance Context

```mermaid
classDiagram
    class AuditLog {
        +UUID id
        +User actor
        +String action
        +String resource_type
        +String resource_id
        +JSON changes
        +String ip_address
        +String user_agent
        +String status
        +String error_message
        +DateTime created_at
    }

    class SecurityEvent {
        +UUID id
        +String event_type
        +String severity
        +User user
        +String ip_address
        +String description
        +JSON metadata
        +Boolean is_resolved
        +User resolved_by
        +DateTime resolved_at
        +String resolution_notes
        +resolve(user, notes) void
    }

    class KPLedger {
        +UUID id
        +User user
        +String action
        +Integer points
        +Integer balance_after
        +String description
        +String dimension
        +UUID reference_id
        +String reference_type
    }

    AuditLog "*" --> "0..1" User : actor
    SecurityEvent "*" --> "0..1" User : related
    SecurityEvent "*" --> "0..1" User : resolved_by
    KPLedger "*" --> "1" User : for
```

---

## 9. Asset Management Context

```mermaid
classDiagram
    class AssetCategory {
        +UUID id
        +String name
        +String slug
        +String description
        +asset_count() Integer
    }

    class Asset {
        +UUID id
        +String asset_tag
        +String name
        +AssetCategory category
        +String status
        +String condition
        +String location
        +String serial_number
        +String manufacturer
        +String model_number
        +Date purchase_date
        +Decimal purchase_price
        +Decimal current_value
        +Date warranty_expiry
        +String notes
        +is_under_warranty() Boolean
        +depreciation() Decimal
    }

    class MaintenanceLog {
        +UUID id
        +Asset asset
        +String maintenance_type
        +String description
        +Date performed_date
        +Decimal cost
        +String performed_by
        +Date next_maintenance_date
        +String notes
    }

    class AssetDisposal {
        +UUID id
        +Asset asset
        +String disposal_method
        +Date disposal_date
        +Decimal disposal_value
        +String reason
        +String approved_by
        +String notes
    }

    AssetCategory "1" --> "*" Asset : categorizes
    Asset "1" --> "*" MaintenanceLog : maintenance
    Asset "1" --> "0..1" AssetDisposal : disposal
```

---

## 10. HR Context

```mermaid
classDiagram
    class Department {
        +UUID id
        +String name
        +String code
        +String description
        +Employee head
        +Boolean is_active
        +employee_count() Integer
        +active_vacancies() QuerySet
    }

    class Employee {
        +UUID id
        +User user
        +String employee_id
        +Department department
        +String position
        +String status
        +Date hire_date
        +Date termination_date
        +Decimal salary
        +String employment_type
        +String emergency_contact
        +String emergency_phone
        +String notes
        +tenure_years() Float
        +is_active() Boolean
    }

    class JobVacancy {
        +UUID id
        +String title
        +Department department
        +String description
        +String requirements
        +String employment_type
        +Decimal salary_min
        +Decimal salary_max
        +String status
        +Date deadline
        +Integer positions_available
        +is_open() Boolean
        +application_count() Integer
    }

    class JobApplication {
        +UUID id
        +JobVacancy vacancy
        +String applicant_name
        +String applicant_email
        +String applicant_phone
        +String resume_path
        +String cover_letter
        +String status
        +String notes
        +User reviewed_by
        +DateTime reviewed_at
    }

    Department "1" --> "*" Employee : employs
    Department "1" --> "*" JobVacancy : posts
    Department "0..1" --> "0..1" Employee : headed by
    Employee "1" --> "1" User : is user
    JobVacancy "1" --> "*" JobApplication : receives
```

---

## 11. Inheritance Hierarchy

```mermaid
classDiagram
    class Model {
        <<Django>>
    }

    class AbstractBaseUser {
        <<Django>>
    }

    class TimeStampedModel {
        <<abstract>>
    }

    class UUIDModel {
        <<abstract>>
    }

    class SoftDeletableModel {
        <<abstract>>
    }

    class VersionedModel {
        <<abstract>>
    }

    Model <|-- TimeStampedModel
    TimeStampedModel <|-- UUIDModel
    UUIDModel <|-- SoftDeletableModel
    UUIDModel <|-- VersionedModel
    AbstractBaseUser <|-- User

    SoftDeletableModel <|-- Book
    SoftDeletableModel <|-- Member

    VersionedModel <|-- BookReview

    UUIDModel <|-- Author
    UUIDModel <|-- Category
    UUIDModel <|-- BookCopy
    UUIDModel <|-- BorrowRecord
    UUIDModel <|-- Reservation
    UUIDModel <|-- Fine
    UUIDModel <|-- DigitalAsset
    UUIDModel <|-- ReadingSession
    UUIDModel <|-- Bookmark
    UUIDModel <|-- Highlight
    UUIDModel <|-- UserLibrary
    UUIDModel <|-- UserEngagement
    UUIDModel <|-- Achievement
    UUIDModel <|-- UserAchievement
    UUIDModel <|-- DailyActivity
    UUIDModel <|-- Recommendation
    UUIDModel <|-- UserPreference
    UUIDModel <|-- AIModelVersion
    UUIDModel <|-- AIProviderConfig
    UUIDModel <|-- TrendingBook
    UUIDModel <|-- Asset
    UUIDModel <|-- AssetCategory
    UUIDModel <|-- MaintenanceLog
    UUIDModel <|-- AssetDisposal
    UUIDModel <|-- Department
    UUIDModel <|-- Employee
    UUIDModel <|-- JobVacancy
    UUIDModel <|-- JobApplication
```
