# Nova Smart Library Management Ecosystem — User Manual

**Version:** 1.0  
**Last Updated:** February 2026  
**System:** Nova Smart Library Management Ecosystem

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Requirements](#2-system-requirements)
3. [Getting Started](#3-getting-started)
   - 3.1 [Creating an Account](#31-creating-an-account)
   - 3.2 [Logging In](#32-logging-in)
   - 3.3 [Password Recovery](#33-password-recovery)
   - 3.4 [Understanding User Roles](#34-understanding-user-roles)
4. [Dashboard](#4-dashboard)
5. [Catalog & Book Discovery](#5-catalog--book-discovery)
   - 5.1 [Browsing the Catalog](#51-browsing-the-catalog)
   - 5.2 [Searching for Books](#52-searching-for-books)
   - 5.3 [Book Detail Page](#53-book-detail-page)
   - 5.4 [Writing Reviews](#54-writing-reviews)
6. [Circulation — Borrowing Books](#6-circulation--borrowing-books)
   - 6.1 [How Borrowing Works](#61-how-borrowing-works)
   - 6.2 [Reserving a Book](#62-reserving-a-book)
   - 6.3 [Picking Up a Reserved Book](#63-picking-up-a-reserved-book)
   - 6.4 [Viewing Your Borrows](#64-viewing-your-borrows)
   - 6.5 [Renewing a Borrow](#65-renewing-a-borrow)
   - 6.6 [Returning a Book](#66-returning-a-book)
   - 6.7 [Fines & Payments](#67-fines--payments)
   - 6.8 [Reservation Policies & Bans](#68-reservation-policies--bans)
7. [Digital Library](#7-digital-library)
   - 7.1 [Your Digital Collection](#71-your-digital-collection)
   - 7.2 [Reading E-Books](#72-reading-e-books)
   - 7.3 [Listening to Audiobooks](#73-listening-to-audiobooks)
   - 7.4 [Bookmarks & Highlights](#74-bookmarks--highlights)
   - 7.5 [Reading Progress & Sessions](#75-reading-progress--sessions)
8. [Knowledge Points & Gamification](#8-knowledge-points--gamification)
   - 8.1 [KP Center Overview](#81-kp-center-overview)
   - 8.2 [How to Earn Knowledge Points](#82-how-to-earn-knowledge-points)
   - 8.3 [Levels & Progression](#83-levels--progression)
   - 8.4 [Streaks & Multipliers](#84-streaks--multipliers)
   - 8.5 [Achievements & Badges](#85-achievements--badges)
   - 8.6 [Leaderboard](#86-leaderboard)
9. [Intelligence & AI Features](#9-intelligence--ai-features)
   - 9.1 [Personalized Recommendations](#91-personalized-recommendations)
   - 9.2 [AI-Powered Search](#92-ai-powered-search)
   - 9.3 [Reading Insights](#93-reading-insights)
   - 9.4 [Notifications](#94-notifications)
10. [Profile Management](#10-profile-management)
    - 10.1 [Editing Your Profile](#101-editing-your-profile)
    - 10.2 [Changing Your Password](#102-changing-your-password)
    - 10.3 [Identity Verification Status](#103-identity-verification-status)
11. [Administration Guide](#11-administration-guide)
    - 11.1 [Admin Dashboard](#111-admin-dashboard)
    - 11.2 [User Management](#112-user-management)
    - 11.3 [Member Management](#113-member-management)
    - 11.4 [Book Management](#114-book-management)
    - 11.5 [Author Management](#115-author-management)
    - 11.6 [Digital Content Management](#116-digital-content-management)
    - 11.7 [Circulation Management](#117-circulation-management)
    - 11.8 [Roles & Permissions (RBAC)](#118-roles--permissions-rbac)
    - 11.9 [Audit Logs & Security Events](#119-audit-logs--security-events)
    - 11.10 [Analytics & Predictive Intelligence](#1110-analytics--predictive-intelligence)
    - 11.11 [AI Provider Configuration](#1111-ai-provider-configuration)
    - 11.12 [Asset Management](#1112-asset-management)
    - 11.13 [Human Resources (HR)](#1113-human-resources-hr)
    - 11.14 [System Settings](#1114-system-settings)
    - 11.15 [Email / SMTP Configuration](#1115-email--smtp-configuration)
12. [Circulation & Fine Policies](#12-circulation--fine-policies)
13. [Keyboard Shortcuts & Tips](#13-keyboard-shortcuts--tips)
14. [Security & Privacy](#14-security--privacy)
15. [Troubleshooting & FAQ](#15-troubleshooting--faq)
16. [Glossary](#16-glossary)

---

## 1. Introduction

**Nova Smart Library Management Ecosystem** is an AI-powered, next-generation library management system designed to transform how libraries operate and how patrons interact with library services. It integrates physical and digital library operations, knowledge gamification, AI-driven personalized recommendations, and comprehensive administrative tools into a single cohesive platform.

### Key Capabilities

| Capability | Description |
|---|---|
| **Catalog Management** | Browse, search, and manage a comprehensive collection of physical and digital books |
| **Smart Circulation** | Reservation-first borrowing with automated fine management and overdue tracking |
| **Digital Library** | Built-in e-book reader and audiobook player with progress tracking |
| **AI-Powered Search** | Hybrid search combining full-text, semantic, and fuzzy matching with natural language AI answers |
| **Knowledge Points (KP)** | Gamification system with levels, achievements, streaks, and leaderboards |
| **Personalized Recommendations** | AI-driven book suggestions based on reading history and preferences |
| **Reading Insights** | Personal analytics on reading speed, session patterns, and engagement |
| **AI Identity Verification** | Automated NIC (National Identity Card) OCR and face recognition during registration |
| **Asset Management** | Track and manage physical library assets (furniture, equipment, computers) |
| **HR Management** | Department, employee, vacancy, and job application management |
| **Governance & Audit** | Immutable audit logs, security event monitoring, and KP transaction ledger |
| **Role-Based Access Control** | Dynamic RBAC with customizable permission matrices |

### Who This Manual Is For

- **Library Patrons (Users)** — Browse catalog, borrow books, read digital content, earn KP
- **Library Assistants** — Help with stock management and basic circulation processing
- **Librarians** — Full circulation management, content management, analytics access
- **Super Administrators** — Complete system control including security, HR, AI configuration, and settings

---

## 2. System Requirements

### For End Users (Browser)

| Requirement | Minimum |
|---|---|
| **Browser** | Chrome 90+, Firefox 88+, Safari 15+, Edge 90+ |
| **JavaScript** | Must be enabled |
| **Screen Resolution** | 1024×768 minimum (responsive design supports mobile) |
| **Internet Connection** | Broadband recommended for digital content streaming |

### For System Administrators (Server)

| Component | Requirement |
|---|---|
| **Python** | 3.11+ |
| **Node.js** | 18+ (for frontend build) |
| **PostgreSQL** | 15+ with pgvector extension |
| **Redis** | 7+ (cache, sessions, task broker) |
| **Ollama** | Latest (for local LLM — llama3.1) |
| **OS** | Linux (Ubuntu 22.04+ recommended) |

---

## 3. Getting Started

### 3.1 Creating an Account

Nova uses a **3-step registration wizard** with AI-powered identity verification.

#### Step 1 — Personal Information

1. Navigate to the registration page by clicking **"Create an account"** on the login page
2. Fill in the required fields:
   - **First Name** and **Last Name**
   - **Email Address** (must be unique; this will be your login credential)
   - **Password** — Must meet the following requirements:
     - Minimum 8 characters
     - At least one uppercase letter
     - At least one number
     - At least one special character
   - A **password strength meter** will display real-time feedback (Weak / Fair / Good / Strong)
   - **Phone Number** (optional)
   - **Date of Birth** (optional)
3. Click **"Continue"** to proceed

#### Step 2 — NIC Verification (Identity Verification)

This step uses AI to verify your identity using your National Identity Card (NIC).

1. **Upload NIC Front Image** — Click the upload area or drag-and-drop the front side of your NIC
   - Accepted formats: JPEG, PNG
   - Maximum file size: 10 MB
2. **Upload NIC Back Image** — Upload the back side of your NIC
3. **Enter NIC Number** — Type your NIC number exactly as it appears on the card
4. Click **"Verify NIC"** — The system will:
   - Perform **OCR (Optical Character Recognition)** to extract text from your NIC photos
   - Match the extracted name against your entered name (fuzzy matching)
   - Match the extracted NIC number against your entered NIC number
   - Display verification results with **match scores**
5. If verification succeeds, click **"Continue"**
6. If verification fails, you may re-upload clearer photos or correct your NIC number

> **Note:** Verification may be queued for manual review by a librarian if the AI confidence score is below the threshold. Your account will still be created but some features may be restricted until verification is approved.

#### Step 3 — Review & Submit

1. Review all entered information
2. Click **"Create Account"** to complete registration
3. You will be redirected to the login page

### 3.2 Logging In

1. Navigate to the login page (`/login`)
2. Enter your **Email** and **Password**
3. Optionally check **"Remember me"** to stay logged in
4. Click **"Sign In"**
5. On successful login:
   - **Regular users** are directed to the **Member Dashboard** (`/dashboard`)
   - **Admin users** (Librarian, Assistant, Super Admin) are directed to the **Admin Dashboard** (`/admin/dashboard`)

> **Security:** After 5 consecutive failed login attempts, your account will be temporarily locked for 5 minutes. Each subsequent failed attempt doubles the lockout duration (up to a maximum of 1 hour).

### 3.3 Password Recovery

If you forget your password, Nova provides a secure 3-step OTP-based recovery process:

#### Step 1 — Request Reset

1. Click **"Forgot password?"** on the login page
2. Enter the **email address** associated with your account
3. Click **"Send Reset Code"**
4. A **6-digit OTP (One-Time Password)** will be sent to your email

#### Step 2 — Verify OTP

1. Enter the **6-digit OTP** received in your email
   - The OTP input provides 6 individual boxes for easy entry
   - You can paste the full code at once
   - The OTP expires after **10 minutes**
2. Click **"Verify Code"**

#### Step 3 — Set New Password

1. Enter your **new password** (same strength requirements as registration)
2. **Confirm** the new password
3. A password strength meter guides you
4. Click **"Reset Password"**
5. You will be redirected to the login page with a success message

### 3.4 Understanding User Roles

Nova has four built-in user roles, each with different levels of access:

| Role | Access Level | Description |
|---|---|---|
| **User** | Standard | Browse catalog, borrow/reserve books, access digital library, earn KP, view recommendations and insights |
| **Assistant** | Elevated | All User permissions + manage stock, process borrows/returns, view borrows |
| **Librarian** | Management | All Assistant permissions + full book/author/copy management, digital content uploads, fine management, verification reviews, analytics, HR, asset management |
| **Super Admin** | Full Control | All Librarian permissions + user management, role configuration, audit logs, security events, AI provider configuration, system settings, SMTP setup |

> **Dynamic Permissions:** Super Admins can create custom roles with fine-grained permissions using the Roles & Permissions panel (see [Section 11.8](#118-roles--permissions-rbac)).

---

## 4. Dashboard

The **Member Dashboard** (`/dashboard`) is your personalized home page that displays everything relevant to your library activity at a glance.

### What You'll See

| Section | Description |
|---|---|
| **Greeting Banner** | Time-based greeting (Good morning/afternoon/evening) with your name |
| **Streak Indicator** | A flame icon showing your current reading streak |
| **KP Badge** | Your current Knowledge Points total and level |
| **Quick Stats** | Active borrows, digital books, weekly KP earned, reading time |
| **Continue Reading/Listening** | Resume your in-progress e-books or audiobooks right from the dashboard |
| **Active Borrows** | Your currently borrowed books with due dates |
| **Overdue Warning** | Any overdue books are prominently highlighted |
| **KP Progress Bar** | Visual indicator of your progress toward the next level |
| **Quick Actions** | Shortcut buttons to common tasks (Browse Catalog, My Borrows, Digital Library) |
| **Trending Books** | Currently popular books across the library |
| **AI Recommendations** | Personalized book suggestions from the AI recommendation engine |
| **Recent Activity** | Your latest borrows and returns |

### Navigation

The **left sidebar** provides access to all sections:

| Section | Menu Items |
|---|---|
| **Main** | Dashboard, Catalog, Search |
| **Circulation** | My Borrows, Reservations, Fines |
| **Digital** | Digital Library |
| **Engagement** | KP Center, Achievements, Leaderboard |
| **Intelligence** | Recommendations, Notifications, Insights |

The sidebar can be **collapsed** to icon-only mode by clicking the collapse button at the bottom. On mobile devices, the sidebar slides out as an overlay.

### Header Bar

- **Quick Search** — Search bar with `⌘K` / `Ctrl+K` keyboard shortcut
- **Theme Toggle** — Switch between dark and light mode (preference persisted)
- **Notifications** — Bell icon with unread count (polled every 30 seconds)
- **User Menu** — Click your avatar to access Profile, Settings, and Sign Out

---

## 5. Catalog & Book Discovery

### 5.1 Browsing the Catalog

The **Catalog** page (`/catalog`) is the primary way to discover books in the library's collection.

#### Layout

- **Hero Banner** — Displays the total book count in the collection
- **Search Bar** — Type to filter books in real-time (400ms debounce)
- **Quick Filter Pills** — One-click filters:
  - **All** — Show all books
  - **Available Now** — Only books with available physical copies
  - **New Arrivals** — Recently added books
  - **Most Popular** — Sorted by borrow count
  - **Top Rated** — Sorted by reader ratings

#### Filtering Options

The left sidebar provides advanced filters:

| Filter | Options |
|---|---|
| **Categories** | Hierarchical category tree (expandable parent → child categories) |
| **Language** | Filter by book language |
| **Active Filters** | Chip-style display of all active filters with individual removal |

#### Display Options

- **Grid View** — Card-based layout with cover images
- **List View** — Compact list with more details per row
- **Sort By** — Newest First, Most Popular, Top Rated, Title (A–Z)
- **Pagination** — Cursor-based navigation (Next/Previous)

#### Book Cards

Each book card shows:
- Cover image
- Title and author(s)
- Star rating (if reviews exist)
- Format badges: **Physical**, **E-Book**, **Audiobook** (based on availability)

### 5.2 Searching for Books

The **Search** page (`/search`) provides an advanced AI-powered hybrid search experience.

#### How to Search

1. Navigate to `/search` or use the `⌘K` / `Ctrl+K` shortcut
2. Type your search query in the search bar
3. **Auto-suggestions** appear as you type (up to 8 suggestions, 300ms debounce)
4. Press **Enter** or click a suggestion to execute the search

#### Search Results

The system executes two types of search simultaneously:

| Search Type | Weight | Description |
|---|---|---|
| **Full-Text Search** | 45% | Traditional keyword matching against titles, descriptions, ISBNs |
| **Semantic Search** | 35% | AI embedding-based meaning matching (understands concepts, not just words) |
| **Fuzzy Search** | 20% | Handles typos and approximate matches |
| **Personalization Boost** | Bonus | Results weighted by your reading history and preferences |

**AI Answer Panel** — If AI search is enabled, you'll also see:
- A natural language answer to your query from the AI model
- Referenced books cited by the AI
- The AI model name used

#### Pre-filled Suggestions

For new users or when the search bar is empty, the page shows suggestion chips like:
- "Recommend a good sci-fi book"
- "Best books about machine learning"
- "Popular fiction this month"

### 5.3 Book Detail Page

Click any book to view its full detail page (`/catalog/:bookId`).

#### Information Displayed

| Section | Content |
|---|---|
| **Header** | Cover image, title, subtitle, author(s) (linked), star rating |
| **Metadata Grid** | Publication date, language, ISBN-10/13, page count, publisher |
| **Format Availability** | Physical copies (available/total), E-Book, Audiobook badges |
| **Reservation Widget** | Reserve a Copy / Join Waitlist button (see [Section 6](#6-circulation--borrowing-books)) |
| **Tabs** | Description, Authors, Digital Formats, Reviews, Physical Copies |

#### Tabs

- **Description** — Full book description, tags, publisher info, classification, statistics (total borrows, current borrows, ratings count)
- **Authors** — Author biography, nationality, photo, and list of other books by the same author
- **Digital Formats** — Links to read the e-book or listen to the audiobook (if available)
- **Reviews** — Reader reviews with star ratings; submit your own review (1–5 stars, title, and text)
- **Physical Copies** — Table showing each physical copy with its barcode, condition, status, and shelf location

### 5.4 Writing Reviews

1. Navigate to a book's detail page
2. Scroll to the **Reviews** tab
3. Click the **star rating** (1–5 stars)
4. Enter a **review title**
5. Write your **review text**
6. Click **"Submit Review"**

> **Note:** You can only submit one review per book. Your review will be visible to all users.

---

## 6. Circulation — Borrowing Books

### 6.1 How Borrowing Works

Nova uses a **reservation-first** borrowing system. You cannot directly check out a book — instead, you first reserve a copy, then pick it up at the library.

**The Flow:**

```
Reserve a Copy → Copy Assigned (if available) → Pick Up at Library → Librarian Confirms → Book Borrowed → Read & Enjoy → Return to Library
```

### 6.2 Reserving a Book

1. Navigate to the book's detail page (`/catalog/:bookId`)
2. Click **"Reserve a Copy"** (or **"Join Waitlist"** if no copies are currently available)
3. The system checks:
   - You have fewer than **2 active borrows** (limit: 2 concurrent borrows)
   - You have fewer than **2 active reservations** (limit: 2 concurrent reservations)
   - You are not currently under a **reservation ban**
   - You don't have excessive unpaid fines (threshold: $25.00)
4. If all checks pass, a reservation is created:
   - **If copies are available:** Status = `READY`, a specific copy is assigned, and a **12-hour pickup window** begins
   - **If no copies available:** Status = `PENDING`, you join the waitlist with a queue position number

#### Reservation Status Card

Once reserved, the book detail page shows a status card with:
- Current reservation status (PENDING / READY)
- Queue position (if waitlisted)
- Pickup deadline (if ready)
- Assigned copy location (branch, floor, shelf)
- **Cancel Reservation** button

### 6.3 Picking Up a Reserved Book

1. When your reservation status is **READY**, visit the library within the **12-hour pickup window**
2. Present yourself at the circulation desk
3. The librarian will **confirm pickup** in the system
4. Your reservation is converted to an **active borrow record**
5. The default loan period is **14 days**

> **Important:** If you do not pick up within 12 hours, the reservation **expires automatically**, the copy is released back to the pool, and a no-show is recorded against your account.

### 6.4 Viewing Your Borrows

Navigate to **My Borrows** (`/borrows`) to see all your borrowing activity.

The page has **three tabs**:

| Tab | Shows |
|---|---|
| **Reservations** | Active reservations (PENDING/READY) with cancel option, pickup location, and time remaining |
| **Active** | Currently borrowed books (ACTIVE/OVERDUE) with due dates, renew button, and days overdue |
| **History** | Past borrows (RETURNED/LOST) — read-only |

A **reservation ban warning** banner appears at the top if you are currently banned from making reservations.

### 6.5 Renewing a Borrow

You can extend your borrow period if you need more time:

1. Go to **My Borrows** → **Active** tab
2. Click **"Renew"** on the borrow you want to extend
3. Each renewal extends the due date by another **14 days**
4. You can renew a maximum of **2 times** per borrow
5. You **cannot renew** if the book is already overdue

### 6.6 Returning a Book

1. Bring the physical book to the library's circulation desk
2. Hand it to the librarian
3. The librarian processes the return in the system
4. The book's status is updated to **RETURNED**
5. If returned after the due date, an **overdue fine** is automatically generated

### 6.7 Fines & Payments

Navigate to **My Fines** (`/fines`) to view and manage your fines.

#### Fine Types

| Type | Description |
|---|---|
| **OVERDUE** | Charged when a book is returned past its due date |
| **LOST** | Charged when a book is declared lost |
| **DAMAGE** | Charged for damaged physical copies |

#### Fine Rates (Escalating)

| Period | Daily Rate |
|---|---|
| Days 1–7 overdue | $0.50 / day |
| Days 8–30 overdue | $0.75 / day (1.5× base rate) |
| Days 31+ overdue | $1.00 / day (2× base rate) |

#### Paying Fines

1. Go to **My Fines** (`/fines`)
2. View your outstanding fines with total amount
3. Click **"Pay Now"** on a specific fine
4. Fines can also be **waived** by a librarian (e.g., for legitimate reasons)

> **Important:** If your total unpaid fines exceed **$25.00**, you will be **blocked from making new reservations** until fines are reduced below the threshold.

#### Fine Statuses

| Status | Meaning |
|---|---|
| **PENDING** | Fine is outstanding and unpaid |
| **PAID** | Fine has been paid in full |
| **WAIVED** | Fine has been waived by a librarian |
| **PARTIALLY_PAID** | Part of the fine has been paid |

### 6.8 Reservation Policies & Bans

To prevent abuse of the reservation system:

| Policy | Value |
|---|---|
| Maximum concurrent borrows | **2** |
| Maximum concurrent reservations | **2** |
| Pickup window | **12 hours** from reservation ready |
| No-show lookback period | 30 days |
| Maximum no-shows before ban | **3** within 30 days |
| Ban duration | **7 days** |

If you accumulate **3 expired (no-show) reservations within 30 days**, the system automatically places a **7-day reservation ban** on your account. During this ban:
- You cannot make new reservations
- A warning banner appears on your borrows page
- Your existing active borrows are not affected

---

## 7. Digital Library

### 7.1 Your Digital Collection

The **Digital Library** page (`/library`) is your personal digital reading hub.

#### Page Layout

- **Continue Reading/Listening** — Hero carousel showing your in-progress books with a "Continue" button
- **Library Stats** — Total digital books, hours read, books finished
- **Tabs**:
  - **All** — All digital content
  - **E-Books** — E-books only
  - **Audiobooks** — Audiobooks only
  - **Favorites** — Your favorited items
  - **History** — Previously read/listened items

#### Features

- **Grid / List View** toggle
- **Sort** by: Recent Activity, Title, Progress
- **Filter** by status: In Progress, Finished, New
- **Favorite Toggle** — Click the heart icon to add/remove from favorites
- **Progress Ring** — Visual arc showing completion percentage
- **Time Spent** — Total time you've spent reading/listening to each book

### 7.2 Reading E-Books

Click on an e-book to open the **Reader** (`/reader/:assetId`).

#### Reader Interface

| Control | Description |
|---|---|
| **Toolbar** | Book title, bookmark button, highlight button, side panel toggle |
| **Page Navigation** | Click left/right sides of the page or use ← → arrow keys |
| **Progress Bar** | Bottom bar showing current page / total pages |
| **Bookmark** | Click the bookmark icon to bookmark the current page |
| **Highlight** | Select text with your mouse, then click highlight to save the selection |
| **Side Panel** | Lists all your bookmarks and highlights for quick navigation |

#### Keyboard Navigation

| Key | Action |
|---|---|
| `←` Left Arrow | Previous page |
| `→` Right Arrow | Next page |

#### Progress Saving

Your reading progress is automatically saved:
- On every page turn
- Every 30 seconds while reading
- When you switch browser tabs
- When you close the browser window (via background beacon)
- You can resume from exactly where you left off across sessions and devices

### 7.3 Listening to Audiobooks

Click on an audiobook to open the **Audiobook Player** (`/listen/:assetId`).

#### Player Interface

| Control | Description |
|---|---|
| **Cover Art** | Large cover image display |
| **Play / Pause** | Central play/pause button |
| **Seek Bar** | Drag to jump to a specific position |
| **Skip Backward** | Jump back 15 seconds |
| **Skip Forward** | Jump forward 30 seconds |
| **Playback Speed** | Adjust speed: 0.5×, 0.75×, 1×, 1.25×, 1.5×, 2×, 2.5×, 3× |
| **Sleep Timer** | Auto-pause after: 15, 30, 45, 60, or 90 minutes |
| **Bookmark** | Save the current audio position with an optional note |

#### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause toggle |
| `←` Left Arrow | Skip backward 15s |
| `→` Right Arrow | Skip forward 30s |

#### Progress Saving

Same automatic progress saving as the e-book reader — saves every 30 seconds, on tab switch, and on window close.

### 7.4 Bookmarks & Highlights

#### Bookmarks
- **E-Books:** Bookmark specific pages
- **Audiobooks:** Bookmark specific time positions with optional notes
- View all bookmarks in the **side panel** of the reader/player
- Click a bookmark to jump directly to that position
- Bookmarks support **color coding**

#### Highlights (E-Books Only)
- Select text in the e-book reader
- Click the highlight button to save the selection
- Highlights include the selected text, start/end position
- View all highlights in the side panel
- Click a highlight to jump to that passage

### 7.5 Reading Progress & Sessions

Every time you open a digital book, a **reading session** is tracked:
- Session type: **READING** (e-books) or **LISTENING** (audiobooks)
- Duration and progress percentage are recorded
- Sessions earn **Knowledge Points** (minimum 2 minutes of reading)
- Device information is logged for cross-device sync

View your active and past sessions from the dashboard's **"Continue Reading/Listening"** widget.

---

## 8. Knowledge Points & Gamification

Nova includes a comprehensive **Knowledge Points (KP)** gamification system that rewards your reading and engagement activities.

### 8.1 KP Center Overview

Access the **KP Center** (`/kp-center`) for a complete view of your gamification progress:

- **Level Tier Track** — Visual track showing 5 tiers from Novice Reader to Thought Leader
- **KP Dimension Radar Chart** — Pentagon chart showing your balance across 5 dimensions
- **Streak Tracker** — Current streak with flame animation and a 30-day activity heatmap calendar
- **Daily Activity Chart** — Graphical view of your daily KP earnings
- **KP History** — Recent transactions showing how you earned (or lost) points
- **Rank & Percentile** — Your position among all users

### 8.2 How to Earn Knowledge Points

KP are earned through various library activities:

| Activity | KP Dimension |
|---|---|
| Browsing and discovering new books | **Explorer** |
| Reading e-books, completing books | **Scholar** |
| Writing reviews, social engagement | **Connector** |
| Unlocking achievements | **Achiever** |
| Maintaining daily reading streaks | **Dedicated** |

#### KP Weight Distribution

| Factor | Weight |
|---|---|
| Reading Time | 30% |
| Book Completion | 25% |
| Content Creation (reviews, etc.) | 20% |
| Consistency (streaks) | 15% |
| Diversity (varied genres) | 10% |

#### Daily Cap

You can earn a maximum of **200 KP per day**. This resets at midnight.

#### Minimum Session Requirements

- Minimum session length for KP credit: **2 minutes**
- Sessions idle for over 60 seconds without activity are not counted
- Maximum KP-eligible session length: **90 minutes**

### 8.3 Levels & Progression

Progress through 5 levels based on your total KP:

| Level | Title | KP Required |
|---|---|---|
| 1 | **Curious Reader** | 0 |
| 2 | **Active Learner** | 100 |
| 3 | **Knowledge Seeker** | 500 |
| 4 | **Scholar** | 1,500 |
| 5 | **Thought Leader** | 5,000 |

Your current level and progress toward the next level are displayed on the KP Center and your dashboard.

### 8.4 Streaks & Multipliers

A **streak** is maintained by being active for at least **15 minutes per day**.

Longer streaks unlock KP **multipliers** that boost your earnings:

| Streak Length | Multiplier |
|---|---|
| 3+ days | **1.1×** (10% bonus) |
| 7+ days | **1.2×** (20% bonus) |
| 14+ days | **1.3×** (30% bonus) |
| 30+ days | **1.5×** (50% bonus) |

The streak and multiplier are displayed with a flame animation on your dashboard and KP Center. The **30-day activity heatmap** shows your reading consistency visually.

### 8.5 Achievements & Badges

Navigate to **Achievements** (`/achievements`) to view all available badges.

#### Achievement Categories

| Category | Examples |
|---|---|
| **READING** | Read your first book, finish 10 books, etc. |
| **BORROWING** | Borrow your first book, complete 5 borrows, etc. |
| **SOCIAL** | Write your first review, get review upvotes |
| **STREAK** | Maintain a 7-day streak, 30-day streak, etc. |
| **MILESTONE** | Reach level 3, earn 1000 KP, etc. |
| **SPECIAL** | Seasonal or event-based achievements |

#### Rarity Tiers

| Tier | Difficulty |
|---|---|
| **Common** | Easily achievable by most users |
| **Uncommon** | Requires moderate effort |
| **Rare** | Requires significant dedication |
| **Epic** | Very challenging, few users achieve |
| **Legendary** | The ultimate achievements |

Each achievement earns a **bonus KP reward** based on its rarity. Unlocked achievements display in full color with the date earned; locked achievements appear greyed out with a 🔒 icon.

### 8.6 Leaderboard

View the **Leaderboard** (`/leaderboard`) to see how you rank among all library users.

- **My Rank Card** — Your personal rank, total KP, and level displayed prominently at the top
- **Top 50 Rankings** — Displays the top 50 users
  - 🥇 Gold medal for 1st place
  - 🥈 Silver medal for 2nd place
  - 🥉 Bronze medal for 3rd place
- **Your row** is highlighted for easy identification
- Each entry shows: Rank, Name, Total KP, Level Title

---

## 9. Intelligence & AI Features

### 9.1 Personalized Recommendations

Access **Recommendations** (`/recommendations`) for AI-curated book suggestions.

#### Recommendation Strategies

| Strategy | How It Works |
|---|---|
| **Collaborative Filtering** | Based on what similar readers enjoyed |
| **Content-Based** | Based on the genres, authors, and topics you've read |
| **Hybrid** | Combines collaborative and content-based approaches |
| **Trending** | Currently popular across all users |
| **"Because You Read X"** | Specific seed-book based recommendations |

#### Features

- **Match Score** — Percentage showing how well the book matches your profile
- **Explanation** — AI-generated reason for the recommendation (e.g., "Because you enjoyed 'Sapiens'")
- **Actions**:
  - **Click** — Opens the book detail (this click is tracked to improve future recommendations)
  - **Dismiss** — Removes the recommendation (also tracked for learning)
  - **Refresh** — Generate new recommendations

> **Cold Start:** If you're a new user with fewer than 5 interactions, you'll see trending and popular recommendations until the AI has enough data to personalize.

### 9.2 AI-Powered Search

The **Search** page (`/search`) combines traditional search with AI intelligence.

#### Features

1. **Auto-Suggest** — As you type, up to 8 suggestions appear based on prefix matching, trending searches, and your history
2. **Hybrid Search** — Combines full-text (keywords), semantic (meaning), and fuzzy (typo-tolerant) matching
3. **AI Answer** — An AI model reads your query and provides a natural language answer with book citations
4. **Search Click Tracking** — When you click a result, the click is logged to improve ranking

#### Tips for Better Search Results

- Use natural language: "best books about World War II" works better than "WWII books"
- Be specific: "introductory Python programming for beginners" is better than "Python"
- The AI understands concepts: searching for "books about overcoming adversity" finds relevant novels even without those exact words

### 9.3 Reading Insights

Access **Insights** (`/insights`) for personal reading analytics.

#### KPI Cards

| Metric | Description |
|---|---|
| **Reading Speed** | Your average words per minute (WPM) with speed category |
| **Avg Session Duration** | Average time per reading session |
| **Sessions/Week** | How many reading sessions you have per week |
| **Preferred Reading Time** | Your typical reading hour (morning, afternoon, evening, night) |

#### Charts

| Chart | Description |
|---|---|
| **Hourly Reading Activity** | Line chart showing when you read throughout the day |
| **Weekly Sessions** | Bar chart of sessions per day of the week |
| **Completion Predictions** | Doughnut chart estimating when you'll finish current books |
| **Engagement Heatmap** | Calendar-style heatmap of your reading activity over the last N days |

### 9.4 Notifications

Access **Notifications** (`/notifications`) to view all system notifications.

#### Notification Types

| Type | Icon | Description |
|---|---|---|
| **Overdue Warning** | ⚠️ | Your borrow is due soon or overdue |
| **Reservation Ready** | 📦 | Your reserved book is ready for pickup |
| **Recommendation** | 💡 | New personalized book recommendation |
| **Achievement** | 🏆 | You've unlocked a new achievement |
| **KP Earned** | ⭐ | Knowledge Points awarded |
| **System** | 🔔 | System-wide announcements |

#### Features

- **Unread Count** — Badge on the notification bell in the header (polled every 30 seconds)
- **Mark as Read** — Click on a notification or use "Mark as Read" button
- **Mark All as Read** — Bulk action to clear all unread notifications
- **Time-ago Timestamps** — Relative time display (e.g., "5 minutes ago", "2 days ago")

> **Daily Notification Cap:** Maximum of 8 notifications per day to avoid notification fatigue.

---

## 10. Profile Management

### 10.1 Editing Your Profile

1. Click your **avatar** in the top-right corner of the header
2. Select **"Profile"**
3. On the Profile page (`/profile`), you'll see:
   - Your avatar (with initial fallback)
   - Name, email, role, and verification status badge
4. Click the **"Edit Profile"** tab
5. Update your **First Name** and/or **Last Name**
6. Click **"Save Changes"**

### 10.2 Changing Your Password

1. Navigate to **Profile** → **"Change Password"** tab
2. Enter your **current password**
3. Enter your **new password** (minimum 8 characters, must include uppercase, number, and special character)
4. **Confirm** the new password
5. Click **"Change Password"**

### 10.3 Identity Verification Status

Your verification status is displayed on your profile page:

| Status | Meaning |
|---|---|
| **Verified** ✅ | Your identity has been confirmed |
| **Pending** ⏳ | Verification is under review |
| **Not Verified** | No verification submitted |
| **Rejected** ❌ | Verification failed — you may resubmit |

---

## 11. Administration Guide

This section covers features available to **Librarians**, **Assistants**, and **Super Admins**. Access the admin panel by clicking **"Admin Panel"** at the bottom of the member sidebar, or navigate directly to `/admin/dashboard`.

> **Permission-Based Access:** Admin menu items are dynamically shown based on your role's permissions. You will only see the sections your role allows.

### 11.1 Admin Dashboard

**Route:** `/admin/dashboard`  
**Access:** Librarian, Super Admin

The Admin Dashboard provides a high-level overview of the library system:

#### KPI Cards

| Metric | Description |
|---|---|
| **Total Users** | Count of registered users |
| **Total Books** | Books in the catalog |
| **Overdue Borrows** | Active overdue borrow records |
| **Active AI Models** | Currently activated AI models |

#### Widgets

- **Quick Access Tiles** — Asset Management, HR, Recruitment, Settings
- **Overdue Predictions** — AI-predicted overdue risk for current borrows
- **Churn Risk Predictions** — Users at risk of becoming inactive
- **Security Events** — Recent security incidents
- **AI Model Distribution** — Doughnut chart of model types (Embedding, Recommendation, OCR, Face)
- **Asset Statistics** — Physical asset status overview
- **HR Statistics** — Department/employee/vacancy counts

### 11.2 User Management

**Route:** `/admin/users`  
**Access:** Super Admin

Manage all registered users in the system.

#### Features

| Action | Description |
|---|---|
| **Search** | Search users by name or email |
| **Filter** | Filter by role (User/Assistant/Librarian/Super Admin) and status (Active/Inactive) |
| **Create User** | Create a new user account directly (bypassing registration) |
| **View Details** | 360° user detail modal showing: profile info, borrow history, fines, reservations, engagement/KP stats, achievements |
| **Activate / Deactivate** | Toggle user account active status |
| **Change Role** | Promote or demote a user's role |
| **Edit User** | Modify user profile details |

#### Creating a New User (Admin)

1. Click **"Create User"** button
2. Fill in: Email, First Name, Last Name, Password, Role
3. Click **"Create"**
4. The user can log in immediately

### 11.3 Member Management

**Route:** `/admin/members`  
**Access:** Librarian, Super Admin

Manage library member/patron records (separate from user accounts — members may have physical library cards without system accounts).

#### Features

| Action | Description |
|---|---|
| **Search** | Search members by name or membership number |
| **Filter** | Filter by membership type and status |
| **Create Member** | Add a new library member |
| **Edit Member** | Update member information |
| **Delete Member** | Remove a member record |

#### Membership Types

| Type | Description |
|---|---|
| **Student** | Student members |
| **Faculty** | Academic faculty |
| **Staff** | Institution staff |
| **Public** | General public members |
| **Senior** | Senior citizen members |
| **Child** | Child/youth members |

#### Member Statuses

| Status | Description |
|---|---|
| **Active** | Current, valid membership |
| **Suspended** | Temporarily suspended |
| **Expired** | Membership period ended |
| **Revoked** | Membership permanently revoked |

### 11.4 Book Management

**Route:** `/admin/books`  
**Access:** Librarian, Super Admin

Full CRUD management for the book catalog.

#### Creating a New Book

1. Click **"Add Book"**
2. Fill in the form:
   - **Title** (required)
   - **Subtitle** (optional)
   - **ISBN-10** and/or **ISBN-13**
   - **Publisher**
   - **Publication Date**
   - **Language**
   - **Page Count**
   - **Description**
   - **Cover Image URL**
   - **Authors** (select from existing)
   - **Categories** (select from existing)
3. Click **"Create Book"**

#### Managing Physical Copies

1. Click on a book to open its detail modal
2. Navigate to the **"Copies"** section
3. Click **"Add Copy"**
4. Fill in:
   - **Barcode** (required, unique)
   - **Shelf Location**
   - **Floor**
   - **Branch**
   - **Condition** (New, Good, Fair, Poor, Damaged)
   - **Acquisition Date**
   - **Acquisition Source**
5. Click **"Add Copy"**

#### Other Actions

- **Edit Book** — Modify any cataloging data
- **Delete Book** — Soft-delete (archival); won't delete if copies are actively borrowed
- **Search** — Filter books by keyword
- **Language Filter** — Filter by language

### 11.5 Author Management

**Route:** `/admin/authors`  
**Access:** Librarian, Super Admin

#### Features

| Action | Description |
|---|---|
| **Create Author** | Name, biography, birth date, death date, nationality, photo URL |
| **Edit Author** | Update author information |
| **Delete Author** | Remove author (only if no books are linked) |
| **View Detail** | 360° view with biography and all books by the author |
| **Search** | Search authors by name |

### 11.6 Digital Content Management

**Route:** `/admin/digital`  
**Access:** Librarian, Super Admin

Manage e-books and audiobooks linked to catalog books.

#### Uploading Digital Content

1. Click **"Upload Digital Asset"**
2. Select the **Book** to link to
3. Choose **Asset Type**: E-Book or Audiobook
4. Fill in metadata:
   - **File Path** / Upload
   - **File Size**
   - **Pages** (for e-books)
   - **Duration** (for audiobooks)
   - **Narrator** (for audiobooks)
   - **Format** (EPUB, PDF for e-books)
   - **DRM Protected** toggle
5. Click **"Upload"**

#### Other Actions

- **Edit Metadata** — Update asset details
- **Delete Asset** — Remove digital content
- **Filter by Type** — Show only E-Books or Audiobooks

### 11.7 Circulation Management

**Route:** `/admin/circulation`  
**Access:** Assistant, Librarian, Super Admin

The circulation admin page provides comprehensive borrow management across 4 tabs:

#### Tab: All Borrows

- View all borrow records system-wide
- Filter by status (Active, Overdue, Returned, Lost)
- Paginated list with user name, book title, borrow date, due date, status

#### Tab: Overdue

- Dedicated view for overdue borrows
- Sorted by how long overdue
- Quick action: **Return Book**

#### Tab: Pending Pickups

- Reservations in READY status awaiting patron arrival
- Shows assigned copy, branch, and pickup deadline
- Quick action: **Confirm Pickup** (creates the borrow record)

#### Tab: Fines

- All fines across the system
- Filter by status (Pending, Paid, Waived)
- Actions:
  - **Pay Fine** — Record a fine payment
  - **Waive Fine** — Forgive a fine (with confirmation dialog)

#### Key Admin Actions

| Action | Description | Who Can Do It |
|---|---|---|
| **Confirm Pickup** | Convert a READY reservation into an active borrow | Librarian, Assistant |
| **Return Book** | Process a physical book return | Librarian, Assistant |
| **Renew Borrow** | Extend a user's borrow period | Librarian |
| **Pay Fine** | Record a fine payment | Librarian |
| **Waive Fine** | Forgive a fine | Librarian |
| **Lift Reservation Ban** | Remove a user's reservation ban early | Librarian, Super Admin |

### 11.8 Roles & Permissions (RBAC)

**Route:** `/admin/roles`  
**Access:** Super Admin only

Nova supports dynamic **Role-Based Access Control** with a visual permission matrix.

#### Viewing Roles

The page lists all role configurations with their:
- Role name and key
- Description
- Number of modules with permissions
- Whether it's a system role (built-in) or custom

#### Creating a Custom Role

1. Click **"Create Role"**
2. Enter a **Role Name** and **Description**
3. Configure the **Permission Matrix**:
   - Rows = Modules (Identity, Catalog, Circulation, Digital Content, Engagement, Intelligence, Governance, Asset Management, HR)
   - Columns = Actions (Create, Read, Update, Delete)
   - Check/uncheck boxes to grant/revoke permissions
4. Click **"Create"**

#### Editing Permissions

1. Click on a role to open its detail
2. Modify the permission checkboxes
3. Click **"Save Changes"**

> **Note:** Built-in system roles (SUPER_ADMIN, LIBRARIAN, ASSISTANT, USER) cannot be deleted but their permissions can be modified.

### 11.9 Audit Logs & Security Events

**Route:** `/admin/audit`  
**Access:** Super Admin only

#### Audit Logs

Every significant action in the system is immutably logged:

| Field | Description |
|---|---|
| **Timestamp** | When the action occurred |
| **Actor** | Who performed the action (user name + email) |
| **Action** | Type of action (26+ categories including USER_LOGIN, BOOK_CREATED, BORROW_INITIATED, etc.) |
| **Resource** | What was affected (e.g., "Book: The Great Gatsby") |
| **IP Address** | IP address of the requester |
| **Old / New Values** | Before/after state for data changes |

Audit logs support:
- **Pagination** — Cursor-based for large datasets
- **Filtering** — By action type, resource type, actor

#### Security Events

Monitor security-related incidents:

| Event Type | Description |
|---|---|
| **FAILED_LOGIN** | Failed authentication attempt |
| **BRUTE_FORCE** | Multiple rapid failed login attempts |
| **TOKEN_REUSE** | Attempt to reuse a rotated refresh token |
| **SUSPICIOUS_ACTIVITY** | Unusual patterns detected |

Each event has a **severity level**: LOW, MEDIUM, HIGH, CRITICAL

Features:
- Filter by severity and resolved status
- View details (IP, user agent, timestamps)
- Mark events as resolved

### 11.10 Analytics & Predictive Intelligence

**Route:** `/admin/analytics`  
**Access:** Librarian, Super Admin

The analytics dashboard provides AI-powered predictive insights organized in tabs:

#### Tab: AI Insights

- **LLM-powered analytics** — Natural language analysis of library trends
- Generated by the local or cloud LLM based on library data

#### Tab: Overdue Risk Predictions

- AI predicts which current borrows are most likely to become overdue
- Risk score (0–1) with threshold of 0.6
- Risk level badges (Low, Medium, High)
- Allows proactive outreach to at-risk borrowers

#### Tab: Demand Forecasts

- Bar chart predicting future demand for books/categories
- Helps with acquisition planning

#### Tab: Churn Predictions

- Identifies users at risk of becoming inactive
- Risk score with contributing factors
- Enables targeted re-engagement

#### Tab: Collection Gap Analysis

- Identifies gaps in the library's collection based on user demand patterns
- Severity classification
- Actionable recommendations for acquisitions

### 11.11 AI Provider Configuration

**Route:** `/admin/ai-config`  
**Access:** Super Admin only

Configure and manage AI/ML providers for the system's intelligence features.

#### Supported Providers

| Provider | Type | Use Cases |
|---|---|---|
| **Ollama** | Local LLM | Chat, summarization, analytics (e.g., llama3.1) |
| **Google Gemini** | Cloud API | Chat, embeddings, classification |
| **OpenAI** | Cloud API | Chat, embeddings, summarization |
| **Local Transformers** | Local ML | Embeddings, face recognition, OCR |

#### Managing Providers

1. Click **"Add Provider"**
2. Select provider type (presets available)
3. Fill in:
   - **Name** and **Description**
   - **API Key** (for cloud providers)
   - **Base URL** (for Ollama: `http://localhost:11434`)
   - **Model Name** (preset selections available per provider)
   - **Capabilities**: Chat, Embedding, Summarization, Classification
4. Click **"Create"**

#### Provider Actions

| Action | Description |
|---|---|
| **Activate** | Enable this provider as the active one for its capabilities |
| **Health Check** | Test connectivity and model availability |
| **Test** | Send a test prompt and view the response |
| **Edit** | Modify configuration |
| **Delete** | Remove the provider |

#### Test Playground

At the bottom of the AI Config page, you can:
1. Enter a **prompt**
2. Click **"Generate"**
3. View the AI response in real-time
4. Useful for testing model quality before activating

### 11.12 Asset Management

**Route:** `/admin/assets`  
**Access:** Librarian, Super Admin

Track and manage physical library assets beyond the book collection.

#### Asset Categories

Hierarchical categories for organizing assets:
- **Furniture** (desks, chairs, shelving)
- **Electronics** (computers, monitors, printers)
- **Equipment** (AV equipment, self-checkout machines)
- Create custom categories as needed

#### Managing Assets

| Action | Description |
|---|---|
| **Create Asset** | Register a new physical asset with tag, category, location, purchase info |
| **Edit Asset** | Update status, condition, assignment |
| **Delete Asset** | Remove asset record |
| **Log Maintenance** | Record maintenance work performed on the asset |
| **Dispose Asset** | Process asset disposal (sold, donated, recycled, scrapped, transferred) |

#### Asset Fields

| Field | Description |
|---|---|
| **Asset Tag** | Unique identifier (barcode/asset number) |
| **Category** | Asset type category |
| **Status** | Active, In Storage, Under Maintenance, Disposed, On Order |
| **Condition** | Current physical condition |
| **Location** | Where the asset is located (building/floor/room) |
| **Purchase Price** | Original acquisition cost |
| **Purchase Date** | When it was acquired |
| **Warranty Expiry** | Warranty end date |
| **Depreciation Method** | Straight-line, declining balance, etc. |
| **Assigned To** | User currently assigned the asset |

#### Maintenance Logging

Record maintenance work:
- **Type**: Preventive, Corrective, Inspection, Upgrade
- **Description**: What was done
- **Cost**: Maintenance cost
- **Vendor**: Who performed the work
- **Condition After**: Asset condition post-maintenance

#### Asset Statistics

The asset dashboard shows:
- Total assets by status
- Total asset value
- Upcoming maintenance schedules
- Recently disposed assets

### 11.13 Human Resources (HR)

**Route:** `/admin/employees`  
**Access:** Librarian, Super Admin

Manage the library's workforce, organizational structure, and recruitment.

#### Departments

| Action | Description |
|---|---|
| **Create Department** | Name, code, description, head (select from employees) |
| **Edit Department** | Update department details |
| **View Details** | See department employees and statistics |

#### Employees

| Action | Description |
|---|---|
| **Create Employee** | Link to user account, set department, job title, employment type, salary |
| **Edit Employee** | Update employment details, reporting chain |
| **View 360° Detail** | Full employee profile with employment history |
| **Search / Filter** | By department, employment status |

#### Employment Types
- Full-Time
- Part-Time
- Contract
- Intern

#### Job Vacancies

| Action | Description |
|---|---|
| **Create Vacancy** | Title, department, description, experience level, salary range, closing date |
| **Edit Vacancy** | Update vacancy details |
| **Status Management** | Draft → Open → Closed / On Hold / Filled |

#### Job Applications

| Feature | Description |
|---|---|
| **View Applications** | See all applications per vacancy |
| **Application Pipeline** | Submitted → Under Review → Shortlisted → Interview → Offered → Accepted/Rejected/Withdrawn |
| **Update Status** | Move applications through the pipeline |

#### HR Statistics

Dashboard widget showing:
- Total departments
- Total employees
- Open vacancies
- Pending applications

### 11.14 System Settings

**Route:** `/admin/settings`  
**Access:** Super Admin only

Configure system-wide settings organized by category.

#### Setting Categories

| Category | Examples |
|---|---|
| **Circulation Policy** | Borrow period, max borrows, fine rates, pickup window |
| **Engagement** | Daily KP cap, streak requirements, level thresholds |
| **Security** | Login attempt limits, lockout durations, token expiry |
| **General** | Library name, timezone, default language |
| **Notifications** | Notification daily cap, email templates |
| **Email** | SMTP configuration (see SMTP page for guided setup) |

#### How to Edit Settings

1. Navigate to `/admin/settings`
2. Settings are displayed grouped by category
3. Click on a setting value to edit it inline
4. The setting type (String, Integer, Float, Boolean, JSON) determines the input control
5. Changes take effect immediately
6. **Sync Defaults** — Click to restore any missing settings to their default values

> **Caution:** Some settings marked as **sensitive** (e.g., API keys) are masked in the UI and require explicit reveal.

### 11.15 Email / SMTP Configuration

**Route:** `/admin/smtp`  
**Access:** Super Admin only

Configure email delivery for system notifications, password resets, and other email communications.

#### Provider Presets

One-click configuration for popular email providers:

| Provider | Port | Security | Notes |
|---|---|---|---|
| **Gmail** | 587 | TLS | Requires App Password (2FA must be enabled) |
| **Outlook** | 587 | TLS | Requires App Password |
| **Zoho** | 587 | TLS | Standard credentials |

Each preset includes **step-by-step instructions** for generating app passwords.

#### Manual Configuration

| Field | Description |
|---|---|
| **SMTP Host** | Mail server hostname |
| **SMTP Port** | Server port (typically 587 for TLS, 465 for SSL) |
| **Use TLS** | Enable TLS encryption |
| **Email User** | SMTP authentication username |
| **Email Password** | SMTP authentication password |
| **Default From Email** | Sender address for outgoing emails |

#### Testing

1. Enter a **test recipient email**
2. Click **"Send Test Email"**
3. Check the recipient's inbox to verify delivery
4. The system reports success or failure with error details

---

## 12. Circulation & Fine Policies

This section provides a comprehensive reference of all default circulation policies.

### Borrowing Limits

| Policy | Default Value |
|---|---|
| Default loan period | **14 days** |
| Maximum renewals per borrow | **2** |
| Maximum concurrent borrows per user | **2** |
| Maximum concurrent reservations per user | **2** |
| Reservation pickup window | **12 hours** |

### Fine Schedule

| Overdue Period | Daily Fine Rate |
|---|---|
| Days 1–7 | **$0.50 / day** |
| Days 8–30 | **$0.75 / day** (1.5× escalation) |
| Days 31+ | **$1.00 / day** (2× escalation) |

### Blocking Threshold

| Condition | Threshold |
|---|---|
| Unpaid fines blocking reservations | **$25.00** |

### Anti-Abuse (No-Show Prevention)

| Policy | Default Value |
|---|---|
| No-show lookback period | **30 days** |
| Max no-shows before ban | **3** |
| Ban duration | **7 days** |

### Overdue Reminders

The system sends automated reminders at the following intervals relative to the due date:

| Days Relative to Due Date | Notification |
|---|---|
| -3 days (3 days before due) | Upcoming due date reminder |
| -1 day (1 day before due) | Due tomorrow reminder |
| 0 days (due date) | Due today reminder |
| +1 day (1 day overdue) | Overdue notice |
| +3 days (3 days overdue) | Overdue warning |
| +7 days (7 days overdue) | Overdue final notice |

---

## 13. Keyboard Shortcuts & Tips

### Global Shortcuts

| Shortcut | Action |
|---|---|
| `⌘K` / `Ctrl+K` | Open quick search |

### E-Book Reader

| Shortcut | Action |
|---|---|
| `←` Left Arrow | Previous page |
| `→` Right Arrow | Next page |

### Audiobook Player

| Shortcut | Action |
|---|---|
| `Space` | Play / Pause |
| `←` Left Arrow | Skip backward 15 seconds |
| `→` Right Arrow | Skip forward 30 seconds |

### UI Tips

| Tip | Description |
|---|---|
| **Collapse Sidebar** | Click the collapse icon at the bottom of the sidebar to switch to icon-only mode |
| **Dark Mode** | Toggle dark/light theme from the header (persisted) |
| **Auto-suggest** | Start typing in the search page for instant suggestions |
| **Drag & Drop** | Drag files directly onto upload areas for NIC verification and other uploads |
| **OTP Paste** | Paste your full 6-digit OTP code into the first box — it auto-fills all boxes |
| **Breadcrumbs** | Use breadcrumb navigation at the top of pages to quickly navigate back |

---

## 14. Security & Privacy

Nova implements multiple layers of security to protect your data and account.

### Account Security

| Feature | Detail |
|---|---|
| **Password Hashing** | Argon2id (industry-leading, memory-hard hashing) |
| **Minimum Password Length** | 10 characters |
| **Password Requirements** | Uppercase, number, and special character |
| **Account Lockout** | After 5 failed login attempts, progressive lockout (5 min → exponential up to 1 hour) |
| **IP-Level Lockout** | After 20 failed attempts from same IP, 10-minute IP block |
| **JWT Tokens** | Access tokens expire in 15 minutes; refresh tokens expire in 7 days |
| **Token Rotation** | Refresh tokens are single-use; using a refresh token issues a new pair |
| **Auto-Logout** | Session automatically ends after 30 minutes of inactivity |

### Data Protection

| Feature | Detail |
|---|---|
| **XSS Prevention** | All user-generated HTML sanitized via DOMPurify |
| **CSRF Protection** | JWT-based authentication (no cookies) |
| **Rate Limiting** | Login: 5/min, Queries: 120/min, Mutations: 30/min, Uploads: 10/hr |
| **GraphQL Security** | Query depth limit: 10, complexity limit: 1000, max query size: 10KB |
| **Audit Trail** | Every significant action is immutably logged with actor, IP, and timestamp |
| **Security Events** | Failed logins, brute force attempts, and token reuse are detected and logged |
| **File Security** | Uploaded files are validated for type, size, and content integrity |

### Privacy

- Identity verification documents are securely stored
- Sensitive settings (API keys, etc.) are masked in the admin UI
- Audit logs do not expose password values
- Personal reading data and KP history are private to each user
- The leaderboard shows only names and aggregate KP — no private reading details

### Best Practices for Users

1. **Use a strong, unique password** — The strength meter helps you choose a good one
2. **Don't share your credentials** — Each account is personal
3. **Log out on shared devices** — Use the Sign Out option from the user menu
4. **Report suspicious activity** — Contact your librarian if you notice unusual account activity
5. **Keep your NIC verification current** — Resubmit if your original verification was rejected

---

## 15. Troubleshooting & FAQ

### Frequently Asked Questions

#### Account & Login

**Q: I can't log in — my account seems locked.**  
A: After 5 consecutive failed login attempts, your account is temporarily locked. Wait at least 5 minutes and try again. If the problem persists, use the "Forgot Password" feature to reset your password or contact a librarian.

**Q: I didn't receive my OTP email.**  
A: Check your spam/junk folder. OTPs expire after 10 minutes. If you still don't receive it, try requesting a new OTP. If the problem persists, contact a system administrator to verify your email configuration.

**Q: My NIC verification was rejected.**  
A: Ensure your NIC photos are clear, well-lit, and fully visible. Make sure the NIC number you entered matches exactly. You can resubmit verification from your profile page.

#### Borrowing & Reservations

**Q: I can't reserve a book.**  
A: Check the following:
- You may have reached your maximum of 2 active borrows or 2 active reservations
- You may be under a reservation ban (3 no-shows in 30 days)
- You may have unpaid fines exceeding $25.00
- The specific book may not have any copies registered

**Q: My reservation expired — what happened?**  
A: When a reservation becomes READY, you have 12 hours to pick up the book. If you don't, the reservation automatically expires and the copy is released. This counts as a no-show.

**Q: How do I return a book?**  
A: Physical book returns must be processed at the library's circulation desk. You cannot return books online. Bring the book to the library, and a librarian will process the return.

**Q: Why was I banned from making reservations?**  
A: If you have 3 or more expired (no-show) reservations within a 30-day period, the system automatically places a 7-day ban. Wait for the ban to expire, or contact a librarian who may lift it early.

**Q: What happens if I lose a book?**  
A: Contact the library immediately. The librarian will mark the book as lost and a replacement fine will be assessed. The fine may be waived at the librarian's discretion.

#### Digital Library

**Q: My reading progress wasn't saved.**  
A: Progress is saved automatically every 30 seconds and on page turns. If you close the browser abruptly, the last auto-save point will be used. Ensure you have a stable internet connection.

**Q: Can I read on multiple devices?**  
A: Yes, your progress syncs across devices. When you open a book on a new device, it will resume from your last saved position.

**Q: The audiobook is not playing.**  
A: Ensure your browser supports audio playback and your volume is turned up. Try a different browser if the issue persists. Check that you have a stable internet connection for streaming.

#### Knowledge Points & Gamification

**Q: Why didn't I earn KP for my reading session?**  
A: KP requires a minimum session of **2 minutes** of active reading. Sessions shorter than 2 minutes or idle for over 60 seconds without interaction are not credited. Also check if you've reached the daily cap of **200 KP**.

**Q: How do I increase my streak multiplier?**  
A: Be active for at least 15 minutes per day. Consecutive days of activity build your streak: 3 days → 1.1×, 7 days → 1.2×, 14 days → 1.3×, 30 days → 1.5× multiplier.

**Q: I lost my streak — can it be restored?**  
A: Streaks are automatically evaluated daily. Missing a single day resets the streak. Streaks cannot be manually restored.

#### Administration

**Q: I can't see admin features.**  
A: Only users with Librarian, Assistant, or Super Admin roles can access admin features. Contact your Super Admin to have your role updated. Individual admin pages are also controlled by RBAC permissions.

**Q: How do I add a new category to the catalog?**  
A: Navigate to the admin books page and use the "Create Category" option. Categories support hierarchical structure (parent-child relationships).

**Q: An AI feature isn't working.**  
A: Check the AI Provider Configuration page (`/admin/ai-config`). Ensure at least one provider is activated and healthy. Run a health check to test connectivity. For local Ollama, ensure the Ollama server is running on port 11434.

### Common Error Messages

| Error | Cause | Solution |
|---|---|---|
| "Maximum borrow limit reached" | You have 2 active borrows | Return a book before borrowing another |
| "Maximum reservation limit reached" | You have 2 active reservations | Wait for a reservation to be fulfilled or cancel one |
| "Account is temporarily locked" | Too many failed login attempts | Wait for the lockout period to expire |
| "Reservation ban active" | 3+ no-shows in 30 days | Wait for ban expiry (7 days) or contact a librarian |
| "Outstanding fines exceed limit" | Unpaid fines over $25.00 | Pay fines before making new reservations |
| "Token expired" | JWT access token expired | The system auto-refreshes; re-login if persistent |
| "Permission denied" | Insufficient role/permissions | Contact your Super Admin for role adjustment |

---

## 16. Glossary

| Term | Definition |
|---|---|
| **AI Provider** | An external or local AI/ML service (Ollama, Gemini, OpenAI) used for intelligent features |
| **Audiobook** | A digital book in audio format that can be streamed through the built-in player |
| **Borrow Record** | A record of a physical book loan from reservation pickup to return |
| **Bookmark** | A saved position in an e-book (page) or audiobook (timestamp) for quick return |
| **Book Copy** | A specific physical instance of a book (identified by barcode) |
| **Churn Prediction** | AI analysis identifying users at risk of becoming inactive |
| **DRM** | Digital Rights Management — content protection for digital assets |
| **E-Book** | A digital book in EPUB or PDF format readable through the built-in reader |
| **Fine** | A monetary charge for overdue, lost, or damaged books |
| **GraphQL** | The API query language used by Nova for client-server communication |
| **Highlight** | A saved text selection in an e-book reader |
| **Hybrid Search** | Search combining full-text, semantic, and fuzzy matching for comprehensive results |
| **JWT** | JSON Web Token — the authentication mechanism used for secure API access |
| **Knowledge Points (KP)** | Gamification currency earned through library engagement activities |
| **KP Dimension** | One of five categories (Explorer, Scholar, Connector, Achiever, Dedicated) measuring engagement type |
| **Leaderboard** | Ranked list of users by total Knowledge Points |
| **LLM** | Large Language Model — AI model used for natural language understanding and generation |
| **Member** | A library patron/cardholder (may or may not have a system user account) |
| **NIC** | National Identity Card — used for AI-powered identity verification |
| **OCR** | Optical Character Recognition — AI extraction of text from images |
| **Ollama** | Local LLM server used for AI features without cloud dependency |
| **OTP** | One-Time Password — a 6-digit code sent via email for password reset verification |
| **RBAC** | Role-Based Access Control — permission system controlling feature access by user role |
| **Reading Session** | A tracked period of e-book reading or audiobook listening |
| **Recommendation** | An AI-suggested book based on your reading history and preferences |
| **Reservation** | A request to borrow a physical book; the entry point for the borrowing workflow |
| **Reservation Ban** | A temporary block on making new reservations due to repeated no-shows |
| **Streak** | Consecutive days of library activity (minimum 15 minutes/day) |
| **Streak Multiplier** | A KP bonus applied based on streak length (up to 1.5× at 30 days) |
| **Trending Book** | A book ranked by current popularity across daily, weekly, monthly, or all-time periods |
| **User Engagement** | Aggregate KP profile for a user including level, dimensions, streaks, and rank |

---

*This user manual covers all features of the Nova Smart Library Management Ecosystem v1.0. For technical documentation, API references, and architecture details, please refer to the `/docs/` directory in the project repository.*
