"""
Nova — Seed Database Command
================================
Populates the database with realistic test data across all 8 bounded contexts.

Usage:
    python manage.py seed_data              # Full seed
    python manage.py seed_data --flush      # Wipe existing data first
    python manage.py seed_data --minimal    # Only users + 5 books

Test Credentials (all passwords = "NovaTest@2026"):
    ┌────────────────────────────┬──────────────┬──────────────────┐
    │ Email                      │ Role         │ Verified?        │
    ├────────────────────────────┼──────────────┼──────────────────┤
    │ admin@nova.local           │ SUPER_ADMIN  │ Yes              │
    │ librarian@nova.local       │ LIBRARIAN    │ Yes              │
    │ assistant@nova.local       │ ASSISTANT    │ Yes              │
    │ alice@nova.local           │ USER         │ Yes              │
    │ bob@nova.local             │ USER         │ Yes              │
    │ charlie@nova.local         │ USER         │ Yes              │
    │ diana@nova.local           │ USER         │ No  (pending)    │
    │ eve@nova.local             │ USER         │ No  (new)        │
    └────────────────────────────┴──────────────┴──────────────────┘
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PASSWORD = "NovaTest@2026"

BOOKS_DATA = [
    {
        "title": "Clean Code",
        "subtitle": "A Handbook of Agile Software Craftsmanship",
        "isbn_13": "9780132350884",
        "isbn_10": "0132350882",
        "publisher": "Prentice Hall",
        "pub_date": date(2008, 8, 1),
        "language": "en",
        "pages": 464,
        "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees. Every year, countless hours and significant resources are lost because of poorly written code. But it doesn't have to be that way.",
        "dewey": "005.1",
        "tags": ["software engineering", "agile", "clean code", "best practices"],
    },
    {
        "title": "Design Patterns",
        "subtitle": "Elements of Reusable Object-Oriented Software",
        "isbn_13": "9780201633610",
        "isbn_10": "0201633612",
        "publisher": "Addison-Wesley",
        "pub_date": date(1994, 10, 31),
        "language": "en",
        "pages": 395,
        "description": "Capturing a wealth of experience about the design of object-oriented software, four top-notch designers present a catalog of simple and succinct solutions to commonly occurring design problems.",
        "dewey": "005.12",
        "tags": ["design patterns", "OOP", "software architecture"],
    },
    {
        "title": "Introduction to Algorithms",
        "subtitle": "",
        "isbn_13": "9780262046305",
        "isbn_10": "0262046305",
        "publisher": "MIT Press",
        "pub_date": date(2022, 4, 5),
        "language": "en",
        "pages": 1312,
        "description": "A comprehensive introduction to the modern study of computer algorithms. It covers a broad range of algorithms in depth, yet makes their design and analysis accessible to all levels of readers.",
        "dewey": "005.1",
        "tags": ["algorithms", "data structures", "computer science"],
    },
    {
        "title": "The Pragmatic Programmer",
        "subtitle": "Your Journey to Mastery",
        "isbn_13": "9780135957059",
        "isbn_10": "0135957052",
        "publisher": "Addison-Wesley",
        "pub_date": date(2019, 9, 23),
        "language": "en",
        "pages": 352,
        "description": "The Pragmatic Programmer is one of those rare tech books you'll read, re-read, and read again over the years. Whether you're new to the field or an experienced practitioner, you'll come away with fresh insights each and every time.",
        "dewey": "005.1",
        "tags": ["pragmatic", "software development", "career"],
    },
    {
        "title": "Refactoring",
        "subtitle": "Improving the Design of Existing Code",
        "isbn_13": "9780134757599",
        "isbn_10": "0134757599",
        "publisher": "Addison-Wesley",
        "pub_date": date(2018, 11, 20),
        "language": "en",
        "pages": 448,
        "description": "Fully revised and updated — includes new refactorings and code examples. For more than twenty years, experienced programmers worldwide have relied on Martin Fowler's Refactoring to improve the design of existing code.",
        "dewey": "005.1",
        "tags": ["refactoring", "code quality", "design"],
    },
    {
        "title": "Structure and Interpretation of Computer Programs",
        "subtitle": "",
        "isbn_13": "9780262510875",
        "isbn_10": "0262510871",
        "publisher": "MIT Press",
        "pub_date": date(1996, 7, 25),
        "language": "en",
        "pages": 657,
        "description": "Structure and Interpretation of Computer Programs has had a dramatic impact on computer science curricula over the past decade. This long-awaited revision contains changes throughout the text.",
        "dewey": "005.13",
        "tags": ["computer science", "scheme", "functional programming"],
    },
    {
        "title": "Artificial Intelligence: A Modern Approach",
        "subtitle": "",
        "isbn_13": "9780134610993",
        "isbn_10": "0134610997",
        "publisher": "Pearson",
        "pub_date": date(2020, 4, 28),
        "language": "en",
        "pages": 1115,
        "description": "The most comprehensive, up-to-date introduction to the theory and practice of artificial intelligence. #1 in its field, this textbook is ideal for one or two-semester courses.",
        "dewey": "006.3",
        "tags": ["artificial intelligence", "machine learning", "AI"],
    },
    {
        "title": "The Art of Computer Programming",
        "subtitle": "Volume 1: Fundamental Algorithms",
        "isbn_13": "9780201896831",
        "isbn_10": "0201896834",
        "publisher": "Addison-Wesley",
        "pub_date": date(2011, 3, 3),
        "language": "en",
        "pages": 672,
        "description": "The bible of all fundamental algorithms and the work that taught many of today's software developers most of what they know about computer programming.",
        "dewey": "005.1",
        "tags": ["algorithms", "knuth", "fundamentals"],
    },
    {
        "title": "Domain-Driven Design",
        "subtitle": "Tackling Complexity in the Heart of Software",
        "isbn_13": "9780321125217",
        "isbn_10": "0321125215",
        "publisher": "Addison-Wesley",
        "pub_date": date(2003, 8, 30),
        "language": "en",
        "pages": 560,
        "description": "Eric Evans has written a fantastic book on how you can make the design of your software match your mental model of the problem domain you are addressing.",
        "dewey": "005.1",
        "tags": ["DDD", "domain driven design", "software architecture"],
    },
    {
        "title": "Database Internals",
        "subtitle": "A Deep Dive into How Distributed Data Systems Work",
        "isbn_13": "9781492040347",
        "isbn_10": "1492040347",
        "publisher": "O'Reilly Media",
        "pub_date": date(2019, 10, 1),
        "language": "en",
        "pages": 373,
        "description": "When it comes to choosing, using, and maintaining a database, understanding its internals is essential. This book explains how databases and various storage engines work under the hood.",
        "dewey": "005.74",
        "tags": ["databases", "distributed systems", "storage"],
    },
    {
        "title": "Python Crash Course",
        "subtitle": "A Hands-On, Project-Based Introduction to Programming",
        "isbn_13": "9781718502703",
        "isbn_10": "1718502702",
        "publisher": "No Starch Press",
        "pub_date": date(2023, 1, 10),
        "language": "en",
        "pages": 552,
        "description": "Python Crash Course is the world's best-selling guide to the Python programming language. This fast-paced, thorough introduction will have you writing programs and solving problems in no time.",
        "dewey": "005.133",
        "tags": ["python", "programming", "beginner"],
    },
    {
        "title": "Designing Data-Intensive Applications",
        "subtitle": "The Big Ideas Behind Reliable, Scalable, and Maintainable Systems",
        "isbn_13": "9781449373320",
        "isbn_10": "1449373321",
        "publisher": "O'Reilly Media",
        "pub_date": date(2017, 3, 16),
        "language": "en",
        "pages": 616,
        "description": "Data is at the center of many challenges in system design today. This book helps you navigate the tools and approaches available for building data-intensive applications.",
        "dewey": "005.7",
        "tags": ["distributed systems", "data engineering", "scalability"],
    },
    {
        "title": "Le Petit Prince",
        "subtitle": "",
        "isbn_13": "9782070612758",
        "isbn_10": "2070612759",
        "publisher": "Gallimard",
        "pub_date": date(2000, 6, 29),
        "language": "fr",
        "pages": 96,
        "description": "Le Petit Prince est une œuvre de langue française, la plus connue d'Antoine de Saint-Exupéry. Publié en 1943 à New York, c'est un conte poétique et philosophique.",
        "dewey": "843",
        "tags": ["french literature", "classic", "children"],
    },
    {
        "title": "Don Quijote de la Mancha",
        "subtitle": "",
        "isbn_13": "9788420412146",
        "isbn_10": "8420412147",
        "publisher": "Alfaguara",
        "pub_date": date(2015, 3, 19),
        "language": "es",
        "pages": 1376,
        "description": "Considerada la primera novela moderna, Don Quijote de la Mancha cuenta las aventuras del ingenioso hidalgo que confunde la realidad con sus fantasías caballerescas.",
        "dewey": "863",
        "tags": ["spanish literature", "classic", "novel"],
    },
    {
        "title": "Microservices Patterns",
        "subtitle": "With examples in Java",
        "isbn_13": "9781617294549",
        "isbn_10": "1617294543",
        "publisher": "Manning",
        "pub_date": date(2018, 10, 27),
        "language": "en",
        "pages": 520,
        "description": "Microservices Patterns teaches you 44 reusable patterns to reliably develop and deploy production-quality microservices-based applications.",
        "dewey": "005.1",
        "tags": ["microservices", "patterns", "architecture"],
    },
]

AUTHORS_DATA = [
    {"first_name": "Robert", "last_name": "Martin", "nationality": "American", "birth_date": date(1952, 12, 5)},
    {"first_name": "Erich", "last_name": "Gamma", "nationality": "Swiss", "birth_date": date(1961, 3, 13)},
    {"first_name": "Thomas", "last_name": "Cormen", "nationality": "American"},
    {"first_name": "David", "last_name": "Thomas", "nationality": "British", "birth_date": date(1956, 1, 1)},
    {"first_name": "Andrew", "last_name": "Hunt", "nationality": "American"},
    {"first_name": "Martin", "last_name": "Fowler", "nationality": "British", "birth_date": date(1963, 12, 18)},
    {"first_name": "Harold", "last_name": "Abelson", "nationality": "American"},
    {"first_name": "Stuart", "last_name": "Russell", "nationality": "British"},
    {"first_name": "Donald", "last_name": "Knuth", "nationality": "American", "birth_date": date(1938, 1, 10)},
    {"first_name": "Eric", "last_name": "Evans", "nationality": "American"},
    {"first_name": "Alex", "last_name": "Petrov", "nationality": "Ukrainian"},
    {"first_name": "Eric", "last_name": "Matthes", "nationality": "American"},
    {"first_name": "Martin", "last_name": "Kleppmann", "nationality": "German"},
    {"first_name": "Antoine", "last_name": "de Saint-Exupéry", "nationality": "French", "birth_date": date(1900, 6, 29), "death_date": date(1944, 7, 31)},
    {"first_name": "Miguel", "last_name": "de Cervantes", "nationality": "Spanish", "birth_date": date(1547, 9, 29), "death_date": date(1616, 4, 22)},
    {"first_name": "Chris", "last_name": "Richardson", "nationality": "American"},
]

# Map: book_index -> [author_indices]
BOOK_AUTHOR_MAP = {
    0: [0],       # Clean Code -> Robert Martin
    1: [1],       # Design Patterns -> Erich Gamma (lead)
    2: [2],       # Intro to Algorithms -> Thomas Cormen (lead)
    3: [3, 4],    # Pragmatic Programmer -> David Thomas, Andrew Hunt
    4: [5],       # Refactoring -> Martin Fowler
    5: [6],       # SICP -> Harold Abelson
    6: [7],       # AI Modern Approach -> Stuart Russell
    7: [8],       # Art of Computer Programming -> Donald Knuth
    8: [9],       # DDD -> Eric Evans
    9: [10],      # Database Internals -> Alex Petrov
    10: [11],     # Python Crash Course -> Eric Matthes
    11: [12],     # DDIA -> Martin Kleppmann
    12: [13],     # Le Petit Prince -> Saint-Exupéry
    13: [14],     # Don Quijote -> Cervantes
    14: [15],     # Microservices Patterns -> Chris Richardson
}

CATEGORIES_DATA = [
    {"name": "Computer Science", "slug": "computer-science", "icon": "cpu", "sort_order": 1,
     "children": [
         {"name": "Algorithms & Data Structures", "slug": "algorithms", "icon": "code", "sort_order": 1},
         {"name": "Software Engineering", "slug": "software-engineering", "icon": "wrench", "sort_order": 2},
         {"name": "Artificial Intelligence", "slug": "artificial-intelligence", "icon": "sparkles", "sort_order": 3},
         {"name": "Databases", "slug": "databases", "icon": "circle-stack", "sort_order": 4},
         {"name": "Programming Languages", "slug": "programming-languages", "icon": "code-bracket", "sort_order": 5},
     ]},
    {"name": "Literature", "slug": "literature", "icon": "book-open", "sort_order": 2,
     "children": [
         {"name": "Classic Literature", "slug": "classic-literature", "icon": "academic-cap", "sort_order": 1},
         {"name": "French Literature", "slug": "french-literature", "icon": "flag", "sort_order": 2},
         {"name": "Spanish Literature", "slug": "spanish-literature", "icon": "flag", "sort_order": 3},
     ]},
    {"name": "Architecture & Design", "slug": "architecture-design", "icon": "building-office", "sort_order": 3},
]

# Maps: book_index -> [category_slugs]
BOOK_CATEGORY_MAP = {
    0: ["software-engineering"],
    1: ["software-engineering"],
    2: ["algorithms"],
    3: ["software-engineering"],
    4: ["software-engineering"],
    5: ["algorithms", "programming-languages"],
    6: ["artificial-intelligence"],
    7: ["algorithms"],
    8: ["software-engineering", "architecture-design"],
    9: ["databases"],
    10: ["programming-languages"],
    11: ["databases", "architecture-design"],
    12: ["french-literature", "classic-literature"],
    13: ["spanish-literature", "classic-literature"],
    14: ["software-engineering", "architecture-design"],
}

REVIEW_TEXTS = [
    ("Excellent resource!", "Changed the way I think about software design. A must-read for every developer."),
    ("Very informative", "Comprehensive coverage of the topic. Some chapters are dense but worth the effort."),
    ("Good but dated", "The core ideas are timeless, even if some examples feel a bit old."),
    ("Outstanding", "One of the best technical books I've ever read. Clear explanations and practical advice."),
    ("Solid fundamentals", "Great for building a strong foundation. I keep coming back to it as a reference."),
    ("Highly recommended", "Practical, well-written, and full of insights from real-world experience."),
]

ACHIEVEMENT_DATA = [
    {"code": "FIRST_BORROW", "name": "First Steps", "description": "Borrowed your first book.", "category": "BORROWING", "rarity": "COMMON", "kp_reward": 10},
    {"code": "BOOKWORM_10", "name": "Bookworm", "description": "Borrowed 10 books.", "category": "BORROWING", "rarity": "UNCOMMON", "kp_reward": 50},
    {"code": "FIRST_REVIEW", "name": "Critic's Debut", "description": "Wrote your first book review.", "category": "SOCIAL", "rarity": "COMMON", "kp_reward": 15},
    {"code": "STREAK_7", "name": "Week Warrior", "description": "Maintained a 7-day reading streak.", "category": "STREAK", "rarity": "UNCOMMON", "kp_reward": 30},
    {"code": "STREAK_30", "name": "Monthly Master", "description": "Maintained a 30-day reading streak.", "category": "STREAK", "rarity": "RARE", "kp_reward": 100},
    {"code": "READER_100_PAGES", "name": "Century Reader", "description": "Read 100 pages digitally.", "category": "READING", "rarity": "COMMON", "kp_reward": 20},
    {"code": "READER_1000_PAGES", "name": "Thousand-Page Turner", "description": "Read 1,000 pages digitally.", "category": "READING", "rarity": "RARE", "kp_reward": 75},
    {"code": "DIVERSE_3_CATS", "name": "Explorer", "description": "Borrowed from 3 different categories.", "category": "MILESTONE", "rarity": "UNCOMMON", "kp_reward": 25},
    {"code": "LEVEL_5", "name": "Thought Leader", "description": "Reached Level 5.", "category": "MILESTONE", "rarity": "LEGENDARY", "kp_reward": 200},
    {"code": "FIRST_HIGHLIGHT", "name": "Highlighter", "description": "Created your first highlight.", "category": "READING", "rarity": "COMMON", "kp_reward": 10},
]


class Command(BaseCommand):
    help = "Seed the database with realistic test data for all bounded contexts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Delete all existing data before seeding.",
        )
        parser.add_argument(
            "--minimal", action="store_true",
            help="Seed only users and 5 books (skip engagement, circulation, etc.).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Nova Database Seeder ===\n"))

        users = self._seed_users()
        authors = self._seed_authors()
        categories = self._seed_categories()
        books = self._seed_books(authors, categories, users)

        if not options["minimal"]:
            copies = self._seed_book_copies(books)
            self._seed_borrows(users, copies, books)
            self._seed_digital_assets(books, users)
            self._seed_reviews(books, users)
            self._seed_engagement(users)
            self._seed_achievements(users)
            self._seed_recommendations(users, books)
            self._seed_trending(books)
            self._seed_audit_logs(users)
            self._seed_assets(users)
            self._seed_hr(users)
            self._seed_members(users)
            self._seed_system_settings()

        self._print_credentials(users)
        self.stdout.write(self.style.SUCCESS("\n✅ Seeding complete!\n"))

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    def _flush(self):
        """Delete all seeded data (order respects FK constraints)."""
        from apps.governance.domain.models import AuditLog, SecurityEvent, KPLedger
        from apps.intelligence.domain.models import Recommendation, UserPreference, SearchLog, TrendingBook
        from apps.engagement.domain.models import UserEngagement, Achievement, UserAchievement, DailyActivity
        from apps.digital_content.domain.models import DigitalAsset, ReadingSession, Bookmark, Highlight, UserLibrary
        from apps.circulation.domain.models import BorrowRecord, Reservation, Fine
        from apps.catalog.domain.models import BookReview, BookCopy, Book, Author, Category
        from apps.identity.domain.models import RefreshToken, VerificationRequest, User, Member
        from apps.asset_management.domain.models import AssetDisposal, MaintenanceLog, Asset, AssetCategory
        from apps.hr.domain.models import JobApplication, JobVacancy, Employee, Department
        from apps.common.domain.settings_model import SystemSetting

        # Delete in dependency order
        for model in [
            SystemSetting,
            JobApplication, JobVacancy, Employee, Department,
            AssetDisposal, MaintenanceLog, Asset, AssetCategory,
            KPLedger, SecurityEvent, AuditLog,
            TrendingBook, SearchLog, Recommendation, UserPreference,
            UserAchievement, DailyActivity, UserEngagement, Achievement,
            Highlight, Bookmark, UserLibrary, ReadingSession, DigitalAsset,
            Fine, Reservation, BorrowRecord,
            BookReview, BookCopy,
            Member,
        ]:
            model.objects.all().delete()

        # Books with M2M need separate handling
        Book.objects.all().delete()
        Author.objects.all().delete()
        Category.objects.all().delete()

        # Users last
        RefreshToken.objects.all().delete()
        VerificationRequest.objects.all().delete()
        User.all_objects.all().delete()

        self.stdout.write(self.style.WARNING("  Flushed all data."))

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def _seed_users(self):
        from apps.identity.domain.models import User

        user_specs = [
            {"email": "admin@nova.local", "first_name": "System", "last_name": "Administrator",
             "role": "SUPER_ADMIN", "is_staff": True, "is_verified": True, "is_active": True,
             "verification_status": "APPROVED"},
            {"email": "librarian@nova.local", "first_name": "Sarah", "last_name": "Johnson",
             "role": "LIBRARIAN", "is_staff": True, "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "phone_number": "+94771234567"},
            {"email": "assistant@nova.local", "first_name": "Kumar", "last_name": "Perera",
             "role": "ASSISTANT", "is_staff": True, "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "phone_number": "+94779876543"},
            {"email": "alice@nova.local", "first_name": "Alice", "last_name": "Fernando",
             "role": "USER", "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "institution_id": "STU-2024-001",
             "date_of_birth": date(2000, 5, 15)},
            {"email": "bob@nova.local", "first_name": "Bob", "last_name": "Silva",
             "role": "USER", "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "institution_id": "STU-2024-002",
             "date_of_birth": date(1998, 11, 22)},
            {"email": "charlie@nova.local", "first_name": "Charlie", "last_name": "Mendis",
             "role": "USER", "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "institution_id": "STU-2024-003",
             "date_of_birth": date(2001, 3, 8)},
            {"email": "diana@nova.local", "first_name": "Diana", "last_name": "Wickrama",
             "role": "USER", "is_verified": False, "is_active": True,
             "verification_status": "PENDING"},
            {"email": "eve@nova.local", "first_name": "Eve", "last_name": "Rajapaksa",
             "role": "USER", "is_verified": False, "is_active": True,
             "verification_status": "PENDING", "date_of_birth": date(2002, 7, 30)},
        ]

        users = {}
        for spec in user_specs:
            email = spec.pop("email")
            user, created = User.objects.get_or_create(
                email=email,
                defaults=spec,
            )
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                self.stdout.write(f"  + User: {email} ({user.role})")
            else:
                self.stdout.write(f"  ~ User exists: {email}")
            users[email] = user

        return users

    # ------------------------------------------------------------------
    # Authors
    # ------------------------------------------------------------------

    def _seed_authors(self):
        from apps.catalog.domain.models import Author

        authors = []
        for a in AUTHORS_DATA:
            obj, created = Author.objects.get_or_create(
                first_name=a["first_name"],
                last_name=a["last_name"],
                defaults={
                    "nationality": a.get("nationality", ""),
                    "birth_date": a.get("birth_date"),
                    "death_date": a.get("death_date"),
                    "biography": f"{a['first_name']} {a['last_name']} is a renowned author in the field.",
                },
            )
            authors.append(obj)
            if created:
                self.stdout.write(f"  + Author: {obj.full_name}")

        return authors

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    def _seed_categories(self):
        from apps.catalog.domain.models import Category

        cat_map = {}
        for top in CATEGORIES_DATA:
            children = top.pop("children", [])
            parent, _ = Category.objects.get_or_create(
                slug=top["slug"],
                defaults={
                    "name": top["name"],
                    "icon": top.get("icon", ""),
                    "sort_order": top.get("sort_order", 0),
                    "description": f"Top-level category: {top['name']}",
                },
            )
            cat_map[top["slug"]] = parent

            for child in children:
                obj, _ = Category.objects.get_or_create(
                    slug=child["slug"],
                    defaults={
                        "name": child["name"],
                        "parent": parent,
                        "icon": child.get("icon", ""),
                        "sort_order": child.get("sort_order", 0),
                        "description": f"Subcategory of {top['name']}",
                    },
                )
                cat_map[child["slug"]] = obj

        self.stdout.write(f"  + Categories: {len(cat_map)} total")
        return cat_map

    # ------------------------------------------------------------------
    # Books
    # ------------------------------------------------------------------

    def _seed_books(self, authors, categories, users):
        from apps.catalog.domain.models import Book

        librarian = users.get("librarian@nova.local")
        books = []
        for i, bd in enumerate(BOOKS_DATA):
            book, created = Book.objects.get_or_create(
                isbn_13=bd["isbn_13"],
                defaults={
                    "title": bd["title"],
                    "subtitle": bd.get("subtitle", ""),
                    "isbn_10": bd.get("isbn_10", ""),
                    "publisher": bd["publisher"],
                    "publication_date": bd.get("pub_date"),
                    "language": bd.get("language", "en"),
                    "page_count": bd.get("pages"),
                    "description": bd["description"],
                    "tags": bd.get("tags", []),
                    "dewey_decimal": bd.get("dewey", ""),
                    "added_by": librarian,
                },
            )
            if created:
                # Add authors
                for ai in BOOK_AUTHOR_MAP.get(i, []):
                    book.authors.add(authors[ai])

                # Add categories
                for slug in BOOK_CATEGORY_MAP.get(i, []):
                    if slug in categories:
                        book.categories.add(categories[slug])

                self.stdout.write(f"  + Book: {book.title}")
            books.append(book)

        return books

    # ------------------------------------------------------------------
    # Book Copies
    # ------------------------------------------------------------------

    def _seed_book_copies(self, books):
        from apps.catalog.domain.models import BookCopy

        copies = []
        conditions = ["NEW", "GOOD", "GOOD", "FAIR"]
        shelf_numbers = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2"]

        for book in books:
            existing = BookCopy.objects.filter(book=book).count()
            if existing > 0:
                copies.extend(list(BookCopy.objects.filter(book=book)))
                continue

            num_copies = random.randint(2, 4)
            for j in range(num_copies):
                bc = BookCopy.objects.create(
                    book=book,
                    barcode=f"NOVA-{book.isbn_13[-4:]}-{j+1:03d}",
                    condition=random.choice(conditions),
                    status="AVAILABLE",
                    floor_number=random.randint(1, 3),
                    shelf_number=random.choice(shelf_numbers),
                    branch="main",
                    acquisition_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
                    acquisition_price=Decimal(str(round(random.uniform(15.00, 85.00), 2))),
                    supplier=random.choice(["Book Distributors Ltd", "Academic Press Supply", "Global Books"]),
                )
                copies.append(bc)

            book.update_copy_counts()

        self.stdout.write(f"  + Book copies: {len(copies)} total")
        return copies

    # ------------------------------------------------------------------
    # Borrow Records + Fines
    # ------------------------------------------------------------------

    def _seed_borrows(self, users, copies, books):
        from apps.circulation.domain.models import BorrowRecord, Fine, Reservation
        from apps.catalog.domain.models import BookCopy

        if BorrowRecord.objects.exists():
            self.stdout.write("  ~ Borrows exist, skipping.")
            return

        librarian = users["librarian@nova.local"]
        member_users = [
            users["admin@nova.local"], users["librarian@nova.local"],
            users["alice@nova.local"], users["bob@nova.local"], users["charlie@nova.local"],
        ]
        now = timezone.now()

        borrow_count = 0
        reservation_count = 0

        # Past returned borrows (6 per user) — each has a fulfilled reservation
        for user in member_users:
            for offset in range(6):
                borrow_date = now - timedelta(days=random.randint(30, 180))
                due = borrow_date + timedelta(days=14)
                returned_at = borrow_date + timedelta(days=random.randint(5, 18))
                is_overdue = returned_at > due

                avail_copies = [c for c in copies if c.status == "AVAILABLE"]
                if not avail_copies:
                    break
                copy = random.choice(avail_copies)

                # Create fulfilled reservation
                resv = Reservation.objects.create(
                    user=user,
                    book=copy.book,
                    assigned_copy=copy,
                    status="FULFILLED",
                    reserved_at=borrow_date - timedelta(hours=2),
                    ready_at=borrow_date - timedelta(hours=1),
                    expires_at=borrow_date + timedelta(hours=11),
                    fulfilled_at=borrow_date,
                    queue_position=0,
                )
                reservation_count += 1

                rec = BorrowRecord.objects.create(
                    user=user,
                    book_copy=copy,
                    reservation=resv,
                    status="RETURNED",
                    borrowed_at=borrow_date,
                    due_date=due,
                    returned_at=returned_at,
                    condition_at_borrow=copy.condition,
                    condition_at_return=copy.condition,
                    issued_by=librarian,
                    returned_to=librarian,
                )
                borrow_count += 1

                # Create a fine for overdue returns
                if is_overdue:
                    days_late = (returned_at - due).days
                    amount = Decimal(str(round(days_late * 0.50, 2)))
                    Fine.objects.create(
                        user=user,
                        borrow_record=rec,
                        reason="OVERDUE",
                        status=random.choice(["PAID", "PAID", "WAIVED"]),
                        amount=amount,
                        paid_amount=amount if random.random() > 0.3 else Decimal("0.00"),
                        waived_by=librarian if random.random() > 0.7 else None,
                    )

                copy.book.increment_borrow_count()

        # Active borrows (1-2 per user)
        for user in member_users:
            for _ in range(random.randint(1, 2)):
                avail_copies = [c for c in copies if c.status == "AVAILABLE"]
                if not avail_copies:
                    break
                copy = random.choice(avail_copies)
                borrow_date = now - timedelta(days=random.randint(2, 10))
                due = borrow_date + timedelta(days=14)

                resv = Reservation.objects.create(
                    user=user,
                    book=copy.book,
                    assigned_copy=copy,
                    status="FULFILLED",
                    reserved_at=borrow_date - timedelta(hours=2),
                    ready_at=borrow_date - timedelta(hours=1),
                    expires_at=borrow_date + timedelta(hours=11),
                    fulfilled_at=borrow_date,
                    queue_position=0,
                )
                reservation_count += 1

                BorrowRecord.objects.create(
                    user=user,
                    book_copy=copy,
                    reservation=resv,
                    status="ACTIVE",
                    borrowed_at=borrow_date,
                    due_date=due,
                    condition_at_borrow=copy.condition,
                    issued_by=librarian,
                )
                copy.mark_borrowed()
                copy.book.increment_borrow_count()
                borrow_count += 1

        # 1 overdue borrow for bob
        avail_copies = [c for c in copies if c.status == "AVAILABLE"]
        if avail_copies:
            copy = avail_copies[0]
            borrow_date = now - timedelta(days=20)
            due = borrow_date + timedelta(days=14)

            resv = Reservation.objects.create(
                user=users["bob@nova.local"],
                book=copy.book,
                assigned_copy=copy,
                status="FULFILLED",
                reserved_at=borrow_date - timedelta(hours=2),
                ready_at=borrow_date - timedelta(hours=1),
                expires_at=borrow_date + timedelta(hours=11),
                fulfilled_at=borrow_date,
                queue_position=0,
            )
            reservation_count += 1

            ov_rec = BorrowRecord.objects.create(
                user=users["bob@nova.local"],
                book_copy=copy,
                reservation=resv,
                status="OVERDUE",
                borrowed_at=borrow_date,
                due_date=due,
                condition_at_borrow=copy.condition,
                issued_by=librarian,
            )
            copy.mark_borrowed()
            days_overdue = (now - due).days
            Fine.objects.create(
                user=users["bob@nova.local"],
                borrow_record=ov_rec,
                reason="OVERDUE",
                status="PENDING",
                amount=Decimal(str(round(days_overdue * 0.50, 2))),
                paid_amount=Decimal("0.00"),
            )
            borrow_count += 1

        # Create some active reservations (PENDING and READY) for demo
        avail_copies = [c for c in copies if c.status == "AVAILABLE"]
        demo_user = users["alice@nova.local"]

        # READY reservation for alice
        if avail_copies:
            copy = avail_copies[0]
            resv = Reservation.objects.create(
                user=demo_user,
                book=copy.book,
                status="PENDING",
                reserved_at=now - timedelta(minutes=30),
                queue_position=0,
            )
            resv.mark_ready(copy)
            reservation_count += 1

        # PENDING reservation for charlie (no copies available for that book)
        if len(books) > 10:
            Reservation.objects.create(
                user=users["charlie@nova.local"],
                book=books[10],
                status="PENDING",
                reserved_at=now - timedelta(hours=2),
                queue_position=1,
            )
            reservation_count += 1

        self.stdout.write(f"  + Borrow records: {borrow_count}, Reservations: {reservation_count}")

    # ------------------------------------------------------------------
    # Digital Assets
    # ------------------------------------------------------------------

    def _seed_digital_assets(self, books, users):
        from apps.digital_content.domain.models import DigitalAsset, UserLibrary

        if DigitalAsset.objects.exists():
            self.stdout.write("  ~ Digital assets exist, skipping.")
            return

        librarian = users["librarian@nova.local"]
        asset_count = 0

        for book in books[:10]:  # first 10 books get e-book assets
            da = DigitalAsset.objects.create(
                book=book,
                asset_type="EBOOK_PDF",
                file_path=f"digital/{book.isbn_13}/content.pdf",
                file_size_bytes=random.randint(1_000_000, 50_000_000),
                file_hash=f"sha256:{uuid4().hex}",
                mime_type="application/pdf",
                total_pages=book.page_count or 300,
                is_drm_protected=False,
                upload_completed=True,
                uploaded_by=librarian,
            )
            asset_count += 1

            # Add to libraries for active users
            for email in ["alice@nova.local", "bob@nova.local", "charlie@nova.local"]:
                if random.random() > 0.3:
                    UserLibrary.objects.create(
                        user=users[email],
                        digital_asset=da,
                        overall_progress=round(random.uniform(0, 80), 2),
                        total_time_seconds=random.randint(600, 7200),
                        is_finished=random.random() > 0.8,
                        is_favorite=random.random() > 0.7,
                    )

        # First 3 books also get audiobook
        for book in books[:3]:
            DigitalAsset.objects.create(
                book=book,
                asset_type="AUDIOBOOK",
                file_path=f"digital/{book.isbn_13}/audio.mp3",
                file_size_bytes=random.randint(50_000_000, 300_000_000),
                file_hash=f"sha256:{uuid4().hex}",
                mime_type="audio/mpeg",
                duration_seconds=random.randint(10800, 43200),
                narrator=random.choice(["James Earl Jones", "Morgan Freeman", "Emma Watson"]),
                is_drm_protected=False,
                upload_completed=True,
                uploaded_by=librarian,
            )
            asset_count += 1

        self.stdout.write(f"  + Digital assets: {asset_count}")

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    def _seed_reviews(self, books, users):
        from apps.catalog.domain.models import BookReview

        if BookReview.objects.exists():
            self.stdout.write("  ~ Reviews exist, skipping.")
            return

        reviewers = [users["alice@nova.local"], users["bob@nova.local"], users["charlie@nova.local"]]
        count = 0

        for book in books[:12]:
            num_reviews = random.randint(1, 3)
            selected = random.sample(reviewers, min(num_reviews, len(reviewers)))
            for user in selected:
                title, content = random.choice(REVIEW_TEXTS)
                BookReview.objects.create(
                    book=book,
                    user=user,
                    rating=random.randint(3, 5),
                    title=title,
                    content=content,
                )
                count += 1

        # Recalculate ratings
        for book in books[:12]:
            reviews = book.reviews.all()
            if reviews.exists():
                avg = sum(r.rating for r in reviews) / reviews.count()
                book.average_rating = round(Decimal(str(avg)), 2)
                book.rating_count = reviews.count()
                book.save(update_fields=["average_rating", "rating_count"])

        self.stdout.write(f"  + Reviews: {count}")

    # ------------------------------------------------------------------
    # Engagement
    # ------------------------------------------------------------------

    def _seed_engagement(self, users):
        from apps.engagement.domain.models import UserEngagement, DailyActivity

        if UserEngagement.objects.exists():
            self.stdout.write("  ~ Engagement exists, skipping.")
            return

        engagement_data = {
            "admin@nova.local": {"total_kp": 250, "level": 2, "level_title": "Avid Reader",
                                  "current_streak": 5, "longest_streak": 10, "explorer_kp": 60,
                                  "scholar_kp": 90, "connector_kp": 40, "achiever_kp": 35, "dedicated_kp": 25},
            "librarian@nova.local": {"total_kp": 920, "level": 5, "level_title": "Knowledge Keeper",
                                      "current_streak": 18, "longest_streak": 30, "explorer_kp": 200,
                                      "scholar_kp": 350, "connector_kp": 150, "achiever_kp": 120, "dedicated_kp": 100},
            "alice@nova.local": {"total_kp": 680, "level": 4, "level_title": "Bibliophile",
                                  "current_streak": 12, "longest_streak": 15, "explorer_kp": 150,
                                  "scholar_kp": 280, "connector_kp": 100, "achiever_kp": 80, "dedicated_kp": 70},
            "bob@nova.local": {"total_kp": 350, "level": 3, "level_title": "Scholar",
                                "current_streak": 3, "longest_streak": 8, "explorer_kp": 80,
                                "scholar_kp": 140, "connector_kp": 50, "achiever_kp": 50, "dedicated_kp": 30},
            "charlie@nova.local": {"total_kp": 1620, "level": 6, "level_title": "Sage",
                                    "current_streak": 25, "longest_streak": 25, "explorer_kp": 350,
                                    "scholar_kp": 500, "connector_kp": 300, "achiever_kp": 270, "dedicated_kp": 200},
            "diana@nova.local": {"total_kp": 45, "level": 1, "level_title": "Novice Reader",
                                  "current_streak": 0, "longest_streak": 2, "explorer_kp": 20,
                                  "scholar_kp": 15, "connector_kp": 5, "achiever_kp": 3, "dedicated_kp": 2},
        }

        for email, data in engagement_data.items():
            user = users.get(email)
            if not user:
                continue
            UserEngagement.objects.create(
                user=user,
                last_activity_date=timezone.now().date() - timedelta(days=random.randint(0, 2)),
                **data,
            )

        # Daily activities for past 7 days for active users
        today = timezone.now().date()
        for email in ["admin@nova.local", "librarian@nova.local", "alice@nova.local", "bob@nova.local", "charlie@nova.local"]:
            user = users[email]
            for day_offset in range(7):
                d = today - timedelta(days=day_offset)
                DailyActivity.objects.get_or_create(
                    user=user,
                    date=d,
                    defaults={
                        "kp_earned": random.randint(5, 45),
                        "books_borrowed": 1 if day_offset == 0 else 0,
                        "reading_minutes": random.randint(10, 90),
                        "pages_read": random.randint(5, 40),
                        "reviews_written": 1 if day_offset == 3 else 0,
                        "sessions_completed": random.randint(0, 3),
                    },
                )

        self.stdout.write(f"  + Engagement profiles: {len(engagement_data)}, daily activities: 21")

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------

    def _seed_achievements(self, users):
        from apps.engagement.domain.models import Achievement, UserAchievement

        if Achievement.objects.exists():
            self.stdout.write("  ~ Achievements exist, skipping.")
            return

        achievements = []
        for i, ad in enumerate(ACHIEVEMENT_DATA):
            obj = Achievement.objects.create(
                code=ad["code"],
                name=ad["name"],
                description=ad["description"],
                category=ad["category"],
                rarity=ad["rarity"],
                kp_reward=ad["kp_reward"],
                criteria={},
                sort_order=i + 1,
            )
            achievements.append(obj)

        # Award some achievements to users
        earned_map = {
            "admin@nova.local": [0, 5, 7],                # FIRST_BORROW, 100_PAGES, EXPLORER
            "librarian@nova.local": [0, 1, 2, 3, 5, 7],   # Multiple achievements
            "alice@nova.local": [0, 2, 3, 5, 7],    # FIRST_BORROW, FIRST_REVIEW, STREAK_7, 100_PAGES, EXPLORER
            "bob@nova.local": [0, 5, 9],              # FIRST_BORROW, 100_PAGES, FIRST_HIGHLIGHT
            "charlie@nova.local": [0, 1, 2, 3, 4, 5, 6, 7, 9],  # Almost all
        }

        count = 0
        for email, indices in earned_map.items():
            user = users.get(email)
            if not user:
                continue
            for ai in indices:
                UserAchievement.objects.create(
                    user=user,
                    achievement=achievements[ai],
                    earned_at=timezone.now() - timedelta(days=random.randint(1, 60)),
                    kp_awarded=achievements[ai].kp_reward,
                    notified=True,
                )
                count += 1

        self.stdout.write(f"  + Achievements: {len(achievements)}, awarded: {count}")

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def _seed_recommendations(self, users, books):
        from apps.intelligence.domain.models import Recommendation, UserPreference

        if Recommendation.objects.exists():
            self.stdout.write("  ~ Recommendations exist, skipping.")
            return

        strategies = ["COLLABORATIVE", "CONTENT_BASED", "HYBRID", "TRENDING"]
        count = 0

        for email in ["admin@nova.local", "librarian@nova.local", "alice@nova.local", "bob@nova.local", "charlie@nova.local"]:
            user = users[email]

            # User preference profile
            UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    "preferred_categories": ["software-engineering", "algorithms"],
                    "preferred_authors": [],
                    "preferred_languages": ["en"],
                    "reading_speed": "average",
                    "last_computed_at": timezone.now(),
                },
            )

            # 5 recommendations per user
            rec_books = random.sample(books, min(5, len(books)))
            for i, book in enumerate(rec_books):
                Recommendation.objects.create(
                    user=user,
                    book=book,
                    strategy=random.choice(strategies),
                    score=round(random.uniform(0.55, 0.98), 3),
                    explanation=f"Recommended because you enjoyed similar titles in {book.categories.first() or 'your library'}.",
                    is_dismissed=False,
                    is_clicked=random.random() > 0.6,
                )
                count += 1

        self.stdout.write(f"  + Recommendations: {count}")

    # ------------------------------------------------------------------
    # Trending
    # ------------------------------------------------------------------

    def _seed_trending(self, books):
        from apps.intelligence.domain.models import TrendingBook

        if TrendingBook.objects.exists():
            self.stdout.write("  ~ Trending exists, skipping.")
            return

        periods = ["DAILY", "WEEKLY", "MONTHLY"]
        count = 0

        for period in periods:
            ranked = random.sample(books, min(10, len(books)))
            for rank, book in enumerate(ranked, 1):
                TrendingBook.objects.create(
                    book=book,
                    period=period,
                    rank=rank,
                    borrow_count=random.randint(5, 50),
                    view_count=random.randint(20, 200),
                    review_count=random.randint(0, 10),
                    score=round(random.uniform(10, 100), 2),
                )
                count += 1

        self.stdout.write(f"  + Trending entries: {count}")

    # ------------------------------------------------------------------
    # Audit Logs
    # ------------------------------------------------------------------

    def _seed_audit_logs(self, users):
        from apps.governance.domain.models import AuditLog

        if AuditLog.objects.count() > 10:
            self.stdout.write("  ~ Audit logs exist, skipping.")
            return

        admin = users["admin@nova.local"]
        librarian = users["librarian@nova.local"]

        logs = [
            {"action": "SYSTEM", "resource_type": "System", "description": "Database seeded with test data.",
             "actor_id": admin.id, "actor_email": admin.email, "actor_role": admin.role},
            {"action": "LOGIN", "resource_type": "User", "description": "Admin logged in.",
             "actor_id": admin.id, "actor_email": admin.email, "actor_role": admin.role,
             "ip_address": "127.0.0.1"},
            {"action": "LOGIN", "resource_type": "User", "description": "Librarian logged in.",
             "actor_id": librarian.id, "actor_email": librarian.email, "actor_role": librarian.role,
             "ip_address": "127.0.0.1"},
        ]

        for member_email in ["alice@nova.local", "bob@nova.local", "charlie@nova.local"]:
            u = users[member_email]
            logs.append({
                "action": "REGISTER", "resource_type": "User",
                "resource_id": str(u.id),
                "description": f"New user registered: {u.email}",
                "actor_id": u.id, "actor_email": u.email, "actor_role": u.role,
                "ip_address": "127.0.0.1",
            })
            logs.append({
                "action": "BORROW", "resource_type": "BorrowRecord",
                "description": f"{u.email} borrowed a book.",
                "actor_id": u.id, "actor_email": u.email, "actor_role": u.role,
                "ip_address": "127.0.0.1",
            })

        for log_data in logs:
            AuditLog.objects.create(**log_data)

        self.stdout.write(f"  + Audit logs: {len(logs)}")

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    def _seed_assets(self, users):
        from apps.asset_management.domain.models import AssetCategory, Asset, MaintenanceLog
        from datetime import date, timedelta

        # Categories
        furniture = AssetCategory.objects.create(name='Furniture', slug='furniture', icon='chair', description='Library furniture')
        electronics = AssetCategory.objects.create(name='Electronics', slug='electronics', icon='computer', description='Electronic equipment')
        hvac = AssetCategory.objects.create(name='HVAC', slug='hvac', icon='air', description='Heating, ventilation, air conditioning')
        tables = AssetCategory.objects.create(name='Tables', slug='tables', icon='table', description='Reading and study tables', parent=furniture)
        shelving = AssetCategory.objects.create(name='Shelving', slug='shelving', icon='bookshelf', description='Book shelves and display units', parent=furniture)

        today = date.today()
        librarian = users.get('librarian@nova.local')

        assets_data = [
            {'asset_tag': 'AST-001', 'name': 'Main Reading Table (Oak)', 'category': tables,
             'status': 'ACTIVE', 'condition': 'GOOD', 'floor_number': 1, 'room': 'Main Reading Hall',
             'purchase_date': today - timedelta(days=730), 'purchase_price': 1200.00,
             'supplier': 'LibFurniture Inc', 'warranty_expiry': today + timedelta(days=365),
             'useful_life_years': 15, 'manufacturer': 'OakCraft', 'serial_number': 'OC-TBL-4821'},
            {'asset_tag': 'AST-002', 'name': 'Self-Checkout Kiosk #1', 'category': electronics,
             'status': 'ACTIVE', 'condition': 'EXCELLENT', 'floor_number': 1, 'room': 'Entrance Lobby',
             'purchase_date': today - timedelta(days=180), 'purchase_price': 4500.00,
             'supplier': 'TechLib Solutions', 'warranty_expiry': today + timedelta(days=545),
             'useful_life_years': 7, 'manufacturer': 'KioskPro', 'model_number': 'KP-3000',
             'serial_number': 'KP3-9182', 'assigned_to': librarian,
             'next_maintenance_date': today + timedelta(days=60), 'maintenance_interval_days': 90},
            {'asset_tag': 'AST-003', 'name': 'Central AC Unit - Floor 2', 'category': hvac,
             'status': 'ACTIVE', 'condition': 'FAIR', 'floor_number': 2, 'room': 'Mechanical Room',
             'purchase_date': today - timedelta(days=1460), 'purchase_price': 8500.00,
             'supplier': 'CoolAir Ltd', 'warranty_expiry': today - timedelta(days=365),
             'useful_life_years': 12, 'manufacturer': 'CoolAir', 'model_number': 'CA-5000',
             'serial_number': 'CA5-0034',
             'next_maintenance_date': today - timedelta(days=10), 'maintenance_interval_days': 180},
            {'asset_tag': 'AST-004', 'name': 'Metal Book Shelving Unit A1', 'category': shelving,
             'status': 'ACTIVE', 'condition': 'GOOD', 'floor_number': 1, 'room': 'Fiction Section',
             'purchase_date': today - timedelta(days=1095), 'purchase_price': 850.00,
             'supplier': 'ShelfMax', 'useful_life_years': 20, 'manufacturer': 'ShelfMax',
             'serial_number': 'SM-SHV-112'},
            {'asset_tag': 'AST-005', 'name': 'HP LaserJet Pro MFP', 'category': electronics,
             'status': 'UNDER_MAINTENANCE', 'condition': 'POOR', 'floor_number': 1, 'room': 'Print Station',
             'purchase_date': today - timedelta(days=900), 'purchase_price': 650.00,
             'supplier': 'HP Direct', 'warranty_expiry': today - timedelta(days=180),
             'useful_life_years': 5, 'manufacturer': 'HP', 'model_number': 'M428fdw',
             'serial_number': 'HP-M428-7291'},
            {'asset_tag': 'AST-006', 'name': 'Ergonomic Study Chair (Set of 20)', 'category': furniture,
             'status': 'ACTIVE', 'condition': 'GOOD', 'floor_number': 2, 'room': 'Study Area',
             'purchase_date': today - timedelta(days=365), 'purchase_price': 3200.00,
             'supplier': 'ErgoSeating Co', 'useful_life_years': 10,
             'manufacturer': 'ErgoSeating', 'serial_number': 'ES-CHR-BATCH20'},
        ]

        created = []
        for data in assets_data:
            created.append(Asset.objects.create(**data))

        # Add maintenance logs
        MaintenanceLog.objects.create(
            asset=created[1], maintenance_type='PREVENTIVE',
            description='Quarterly touchscreen calibration and software update',
            performed_by=librarian, performed_date=today - timedelta(days=30),
            cost=150.00, vendor='TechLib Solutions', condition_after='EXCELLENT',
        )
        MaintenanceLog.objects.create(
            asset=created[4], maintenance_type='CORRECTIVE',
            description='Paper jam mechanism repair, replaced rollers',
            performed_by=librarian, performed_date=today - timedelta(days=5),
            cost=250.00, vendor='HP Authorized Service',
            notes='Awaiting replacement toner cartridge',
        )

        self.stdout.write(f"  + Assets: {len(created)} assets, 5 categories")

    # ------------------------------------------------------------------
    # HR / Employees
    # ------------------------------------------------------------------

    def _seed_hr(self, users):
        from apps.hr.domain.models import Department, Employee, JobVacancy, JobApplication
        from datetime import date, timedelta

        today = date.today()

        # Departments
        circulation_dept = Department.objects.create(name='Circulation Services', code='CIRC', description='Handles book lending, returns, and reservations')
        reference_dept = Department.objects.create(name='Reference & Research', code='REF', description='Assists patrons with research queries and reference materials')
        it_dept = Department.objects.create(name='IT & Digital Services', code='IT', description='Manages technology infrastructure and digital library systems')
        admin_dept = Department.objects.create(name='Administration', code='ADMIN', description='Library management and administrative functions')

        admin_user = users.get('admin@nova.local')
        librarian_user = users.get('librarian@nova.local')
        assistant_user = users.get('assistant@nova.local')

        # Employees
        admin_emp = Employee.objects.create(
            user=admin_user, employee_id='EMP-001',
            department=admin_dept, job_title='Library Director',
            hire_date=today - timedelta(days=2190), employment_type='FULL_TIME',
            status='ACTIVE', salary=85000, salary_currency='USD',
        )
        librarian_emp = Employee.objects.create(
            user=librarian_user, employee_id='EMP-002',
            department=circulation_dept, job_title='Senior Librarian',
            hire_date=today - timedelta(days=1460), employment_type='FULL_TIME',
            status='ACTIVE', salary=62000, salary_currency='USD',
            reports_to=admin_emp,
        )
        assistant_emp = Employee.objects.create(
            user=assistant_user, employee_id='EMP-003',
            department=circulation_dept, job_title='Library Assistant',
            hire_date=today - timedelta(days=365), employment_type='FULL_TIME',
            status='ACTIVE', salary=38000, salary_currency='USD',
            reports_to=librarian_emp,
        )

        # Set department heads
        admin_dept.head = admin_emp
        admin_dept.save()
        circulation_dept.head = librarian_emp
        circulation_dept.save()

        # Job Vacancies
        vacancy1 = JobVacancy.objects.create(
            title='Digital Services Librarian',
            department=it_dept,
            description='We are seeking a Digital Services Librarian to manage our growing digital collections and online resources. The ideal candidate will have experience with digital library platforms and a passion for technology.',
            requirements='- MLS/MLIS degree from ALA-accredited program\n- 2+ years experience with digital library systems\n- Proficiency in metadata standards (Dublin Core, MARC)\n- Experience with content management systems',
            responsibilities='- Manage digital collection acquisition and organization\n- Maintain digital library platform and troubleshoot issues\n- Train staff on digital tools and resources\n- Develop digital literacy programs for patrons',
            experience_level='MID', employment_type='FULL_TIME',
            positions_available=1, salary_range_min=52000, salary_range_max=65000,
            status='OPEN', posted_by=admin_user, posted_date=today - timedelta(days=14),
            closing_date=today + timedelta(days=30),
            location='Nova Library - Main Campus',
        )
        vacancy2 = JobVacancy.objects.create(
            title='Part-Time Reference Assistant',
            department=reference_dept,
            description='Join our reference team to help patrons navigate research databases and library resources. Perfect for library science students seeking practical experience.',
            requirements='- Currently enrolled in or graduated from library science program\n- Strong communication and customer service skills\n- Familiarity with academic databases',
            experience_level='ENTRY', employment_type='PART_TIME',
            positions_available=2, salary_range_min=18, salary_range_max=22,
            status='OPEN', posted_by=admin_user, posted_date=today - timedelta(days=7),
            closing_date=today + timedelta(days=45),
            location='Nova Library - Reference Desk',
        )
        vacancy3 = JobVacancy.objects.create(
            title='Summer Intern - Children\'s Section',
            department=circulation_dept,
            description='Help organize and run summer reading programs for children.',
            requirements='- Interest in children\'s literature\n- Available June through August',
            experience_level='ENTRY', employment_type='INTERN',
            positions_available=3, status='DRAFT', posted_by=admin_user,
        )

        # Job Applications
        alice = users.get('alice@nova.local')
        bob = users.get('bob@nova.local')

        if alice:
            JobApplication.objects.create(
                vacancy=vacancy1, applicant=alice,
                applicant_name=f'{alice.first_name} {alice.last_name}',
                applicant_email=alice.email,
                cover_letter='I am excited to apply for the Digital Services Librarian position. With my background in library science and technology, I believe I can make a significant contribution to your digital initiatives.',
                status='UNDER_REVIEW', reviewed_by=admin_user,
                review_notes='Strong technical background. Schedule interview.',
            )
        if bob:
            JobApplication.objects.create(
                vacancy=vacancy2, applicant=bob,
                applicant_name=f'{bob.first_name} {bob.last_name}',
                applicant_email=bob.email,
                cover_letter='As a graduate student in Library Science, I would love the opportunity to gain hands-on experience at Nova Library.',
                status='SUBMITTED',
            )

        self.stdout.write(f"  + HR: 4 departments, 3 employees, 3 vacancies")

    # ------------------------------------------------------------------
    # System Settings
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Members (Library Patrons)
    # ------------------------------------------------------------------

    def _seed_members(self, users):
        from apps.identity.domain.models import Member
        from datetime import date, timedelta

        if Member.objects.exists():
            self.stdout.write("  ⏭  Members already exist — skipping.")
            return

        today = date.today()
        reader = users.get('reader@nova.local')
        student = users.get('student@nova.local')

        members_data = [
            {
                'membership_number': 'LIB-2025-0001',
                'first_name': 'Amara',
                'last_name': 'Perera',
                'email': 'amara.perera@example.com',
                'phone_number': '+94 71 234 5678',
                'date_of_birth': date(1990, 5, 14),
                'nic_number': '901345678V',
                'address': '42 Galle Road, Colombo 03',
                'membership_type': 'PUBLIC',
                'status': 'ACTIVE',
                'max_borrows': 5,
                'emergency_contact_name': 'Nimal Perera',
                'emergency_contact_phone': '+94 77 987 6543',
                'notes': 'Frequent visitor, interested in history.',
                'user': reader,
            },
            {
                'membership_number': 'LIB-2025-0002',
                'first_name': 'Kavindu',
                'last_name': 'Silva',
                'email': 'kavindu.s@campus.lk',
                'phone_number': '+94 76 543 2100',
                'date_of_birth': date(2002, 3, 22),
                'nic_number': '200256789012',
                'address': '105 University Ave, Peradeniya',
                'membership_type': 'STUDENT',
                'status': 'ACTIVE',
                'max_borrows': 8,
                'emergency_contact_name': 'Ranjith Silva',
                'emergency_contact_phone': '+94 71 111 2222',
                'notes': 'CS undergraduate, borrows tech books often.',
                'user': student,
            },
            {
                'membership_number': 'LIB-2025-0003',
                'first_name': 'Dr. Lakshmi',
                'last_name': 'Fernando',
                'email': 'l.fernando@university.lk',
                'phone_number': '+94 77 888 9999',
                'date_of_birth': date(1975, 11, 8),
                'nic_number': '757654321V',
                'address': '18 Faculty Lane, Colombo 07',
                'membership_type': 'FACULTY',
                'status': 'ACTIVE',
                'max_borrows': 15,
                'notes': 'Professor of Literature. High borrow limit.',
            },
            {
                'membership_number': 'LIB-2025-0004',
                'first_name': 'Dilshan',
                'last_name': 'Jayawardena',
                'email': 'dilshan.j@library.org',
                'phone_number': '+94 75 321 0000',
                'date_of_birth': date(1988, 7, 30),
                'address': '7 Library Rd, Kandy',
                'membership_type': 'STAFF',
                'status': 'ACTIVE',
                'max_borrows': 10,
            },
            {
                'membership_number': 'LIB-2025-0005',
                'first_name': 'Malini',
                'last_name': 'Wickramasinghe',
                'email': '',
                'phone_number': '+94 71 000 1111',
                'date_of_birth': date(1955, 1, 12),
                'address': '33 Temple Rd, Galle',
                'membership_type': 'SENIOR',
                'status': 'ACTIVE',
                'max_borrows': 5,
                'emergency_contact_name': 'Sunil Wickramasinghe',
                'emergency_contact_phone': '+94 77 222 3333',
                'notes': 'Senior patron — prefers large print.',
            },
            {
                'membership_number': 'LIB-2025-0006',
                'first_name': 'Ishara',
                'last_name': 'Bandara',
                'email': 'ishara.b@example.com',
                'phone_number': '+94 76 444 5555',
                'date_of_birth': date(2015, 9, 5),
                'address': '90 Park St, Nugegoda',
                'membership_type': 'CHILD',
                'status': 'ACTIVE',
                'max_borrows': 3,
                'emergency_contact_name': 'Chaminda Bandara',
                'emergency_contact_phone': '+94 71 666 7777',
                'notes': 'Junior reader program participant.',
            },
            {
                'membership_number': 'LIB-2024-0050',
                'first_name': 'Tharushi',
                'last_name': 'Rathnayake',
                'email': 'tharushi@old.lk',
                'phone_number': '+94 77 111 0000',
                'date_of_birth': date(1995, 4, 18),
                'address': '12 Old Lane, Matara',
                'membership_type': 'PUBLIC',
                'status': 'EXPIRED',
                'max_borrows': 5,
                'notes': 'Membership expired — awaiting renewal.',
            },
            {
                'membership_number': 'LIB-2024-0051',
                'first_name': 'Nuwan',
                'last_name': 'Dissanayake',
                'email': 'nuwan.d@example.com',
                'phone_number': '+94 75 222 3333',
                'date_of_birth': date(2000, 12, 1),
                'address': '55 Main St, Ratnapura',
                'membership_type': 'STUDENT',
                'status': 'SUSPENDED',
                'max_borrows': 0,
                'notes': 'Suspended for overdue items — 3 months.',
            },
        ]

        created = 0
        for m_data in members_data:
            user_link = m_data.pop('user', None)
            expiry = today + timedelta(days=365) if m_data.get('status') == 'ACTIVE' else None
            Member.objects.create(
                **m_data,
                user=user_link,
                expiry_date=expiry,
            )
            created += 1

        self.stdout.write(f"  + Members: {created} library patrons")

    # ------------------------------------------------------------------
    # System Settings
    # ------------------------------------------------------------------

    def _seed_system_settings(self):
        from apps.common.domain.settings_model import SystemSetting
        count = SystemSetting.sync_defaults()
        self.stdout.write(f"  + System settings: {count} defaults synced")

    # ------------------------------------------------------------------
    # Print credentials table
    # ------------------------------------------------------------------

    def _print_credentials(self, users):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Test Credentials ==="))
        self.stdout.write(f"  Password for ALL accounts: {DEFAULT_PASSWORD}\n")
        self.stdout.write(f"  {'Email':<30} {'Role':<15} {'Verified':<10} {'Active':<8}")
        self.stdout.write(f"  {'─' * 30} {'─' * 15} {'─' * 10} {'─' * 8}")
        for email, user in users.items():
            verified = "Yes" if user.is_verified else "No"
            active = "Yes" if user.is_active else "No"
            self.stdout.write(f"  {email:<30} {user.role:<15} {verified:<10} {active:<8}")
