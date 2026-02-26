"""
Nova — Seed Database Command (Advanced Edition)
====================================================
Populates the database with rich, realistic test data across all 10 bounded
contexts.  Every list-view page will show **20 + items** so the UI feels
production-grade during demos and development.

Usage:
    python manage.py seed_data              # Full seed
    python manage.py seed_data --flush      # Wipe existing data first
    python manage.py seed_data --minimal    # Only users + books (skip rest)

Test Credentials (all passwords = "NovaTest@2026"):
    ┌────────────────────────────────────┬──────────────┬──────────┐
    │ Email                              │ Role         │ Verified │
    ├────────────────────────────────────┼──────────────┼──────────┤
    │ admin@nova.local                   │ SUPER_ADMIN  │ Yes      │
    │ librarian@nova.local               │ LIBRARIAN    │ Yes      │
    │ assistant@nova.local               │ ASSISTANT    │ Yes      │
    │ alice@nova.local … (20 patrons)    │ USER         │ Mixed    │
    └────────────────────────────────────┴──────────────┴──────────┘
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PASSWORD = "NovaTest@2026"

# ── 30 Books ──────────────────────────────────────────────────────────────
BOOKS_DATA = [
    {"title": "Clean Code", "subtitle": "A Handbook of Agile Software Craftsmanship", "isbn_13": "9780132350884", "isbn_10": "0132350882", "publisher": "Prentice Hall", "pub_date": date(2008, 8, 1), "language": "en", "pages": 464, "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.", "dewey": "005.1", "tags": ["software engineering", "agile", "clean code"]},
    {"title": "Design Patterns", "subtitle": "Elements of Reusable Object-Oriented Software", "isbn_13": "9780201633610", "isbn_10": "0201633612", "publisher": "Addison-Wesley", "pub_date": date(1994, 10, 31), "language": "en", "pages": 395, "description": "Capturing a wealth of experience about the design of object-oriented software, four top-notch designers present a catalog of simple and succinct solutions.", "dewey": "005.12", "tags": ["design patterns", "OOP", "software architecture"]},
    {"title": "Introduction to Algorithms", "subtitle": "", "isbn_13": "9780262046305", "isbn_10": "0262046305", "publisher": "MIT Press", "pub_date": date(2022, 4, 5), "language": "en", "pages": 1312, "description": "A comprehensive introduction to the modern study of computer algorithms.", "dewey": "005.1", "tags": ["algorithms", "data structures", "computer science"]},
    {"title": "The Pragmatic Programmer", "subtitle": "Your Journey to Mastery", "isbn_13": "9780135957059", "isbn_10": "0135957052", "publisher": "Addison-Wesley", "pub_date": date(2019, 9, 23), "language": "en", "pages": 352, "description": "One of those rare tech books you'll read, re-read, and read again over the years.", "dewey": "005.1", "tags": ["pragmatic", "software development", "career"]},
    {"title": "Refactoring", "subtitle": "Improving the Design of Existing Code", "isbn_13": "9780134757599", "isbn_10": "0134757599", "publisher": "Addison-Wesley", "pub_date": date(2018, 11, 20), "language": "en", "pages": 448, "description": "For more than twenty years, experienced programmers worldwide have relied on Martin Fowler's Refactoring.", "dewey": "005.1", "tags": ["refactoring", "code quality", "design"]},
    {"title": "Structure and Interpretation of Computer Programs", "subtitle": "", "isbn_13": "9780262510875", "isbn_10": "0262510871", "publisher": "MIT Press", "pub_date": date(1996, 7, 25), "language": "en", "pages": 657, "description": "SICP has had a dramatic impact on computer science curricula over the past decade.", "dewey": "005.13", "tags": ["computer science", "scheme", "functional programming"]},
    {"title": "Artificial Intelligence: A Modern Approach", "subtitle": "", "isbn_13": "9780134610993", "isbn_10": "0134610997", "publisher": "Pearson", "pub_date": date(2020, 4, 28), "language": "en", "pages": 1115, "description": "The most comprehensive, up-to-date introduction to the theory and practice of artificial intelligence.", "dewey": "006.3", "tags": ["artificial intelligence", "machine learning", "AI"]},
    {"title": "The Art of Computer Programming", "subtitle": "Volume 1: Fundamental Algorithms", "isbn_13": "9780201896831", "isbn_10": "0201896834", "publisher": "Addison-Wesley", "pub_date": date(2011, 3, 3), "language": "en", "pages": 672, "description": "The bible of all fundamental algorithms and the work that taught many of today's software developers.", "dewey": "005.1", "tags": ["algorithms", "knuth", "fundamentals"]},
    {"title": "Domain-Driven Design", "subtitle": "Tackling Complexity in the Heart of Software", "isbn_13": "9780321125217", "isbn_10": "0321125215", "publisher": "Addison-Wesley", "pub_date": date(2003, 8, 30), "language": "en", "pages": 560, "description": "Eric Evans has written a fantastic book on how you can make the design of your software match your mental model.", "dewey": "005.1", "tags": ["DDD", "domain driven design", "software architecture"]},
    {"title": "Database Internals", "subtitle": "A Deep Dive into How Distributed Data Systems Work", "isbn_13": "9781492040347", "isbn_10": "1492040347", "publisher": "O'Reilly Media", "pub_date": date(2019, 10, 1), "language": "en", "pages": 373, "description": "When it comes to choosing, using, and maintaining a database, understanding its internals is essential.", "dewey": "005.74", "tags": ["databases", "distributed systems", "storage"]},
    {"title": "Python Crash Course", "subtitle": "A Hands-On, Project-Based Introduction to Programming", "isbn_13": "9781718502703", "isbn_10": "1718502702", "publisher": "No Starch Press", "pub_date": date(2023, 1, 10), "language": "en", "pages": 552, "description": "The world's best-selling guide to the Python programming language.", "dewey": "005.133", "tags": ["python", "programming", "beginner"]},
    {"title": "Designing Data-Intensive Applications", "subtitle": "The Big Ideas Behind Reliable, Scalable Systems", "isbn_13": "9781449373320", "isbn_10": "1449373321", "publisher": "O'Reilly Media", "pub_date": date(2017, 3, 16), "language": "en", "pages": 616, "description": "Data is at the center of many challenges in system design today.", "dewey": "005.7", "tags": ["distributed systems", "data engineering", "scalability"]},
    {"title": "Le Petit Prince", "subtitle": "", "isbn_13": "9782070612758", "isbn_10": "2070612759", "publisher": "Gallimard", "pub_date": date(2000, 6, 29), "language": "fr", "pages": 96, "description": "Le Petit Prince est une œuvre de langue française, la plus connue d'Antoine de Saint-Exupéry.", "dewey": "843", "tags": ["french literature", "classic", "children"]},
    {"title": "Don Quijote de la Mancha", "subtitle": "", "isbn_13": "9788420412146", "isbn_10": "8420412147", "publisher": "Alfaguara", "pub_date": date(2015, 3, 19), "language": "es", "pages": 1376, "description": "Considerada la primera novela moderna.", "dewey": "863", "tags": ["spanish literature", "classic", "novel"]},
    {"title": "Microservices Patterns", "subtitle": "With examples in Java", "isbn_13": "9781617294549", "isbn_10": "1617294543", "publisher": "Manning", "pub_date": date(2018, 10, 27), "language": "en", "pages": 520, "description": "Microservices Patterns teaches you 44 reusable patterns to reliably develop and deploy production-quality microservices.", "dewey": "005.1", "tags": ["microservices", "patterns", "architecture"]},
    # 15 additional books --------------------------------------------------
    {"title": "Clean Architecture", "subtitle": "A Craftsman's Guide to Software Structure", "isbn_13": "9780134494166", "isbn_10": "0134494164", "publisher": "Prentice Hall", "pub_date": date(2017, 9, 10), "language": "en", "pages": 432, "description": "Building on the success of Clean Code, Robert C. Martin presents the universal rules of software architecture.", "dewey": "005.1", "tags": ["architecture", "clean code", "SOLID"]},
    {"title": "Cracking the Coding Interview", "subtitle": "189 Programming Questions and Solutions", "isbn_13": "9780984782857", "isbn_10": "0984782850", "publisher": "CareerCup", "pub_date": date(2015, 7, 1), "language": "en", "pages": 687, "description": "The most expansive, detailed guide on how to ace the software engineering interview.", "dewey": "005.1", "tags": ["interview", "algorithms", "career"]},
    {"title": "Effective Java", "subtitle": "Third Edition", "isbn_13": "9780134685991", "isbn_10": "0134685997", "publisher": "Addison-Wesley", "pub_date": date(2018, 1, 6), "language": "en", "pages": 416, "description": "The definitive guide to Java platform best practices from Joshua Bloch.", "dewey": "005.133", "tags": ["java", "best practices", "programming"]},
    {"title": "The Mythical Man-Month", "subtitle": "Essays on Software Engineering", "isbn_13": "9780201835953", "isbn_10": "0201835959", "publisher": "Addison-Wesley", "pub_date": date(1995, 8, 12), "language": "en", "pages": 336, "description": "Few books on software project management have been as influential and timeless.", "dewey": "005.1", "tags": ["project management", "software engineering", "classic"]},
    {"title": "Computer Networking", "subtitle": "A Top-Down Approach", "isbn_13": "9780136681854", "isbn_10": "0136681859", "publisher": "Pearson", "pub_date": date(2021, 3, 1), "language": "en", "pages": 800, "description": "Unique among computer networking texts, this top-down approach to networking focuses on the application layer.", "dewey": "004.6", "tags": ["networking", "protocols", "internet"]},
    {"title": "Operating System Concepts", "subtitle": "Tenth Edition", "isbn_13": "9781119800361", "isbn_10": "1119800366", "publisher": "Wiley", "pub_date": date(2021, 5, 4), "language": "en", "pages": 992, "description": "Operating System Concepts continues to evolve to provide a solid theoretical foundation for understanding operating systems.", "dewey": "005.43", "tags": ["operating systems", "OS", "computer science"]},
    {"title": "Head First Design Patterns", "subtitle": "Building Extensible and Maintainable Software", "isbn_13": "9781492078005", "isbn_10": "1492078009", "publisher": "O'Reilly Media", "pub_date": date(2021, 1, 12), "language": "en", "pages": 672, "description": "You'll learn design principles and patterns that will make your code more flexible and resilient.", "dewey": "005.12", "tags": ["design patterns", "beginner", "OOP"]},
    {"title": "Learning Python", "subtitle": "Powerful Object-Oriented Programming", "isbn_13": "9781449355739", "isbn_10": "1449355730", "publisher": "O'Reilly Media", "pub_date": date(2013, 7, 6), "language": "en", "pages": 1648, "description": "Get a comprehensive, in-depth introduction to the core Python language.", "dewey": "005.133", "tags": ["python", "programming", "reference"]},
    {"title": "Eloquent JavaScript", "subtitle": "A Modern Introduction to Programming", "isbn_13": "9781593279509", "isbn_10": "1593279507", "publisher": "No Starch Press", "pub_date": date(2018, 12, 4), "language": "en", "pages": 472, "description": "Eloquent JavaScript dives into the JavaScript language to show programmers how to write beautiful, effective code.", "dewey": "005.133", "tags": ["javascript", "web", "programming"]},
    {"title": "Grokking Algorithms", "subtitle": "An Illustrated Guide for Programmers", "isbn_13": "9781617292231", "isbn_10": "1617292230", "publisher": "Manning", "pub_date": date(2016, 5, 1), "language": "en", "pages": 256, "description": "An easy-to-read, fully illustrated introduction to algorithms.", "dewey": "005.1", "tags": ["algorithms", "beginner", "illustrated"]},
    {"title": "System Design Interview", "subtitle": "An Insider's Guide", "isbn_13": "9798664653403", "isbn_10": "", "publisher": "Independently Published", "pub_date": date(2020, 6, 12), "language": "en", "pages": 322, "description": "Step-by-step framework for approaching system design questions in interviews.", "dewey": "005.1", "tags": ["system design", "interview", "architecture"]},
    {"title": "Code Complete", "subtitle": "A Practical Handbook of Software Construction", "isbn_13": "9780735619678", "isbn_10": "0735619670", "publisher": "Microsoft Press", "pub_date": date(2004, 6, 9), "language": "en", "pages": 960, "description": "A practical handbook for software construction that has been helping developers write better code for decades.", "dewey": "005.1", "tags": ["software construction", "best practices", "classic"]},
    {"title": "Working Effectively with Legacy Code", "subtitle": "", "isbn_13": "9780131177055", "isbn_10": "0131177052", "publisher": "Prentice Hall", "pub_date": date(2004, 9, 22), "language": "en", "pages": 456, "description": "Michael Feathers offers start-to-finish strategies for working more effectively with large, untested legacy code bases.", "dewey": "005.1", "tags": ["legacy code", "testing", "refactoring"]},
    {"title": "Cien años de soledad", "subtitle": "", "isbn_13": "9780307474728", "isbn_10": "0307474720", "publisher": "Vintage Español", "pub_date": date(2009, 2, 10), "language": "es", "pages": 496, "description": "La novela más emblemática de Gabriel García Márquez y una de las obras cumbre del realismo mágico.", "dewey": "863", "tags": ["spanish literature", "magic realism", "classic"]},
    {"title": "Les Misérables", "subtitle": "", "isbn_13": "9782070409228", "isbn_10": "2070409228", "publisher": "Gallimard", "pub_date": date(2001, 3, 1), "language": "fr", "pages": 1900, "description": "Victor Hugo's epic masterpiece of injustice, heroism, and love.", "dewey": "843", "tags": ["french literature", "classic", "novel"]},
]

# ── 25 Authors ────────────────────────────────────────────────────────────
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
    {"first_name": "Gayle", "last_name": "McDowell", "nationality": "American"},
    {"first_name": "Joshua", "last_name": "Bloch", "nationality": "American", "birth_date": date(1961, 8, 28)},
    {"first_name": "Frederick", "last_name": "Brooks", "nationality": "American", "birth_date": date(1931, 4, 19), "death_date": date(2022, 11, 17)},
    {"first_name": "James", "last_name": "Kurose", "nationality": "American"},
    {"first_name": "Abraham", "last_name": "Silberschatz", "nationality": "Israeli-American"},
    {"first_name": "Eric", "last_name": "Freeman", "nationality": "American"},
    {"first_name": "Mark", "last_name": "Lutz", "nationality": "American"},
    {"first_name": "Marijn", "last_name": "Haverbeke", "nationality": "Belgian"},
    {"first_name": "Aditya", "last_name": "Bhargava", "nationality": "American"},
    {"first_name": "Alex", "last_name": "Xu", "nationality": "American"},
    {"first_name": "Steve", "last_name": "McConnell", "nationality": "American"},
    {"first_name": "Michael", "last_name": "Feathers", "nationality": "American"},
    {"first_name": "Gabriel", "last_name": "García Márquez", "nationality": "Colombian", "birth_date": date(1927, 3, 6), "death_date": date(2014, 4, 17)},
    {"first_name": "Victor", "last_name": "Hugo", "nationality": "French", "birth_date": date(1802, 2, 26), "death_date": date(1885, 5, 22)},
]

# book_index → [author_indices]
BOOK_AUTHOR_MAP = {
    0: [0], 1: [1], 2: [2], 3: [3, 4], 4: [5], 5: [6], 6: [7], 7: [8],
    8: [9], 9: [10], 10: [11], 11: [12], 12: [13], 13: [14], 14: [15],
    15: [0],      # Clean Architecture
    16: [16],     # Cracking the Coding Interview
    17: [17],     # Effective Java
    18: [18],     # Mythical Man-Month
    19: [19],     # Computer Networking
    20: [20],     # Operating System Concepts
    21: [21],     # Head First Design Patterns
    22: [22],     # Learning Python
    23: [23],     # Eloquent JavaScript
    24: [24],     # Grokking Algorithms
    25: [25],     # System Design Interview
    26: [26],     # Code Complete
    27: [27],     # Working Effectively with Legacy Code
    28: [28],     # Cien años de soledad
    29: [29],     # Les Misérables
}

# ── Categories ────────────────────────────────────────────────────────────
CATEGORIES_DATA = [
    {"name": "Computer Science", "slug": "computer-science", "icon": "cpu", "sort_order": 1,
     "children": [
         {"name": "Algorithms & Data Structures", "slug": "algorithms", "icon": "code", "sort_order": 1},
         {"name": "Software Engineering", "slug": "software-engineering", "icon": "wrench", "sort_order": 2},
         {"name": "Artificial Intelligence", "slug": "artificial-intelligence", "icon": "sparkles", "sort_order": 3},
         {"name": "Databases", "slug": "databases", "icon": "circle-stack", "sort_order": 4},
         {"name": "Programming Languages", "slug": "programming-languages", "icon": "code-bracket", "sort_order": 5},
         {"name": "Operating Systems", "slug": "operating-systems", "icon": "server", "sort_order": 6},
         {"name": "Computer Networks", "slug": "computer-networks", "icon": "globe", "sort_order": 7},
     ]},
    {"name": "Literature", "slug": "literature", "icon": "book-open", "sort_order": 2,
     "children": [
         {"name": "Classic Literature", "slug": "classic-literature", "icon": "academic-cap", "sort_order": 1},
         {"name": "French Literature", "slug": "french-literature", "icon": "flag", "sort_order": 2},
         {"name": "Spanish Literature", "slug": "spanish-literature", "icon": "flag", "sort_order": 3},
     ]},
    {"name": "Architecture & Design", "slug": "architecture-design", "icon": "building-office", "sort_order": 3},
    {"name": "Career & Interview Prep", "slug": "career-interview", "icon": "briefcase", "sort_order": 4},
]

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
    15: ["software-engineering", "architecture-design"],
    16: ["algorithms", "career-interview"],
    17: ["programming-languages"],
    18: ["software-engineering"],
    19: ["computer-networks"],
    20: ["operating-systems"],
    21: ["software-engineering"],
    22: ["programming-languages"],
    23: ["programming-languages"],
    24: ["algorithms"],
    25: ["architecture-design", "career-interview"],
    26: ["software-engineering"],
    27: ["software-engineering"],
    28: ["spanish-literature", "classic-literature"],
    29: ["french-literature", "classic-literature"],
}

# ── Reviews ───────────────────────────────────────────────────────────────
REVIEW_TEXTS = [
    ("Excellent resource!", "Changed the way I think about software design. A must-read for every developer."),
    ("Very informative", "Comprehensive coverage of the topic. Some chapters are dense but worth the effort."),
    ("Good but dated", "The core ideas are timeless, even if some examples feel a bit old."),
    ("Outstanding", "One of the best technical books I've ever read. Clear explanations and practical advice."),
    ("Solid fundamentals", "Great for building a strong foundation. I keep coming back to it as a reference."),
    ("Highly recommended", "Practical, well-written, and full of insights from real-world experience."),
    ("Must own!", "Every serious professional should have this on their shelf."),
    ("Great for beginners", "Very accessible writing style. Perfect for newcomers to the field."),
    ("Deep and thorough", "Goes well beyond surface-level. Found myself highlighting almost every page."),
    ("Life-changing", "Reading this book fundamentally changed how I approach problem solving."),
]

# ── Achievements ──────────────────────────────────────────────────────────
ACHIEVEMENT_DATA = [
    {"code": "FIRST_BORROW", "name": "First Steps", "description": "Borrowed your first book.", "category": "BORROWING", "rarity": "COMMON", "kp_reward": 10},
    {"code": "BOOKWORM_10", "name": "Bookworm", "description": "Borrowed 10 books.", "category": "BORROWING", "rarity": "UNCOMMON", "kp_reward": 50},
    {"code": "BOOKWORM_25", "name": "Library Regular", "description": "Borrowed 25 books.", "category": "BORROWING", "rarity": "RARE", "kp_reward": 100},
    {"code": "FIRST_REVIEW", "name": "Critic's Debut", "description": "Wrote your first book review.", "category": "SOCIAL", "rarity": "COMMON", "kp_reward": 15},
    {"code": "REVIEWER_10", "name": "Prolific Critic", "description": "Wrote 10 book reviews.", "category": "SOCIAL", "rarity": "UNCOMMON", "kp_reward": 50},
    {"code": "STREAK_7", "name": "Week Warrior", "description": "Maintained a 7-day reading streak.", "category": "STREAK", "rarity": "UNCOMMON", "kp_reward": 30},
    {"code": "STREAK_30", "name": "Monthly Master", "description": "Maintained a 30-day reading streak.", "category": "STREAK", "rarity": "RARE", "kp_reward": 100},
    {"code": "STREAK_90", "name": "Quarterly Champion", "description": "Maintained a 90-day reading streak.", "category": "STREAK", "rarity": "EPIC", "kp_reward": 250},
    {"code": "READER_100_PAGES", "name": "Century Reader", "description": "Read 100 pages digitally.", "category": "READING", "rarity": "COMMON", "kp_reward": 20},
    {"code": "READER_1000_PAGES", "name": "Thousand-Page Turner", "description": "Read 1,000 pages digitally.", "category": "READING", "rarity": "RARE", "kp_reward": 75},
    {"code": "READER_5000_PAGES", "name": "Marathon Reader", "description": "Read 5,000 pages digitally.", "category": "READING", "rarity": "EPIC", "kp_reward": 200},
    {"code": "DIVERSE_3_CATS", "name": "Explorer", "description": "Borrowed from 3 different categories.", "category": "MILESTONE", "rarity": "UNCOMMON", "kp_reward": 25},
    {"code": "DIVERSE_5_CATS", "name": "Renaissance Reader", "description": "Borrowed from 5 different categories.", "category": "MILESTONE", "rarity": "RARE", "kp_reward": 75},
    {"code": "LEVEL_5", "name": "Thought Leader", "description": "Reached Level 5.", "category": "MILESTONE", "rarity": "LEGENDARY", "kp_reward": 200},
    {"code": "LEVEL_10", "name": "Knowledge Sage", "description": "Reached Level 10.", "category": "MILESTONE", "rarity": "LEGENDARY", "kp_reward": 500},
    {"code": "FIRST_HIGHLIGHT", "name": "Highlighter", "description": "Created your first highlight.", "category": "READING", "rarity": "COMMON", "kp_reward": 10},
    {"code": "FIRST_BOOKMARK", "name": "Bookmarker", "description": "Created your first bookmark.", "category": "READING", "rarity": "COMMON", "kp_reward": 10},
    {"code": "NIGHT_OWL", "name": "Night Owl", "description": "Read for 2 hours after midnight.", "category": "SPECIAL", "rarity": "UNCOMMON", "kp_reward": 30},
    {"code": "EARLY_BIRD", "name": "Early Bird", "description": "Started a reading session before 6 AM.", "category": "SPECIAL", "rarity": "UNCOMMON", "kp_reward": 30},
    {"code": "SPEED_READER", "name": "Speed Reader", "description": "Read 100 pages in a single session.", "category": "READING", "rarity": "RARE", "kp_reward": 60},
    {"code": "SOCIAL_BUTTERFLY", "name": "Social Butterfly", "description": "Reviewed 5 different books.", "category": "SOCIAL", "rarity": "UNCOMMON", "kp_reward": 40},
    {"code": "PERFECT_RETURN", "name": "Perfect Record", "description": "Returned 10 books on time with no fines.", "category": "BORROWING", "rarity": "UNCOMMON", "kp_reward": 35},
]


class Command(BaseCommand):
    help = "Seed the database with rich test data for all bounded contexts."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete all existing data before seeding.")
        parser.add_argument("--minimal", action="store_true", help="Seed only users + books (skip engagement, circulation, etc.).")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Nova Database Seeder (Advanced) ===\n"))

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
            self._seed_audit_logs(users, books)
            self._seed_assets(users)
            self._seed_hr(users)
            self._seed_members(users)
            self._seed_notifications(users, books)
            self._seed_book_views(users, books)
            self._seed_kp_ledger(users)
            self._seed_search_logs(users)
            self._seed_security_events(users)
            self._seed_role_configs()
            self._seed_system_settings()

        self._print_credentials(users)
        self.stdout.write(self.style.SUCCESS("\n✅ Seeding complete!\n"))

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------
    def _flush(self):
        from apps.governance.domain.models import AuditLog, SecurityEvent, KPLedger
        from apps.intelligence.domain.models import (
            Recommendation, UserPreference, SearchLog, TrendingBook, BookView,
            AIModelVersion, AIProviderConfig,
        )
        from apps.intelligence.infrastructure.notification_engine import UserNotification
        from apps.engagement.domain.models import UserEngagement, Achievement, UserAchievement, DailyActivity
        from apps.digital_content.domain.models import DigitalAsset, ReadingSession, Bookmark, Highlight, UserLibrary
        from apps.circulation.domain.models import BorrowRecord, Reservation, Fine, ReservationBan
        from apps.catalog.domain.models import BookReview, BookCopy, Book, Author, Category
        from apps.identity.domain.models import RefreshToken, VerificationRequest, User, Member, RoleConfig
        from apps.asset_management.domain.models import AssetDisposal, MaintenanceLog, Asset, AssetCategory
        from apps.hr.domain.models import JobApplication, JobVacancy, Employee, Department
        from apps.common.domain.settings_model import SystemSetting

        for model in [
            SystemSetting,
            JobApplication, JobVacancy, Employee, Department,
            AssetDisposal, MaintenanceLog, Asset, AssetCategory,
            KPLedger, SecurityEvent, AuditLog,
            AIProviderConfig, AIModelVersion,
            UserNotification, BookView, SearchLog,
            TrendingBook, Recommendation, UserPreference,
            UserAchievement, DailyActivity, UserEngagement, Achievement,
            Highlight, Bookmark, UserLibrary, ReadingSession, DigitalAsset,
            Fine, ReservationBan, Reservation, BorrowRecord,
            BookReview, BookCopy, Member, RoleConfig,
        ]:
            model.objects.all().delete()

        Book.objects.all().delete()
        Author.objects.all().delete()
        Category.objects.all().delete()
        RefreshToken.objects.all().delete()
        VerificationRequest.objects.all().delete()
        User.all_objects.all().delete()

        self.stdout.write(self.style.WARNING("  Flushed all data."))

    # ------------------------------------------------------------------
    # Users  (23 total: 3 staff + 20 patrons)
    # ------------------------------------------------------------------
    def _seed_users(self):
        from apps.identity.domain.models import User

        staff = [
            {"email": "admin@nova.local", "first_name": "System", "last_name": "Administrator",
             "role": "SUPER_ADMIN", "is_staff": True, "is_verified": True, "is_active": True,
             "verification_status": "APPROVED"},
            {"email": "librarian@nova.local", "first_name": "Sarah", "last_name": "Johnson",
             "role": "LIBRARIAN", "is_staff": True, "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "phone_number": "+94771234567"},
            {"email": "assistant@nova.local", "first_name": "Kumar", "last_name": "Perera",
             "role": "ASSISTANT", "is_staff": True, "is_verified": True, "is_active": True,
             "verification_status": "APPROVED", "phone_number": "+94779876543"},
        ]

        patrons = [
            {"email": "alice@nova.local", "first_name": "Alice", "last_name": "Fernando", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-001", "date_of_birth": date(2000, 5, 15)},
            {"email": "bob@nova.local", "first_name": "Bob", "last_name": "Silva", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-002", "date_of_birth": date(1998, 11, 22)},
            {"email": "charlie@nova.local", "first_name": "Charlie", "last_name": "Mendis", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-003", "date_of_birth": date(2001, 3, 8)},
            {"email": "diana@nova.local", "first_name": "Diana", "last_name": "Wickrama", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(1999, 7, 14)},
            {"email": "eve@nova.local", "first_name": "Eve", "last_name": "Rajapaksa", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(2002, 7, 30)},
            {"email": "frank@nova.local", "first_name": "Frank", "last_name": "De Mel", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-006"},
            {"email": "grace@nova.local", "first_name": "Grace", "last_name": "Pieris", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(2000, 1, 20)},
            {"email": "henry@nova.local", "first_name": "Henry", "last_name": "Jayawardena", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-008"},
            {"email": "iris@nova.local", "first_name": "Iris", "last_name": "Bandara", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(2001, 9, 5)},
            {"email": "jack@nova.local", "first_name": "Jack", "last_name": "Gunasekara", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-010"},
            {"email": "kate@nova.local", "first_name": "Kate", "last_name": "Wijesinghe", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(1997, 12, 3)},
            {"email": "liam@nova.local", "first_name": "Liam", "last_name": "Rathnayake", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "FAC-2024-001"},
            {"email": "maya@nova.local", "first_name": "Maya", "last_name": "Senanayake", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(2003, 2, 28)},
            {"email": "noah@nova.local", "first_name": "Noah", "last_name": "Herath", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "institution_id": "STU-2024-014"},
            {"email": "olivia@nova.local", "first_name": "Olivia", "last_name": "Kumarasinghe", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(2000, 6, 10)},
            {"email": "peter@nova.local", "first_name": "Peter", "last_name": "Samaraweera", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED"},
            {"email": "quinn@nova.local", "first_name": "Quinn", "last_name": "Pathirana", "role": "USER", "is_verified": True, "is_active": True, "verification_status": "APPROVED", "date_of_birth": date(1996, 8, 15)},
            {"email": "ruby@nova.local", "first_name": "Ruby", "last_name": "Dissanayake", "role": "USER", "is_verified": False, "is_active": True, "verification_status": "PENDING"},
            {"email": "sam@nova.local", "first_name": "Sam", "last_name": "Abeysekara", "role": "USER", "is_verified": False, "is_active": True, "verification_status": "PENDING", "date_of_birth": date(2004, 4, 1)},
            {"email": "tina@nova.local", "first_name": "Tina", "last_name": "Weerasinghe", "role": "USER", "is_verified": False, "is_active": True, "verification_status": "PENDING"},
        ]

        users = {}
        for spec in staff + patrons:
            email = spec.pop("email")
            user, created = User.objects.get_or_create(email=email, defaults=spec)
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                self.stdout.write(f"  + User: {email} ({user.role})")
            users[email] = user

        self.stdout.write(f"  → {len(users)} users total")
        return users

    # ------------------------------------------------------------------
    # Authors  (30 total)
    # ------------------------------------------------------------------
    def _seed_authors(self):
        from apps.catalog.domain.models import Author

        authors = []
        for a in AUTHORS_DATA:
            obj, created = Author.objects.get_or_create(
                first_name=a["first_name"], last_name=a["last_name"],
                defaults={
                    "nationality": a.get("nationality", ""),
                    "birth_date": a.get("birth_date"),
                    "death_date": a.get("death_date"),
                    "biography": f"{a['first_name']} {a['last_name']} is a renowned author.",
                },
            )
            authors.append(obj)
            if created:
                self.stdout.write(f"  + Author: {obj.full_name}")

        self.stdout.write(f"  → {len(authors)} authors total")
        return authors

    # ------------------------------------------------------------------
    # Categories (16 total)
    # ------------------------------------------------------------------
    def _seed_categories(self):
        from apps.catalog.domain.models import Category

        cat_map = {}
        for top in CATEGORIES_DATA:
            children = top.pop("children", [])
            parent, _ = Category.objects.get_or_create(
                slug=top["slug"],
                defaults={"name": top["name"], "icon": top.get("icon", ""), "sort_order": top.get("sort_order", 0), "description": f"Top-level category: {top['name']}"},
            )
            cat_map[top["slug"]] = parent
            for child in children:
                obj, _ = Category.objects.get_or_create(
                    slug=child["slug"],
                    defaults={"name": child["name"], "parent": parent, "icon": child.get("icon", ""), "sort_order": child.get("sort_order", 0), "description": f"Subcategory of {top['name']}"},
                )
                cat_map[child["slug"]] = obj

        self.stdout.write(f"  → {len(cat_map)} categories total")
        return cat_map

    # ------------------------------------------------------------------
    # Books  (30 total)
    # ------------------------------------------------------------------
    def _seed_books(self, authors, categories, users):
        from apps.catalog.domain.models import Book

        librarian = users.get("librarian@nova.local")
        books = []
        for i, bd in enumerate(BOOKS_DATA):
            book, created = Book.objects.get_or_create(
                isbn_13=bd["isbn_13"],
                defaults={
                    "title": bd["title"], "subtitle": bd.get("subtitle", ""),
                    "isbn_10": bd.get("isbn_10", ""), "publisher": bd["publisher"],
                    "publication_date": bd.get("pub_date"), "language": bd.get("language", "en"),
                    "page_count": bd.get("pages"), "description": bd["description"],
                    "tags": bd.get("tags", []), "dewey_decimal": bd.get("dewey", ""),
                    "added_by": librarian,
                },
            )
            if created:
                for ai in BOOK_AUTHOR_MAP.get(i, []):
                    if ai < len(authors):
                        book.authors.add(authors[ai])
                for slug in BOOK_CATEGORY_MAP.get(i, []):
                    if slug in categories:
                        book.categories.add(categories[slug])
                self.stdout.write(f"  + Book: {book.title}")
            books.append(book)

        self.stdout.write(f"  → {len(books)} books total")
        return books

    # ------------------------------------------------------------------
    # Book Copies  (~90 total)
    # ------------------------------------------------------------------
    def _seed_book_copies(self, books):
        from apps.catalog.domain.models import BookCopy

        copies = []
        conditions = ["NEW", "GOOD", "GOOD", "FAIR", "GOOD"]
        shelves = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "D1", "D2"]

        for book in books:
            existing = BookCopy.objects.filter(book=book).count()
            if existing > 0:
                copies.extend(list(BookCopy.objects.filter(book=book)))
                continue
            num = random.randint(2, 4)
            for j in range(num):
                bc = BookCopy.objects.create(
                    book=book,
                    barcode=f"NOVA-{book.isbn_13[-4:]}-{j+1:03d}",
                    condition=random.choice(conditions),
                    status="AVAILABLE",
                    floor_number=random.randint(1, 3),
                    shelf_number=random.choice(shelves),
                    branch="main",
                    acquisition_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
                    acquisition_price=Decimal(str(round(random.uniform(15.00, 85.00), 2))),
                    supplier=random.choice(["Book Distributors Ltd", "Academic Press Supply", "Global Books", "Online Wholesale"]),
                )
                copies.append(bc)
            book.update_copy_counts()

        self.stdout.write(f"  → {len(copies)} book copies total")
        return copies

    # ------------------------------------------------------------------
    # Borrows + Fines + Reservations  (large set for 20+ per page)
    # ------------------------------------------------------------------
    def _seed_borrows(self, users, copies, books):
        from apps.circulation.domain.models import BorrowRecord, Fine, Reservation
        from apps.catalog.domain.models import BookCopy

        if BorrowRecord.objects.exists():
            self.stdout.write("  ~ Borrows exist, skipping.")
            return

        librarian = users["librarian@nova.local"]
        patron_emails = [e for e in users if users[e].role == "USER" and users[e].is_verified]
        now = timezone.now()
        borrow_count = 0
        reservation_count = 0
        fine_count = 0

        # Past returned borrows — 4-8 per verified patron
        for email in patron_emails:
            user = users[email]
            num_past = random.randint(4, 8)
            for _ in range(num_past):
                avail = [c for c in copies if c.status == "AVAILABLE"]
                if not avail:
                    break
                copy = random.choice(avail)
                borrow_date = now - timedelta(days=random.randint(20, 200))
                due = borrow_date + timedelta(days=14)
                returned_at = borrow_date + timedelta(days=random.randint(5, 20))
                is_overdue = returned_at > due

                resv = Reservation.objects.create(
                    user=user, book=copy.book, assigned_copy=copy, status="FULFILLED",
                    reserved_at=borrow_date - timedelta(hours=2),
                    ready_at=borrow_date - timedelta(hours=1),
                    expires_at=borrow_date + timedelta(hours=11),
                    fulfilled_at=borrow_date, queue_position=0,
                )
                reservation_count += 1

                rec = BorrowRecord.objects.create(
                    user=user, book_copy=copy, reservation=resv, status="RETURNED",
                    borrowed_at=borrow_date, due_date=due, returned_at=returned_at,
                    condition_at_borrow=copy.condition, condition_at_return=copy.condition,
                    issued_by=librarian, returned_to=librarian,
                )
                borrow_count += 1

                if is_overdue:
                    days_late = (returned_at - due).days
                    amount = Decimal(str(round(days_late * 0.50, 2)))
                    Fine.objects.create(
                        user=user, borrow_record=rec, reason="OVERDUE",
                        status=random.choice(["PAID", "PAID", "WAIVED"]),
                        amount=amount,
                        paid_amount=amount if random.random() > 0.3 else Decimal("0.00"),
                        waived_by=librarian if random.random() > 0.7 else None,
                    )
                    fine_count += 1

                copy.book.increment_borrow_count()

        # Active borrows — 1-2 per first 15 users
        active_patrons = patron_emails[:15]
        for email in active_patrons:
            user = users[email]
            for _ in range(random.randint(1, 2)):
                avail = [c for c in copies if c.status == "AVAILABLE"]
                if not avail:
                    break
                copy = random.choice(avail)
                borrow_date = now - timedelta(days=random.randint(1, 10))
                due = borrow_date + timedelta(days=14)

                resv = Reservation.objects.create(
                    user=user, book=copy.book, assigned_copy=copy, status="FULFILLED",
                    reserved_at=borrow_date - timedelta(hours=2),
                    ready_at=borrow_date - timedelta(hours=1),
                    expires_at=borrow_date + timedelta(hours=11),
                    fulfilled_at=borrow_date, queue_position=0,
                )
                reservation_count += 1

                BorrowRecord.objects.create(
                    user=user, book_copy=copy, reservation=resv, status="ACTIVE",
                    borrowed_at=borrow_date, due_date=due,
                    condition_at_borrow=copy.condition, issued_by=librarian,
                )
                copy.mark_borrowed()
                copy.book.increment_borrow_count()
                borrow_count += 1

        # Overdue borrows — give 5 users an overdue borrow each
        for email in patron_emails[:5]:
            user = users[email]
            avail = [c for c in copies if c.status == "AVAILABLE"]
            if not avail:
                break
            copy = random.choice(avail)
            borrow_date = now - timedelta(days=random.randint(18, 30))
            due = borrow_date + timedelta(days=14)

            resv = Reservation.objects.create(
                user=user, book=copy.book, assigned_copy=copy, status="FULFILLED",
                reserved_at=borrow_date - timedelta(hours=2),
                ready_at=borrow_date - timedelta(hours=1),
                expires_at=borrow_date + timedelta(hours=11),
                fulfilled_at=borrow_date, queue_position=0,
            )
            reservation_count += 1

            ov_rec = BorrowRecord.objects.create(
                user=user, book_copy=copy, reservation=resv, status="OVERDUE",
                borrowed_at=borrow_date, due_date=due,
                condition_at_borrow=copy.condition, issued_by=librarian,
            )
            copy.mark_borrowed()
            days_overdue = max(1, (now - due).days)
            Fine.objects.create(
                user=user, borrow_record=ov_rec, reason="OVERDUE", status="PENDING",
                amount=Decimal(str(round(days_overdue * 0.50, 2))),
                paid_amount=Decimal("0.00"),
            )
            fine_count += 1
            borrow_count += 1

        # Active reservations: READY for 5, PENDING for 5
        for idx, email in enumerate(patron_emails[5:15]):
            user = users[email]
            avail = [c for c in copies if c.status == "AVAILABLE"]
            if not avail:
                break
            copy = random.choice(avail)
            if idx < 5:
                resv = Reservation.objects.create(
                    user=user, book=copy.book, status="PENDING",
                    reserved_at=now - timedelta(minutes=random.randint(10, 120)),
                    queue_position=0,
                )
                resv.mark_ready(copy)
            else:
                Reservation.objects.create(
                    user=user, book=books[random.randint(0, len(books)-1)],
                    status="PENDING",
                    reserved_at=now - timedelta(hours=random.randint(1, 12)),
                    queue_position=random.randint(1, 3),
                )
            reservation_count += 1

        self.stdout.write(f"  → Borrows: {borrow_count}, Reservations: {reservation_count}, Fines: {fine_count}")

    # ------------------------------------------------------------------
    # Digital Assets  (25 ebooks + 8 audiobooks)
    # ------------------------------------------------------------------
    def _seed_digital_assets(self, books, users):
        from apps.digital_content.domain.models import DigitalAsset, UserLibrary

        if DigitalAsset.objects.exists():
            self.stdout.write("  ~ Digital assets exist, skipping.")
            return

        librarian = users["librarian@nova.local"]
        patron_emails = [e for e in users if users[e].role == "USER" and users[e].is_verified]
        asset_count = 0

        # Ebooks for first 25 books
        for book in books[:25]:
            da = DigitalAsset.objects.create(
                book=book, asset_type="EBOOK_PDF",
                file_path=f"digital/{book.isbn_13}/content.pdf",
                file_size_bytes=random.randint(1_000_000, 50_000_000),
                file_hash=f"sha256:{uuid4().hex}", mime_type="application/pdf",
                total_pages=book.page_count or 300,
                is_drm_protected=False, upload_completed=True, uploaded_by=librarian,
            )
            asset_count += 1

            # Add to libraries for active users
            for email in random.sample(patron_emails, min(8, len(patron_emails))):
                UserLibrary.objects.create(
                    user=users[email], digital_asset=da,
                    overall_progress=round(random.uniform(0, 95), 2),
                    total_time_seconds=random.randint(300, 14400),
                    is_finished=random.random() > 0.75,
                    is_favorite=random.random() > 0.65,
                )

        # Audiobooks for first 8 books
        narrators = ["James Earl Jones", "Morgan Freeman", "Emma Watson", "Stephen Fry", "Scarlett Johansson", "Benedict Cumberbatch"]
        for book in books[:8]:
            DigitalAsset.objects.create(
                book=book, asset_type="AUDIOBOOK",
                file_path=f"digital/{book.isbn_13}/audio.mp3",
                file_size_bytes=random.randint(50_000_000, 300_000_000),
                file_hash=f"sha256:{uuid4().hex}", mime_type="audio/mpeg",
                duration_seconds=random.randint(10800, 43200),
                narrator=random.choice(narrators),
                is_drm_protected=False, upload_completed=True, uploaded_by=librarian,
            )
            asset_count += 1

        self.stdout.write(f"  → {asset_count} digital assets")

    # ------------------------------------------------------------------
    # Reviews  (60+ total — at least 2 per book)
    # ------------------------------------------------------------------
    def _seed_reviews(self, books, users):
        from apps.catalog.domain.models import BookReview

        if BookReview.objects.exists():
            self.stdout.write("  ~ Reviews exist, skipping.")
            return

        reviewer_emails = [e for e in users if users[e].role == "USER" and users[e].is_verified]
        reviewers = [users[e] for e in reviewer_emails]
        count = 0

        for book in books:
            num_reviews = random.randint(2, 4)
            selected = random.sample(reviewers, min(num_reviews, len(reviewers)))
            for user in selected:
                title, content = random.choice(REVIEW_TEXTS)
                BookReview.objects.create(
                    book=book, user=user,
                    rating=random.randint(3, 5), title=title, content=content,
                )
                count += 1

        # Recalculate ratings
        for book in books:
            reviews = book.reviews.all()
            if reviews.exists():
                avg = sum(r.rating for r in reviews) / reviews.count()
                book.average_rating = round(Decimal(str(avg)), 2)
                book.rating_count = reviews.count()
                book.save(update_fields=["average_rating", "rating_count"])

        self.stdout.write(f"  → {count} reviews")

    # ------------------------------------------------------------------
    # Engagement  (profiles for all verified users)
    # ------------------------------------------------------------------
    def _seed_engagement(self, users):
        from apps.engagement.domain.models import UserEngagement, DailyActivity

        if UserEngagement.objects.exists():
            self.stdout.write("  ~ Engagement exists, skipping.")
            return

        verified = {e: u for e, u in users.items() if u.is_verified}
        levels = [
            (50, 1, "Novice Reader"), (150, 2, "Avid Reader"), (350, 3, "Scholar"),
            (680, 4, "Bibliophile"), (920, 5, "Knowledge Keeper"), (1620, 6, "Sage"),
            (2500, 7, "Luminary"), (3200, 8, "Grand Scholar"),
        ]
        created = 0

        for email, user in verified.items():
            kp, level, title = random.choice(levels)
            kp = kp + random.randint(-30, 60)
            explorer = random.randint(20, 350)
            scholar = random.randint(15, 500)
            connector = random.randint(5, 300)
            achiever = random.randint(3, 270)
            dedicated = random.randint(2, 200)

            UserEngagement.objects.create(
                user=user,
                total_kp=kp, level=level, level_title=title,
                current_streak=random.randint(0, 30),
                longest_streak=random.randint(5, 45),
                explorer_kp=explorer, scholar_kp=scholar,
                connector_kp=connector, achiever_kp=achiever, dedicated_kp=dedicated,
                last_activity_date=timezone.now().date() - timedelta(days=random.randint(0, 3)),
            )
            created += 1

        # Daily activities for past 14 days for all verified users
        today = timezone.now().date()
        activity_count = 0
        for email, user in verified.items():
            for day_offset in range(14):
                d = today - timedelta(days=day_offset)
                DailyActivity.objects.get_or_create(
                    user=user, date=d,
                    defaults={
                        "kp_earned": random.randint(3, 55),
                        "books_borrowed": 1 if random.random() > 0.8 else 0,
                        "reading_minutes": random.randint(5, 120),
                        "pages_read": random.randint(2, 60),
                        "reviews_written": 1 if random.random() > 0.9 else 0,
                        "sessions_completed": random.randint(0, 4),
                    },
                )
                activity_count += 1

        self.stdout.write(f"  → {created} engagement profiles, {activity_count} daily activities")

    # ------------------------------------------------------------------
    # Achievements  (22 definitions, awards for many users)
    # ------------------------------------------------------------------
    def _seed_achievements(self, users):
        from apps.engagement.domain.models import Achievement, UserAchievement

        if Achievement.objects.exists():
            self.stdout.write("  ~ Achievements exist, skipping.")
            return

        achievements = []
        for i, ad in enumerate(ACHIEVEMENT_DATA):
            obj = Achievement.objects.create(
                code=ad["code"], name=ad["name"], description=ad["description"],
                category=ad["category"], rarity=ad["rarity"], kp_reward=ad["kp_reward"],
                criteria={}, sort_order=i + 1,
            )
            achievements.append(obj)

        verified = [e for e in users if users[e].role == "USER" and users[e].is_verified]
        count = 0
        for email in verified:
            user = users[email]
            # Each user earns 4-10 random achievements
            earned = random.sample(range(len(achievements)), random.randint(4, min(10, len(achievements))))
            for ai in earned:
                UserAchievement.objects.create(
                    user=user, achievement=achievements[ai],
                    earned_at=timezone.now() - timedelta(days=random.randint(1, 90)),
                    kp_awarded=achievements[ai].kp_reward, notified=True,
                )
                count += 1

        self.stdout.write(f"  → {len(achievements)} achievements, {count} awarded")

    # ------------------------------------------------------------------
    # Recommendations  (20 per user)
    # ------------------------------------------------------------------
    def _seed_recommendations(self, users, books):
        from apps.intelligence.domain.models import Recommendation, UserPreference

        if Recommendation.objects.exists():
            self.stdout.write("  ~ Recommendations exist, skipping.")
            return

        strategies = ["COLLABORATIVE", "CONTENT_BASED", "HYBRID", "TRENDING", "POPULAR", "SIMILAR_USERS", "CATEGORY_BASED"]
        verified = [e for e in users if users[e].is_verified]
        count = 0

        for email in verified:
            user = users[email]
            UserPreference.objects.get_or_create(
                user=user,
                defaults={
                    "preferred_categories": random.sample(["software-engineering", "algorithms", "databases", "programming-languages", "artificial-intelligence"], 3),
                    "preferred_authors": [], "preferred_languages": ["en"],
                    "reading_speed": random.choice(["slow", "average", "fast"]),
                    "last_computed_at": timezone.now(),
                },
            )

            rec_books = random.sample(books, min(20, len(books)))
            for book in rec_books:
                Recommendation.objects.create(
                    user=user, book=book,
                    strategy=random.choice(strategies),
                    score=round(random.uniform(0.45, 0.99), 3),
                    explanation=f"Based on your interest in {random.choice(book.tags) if book.tags else 'similar titles'}.",
                    is_dismissed=False, is_clicked=random.random() > 0.6,
                )
                count += 1

        self.stdout.write(f"  → {count} recommendations")

    # ------------------------------------------------------------------
    # Trending  (30 per period × 3 periods)
    # ------------------------------------------------------------------
    def _seed_trending(self, books):
        from apps.intelligence.domain.models import TrendingBook

        if TrendingBook.objects.exists():
            self.stdout.write("  ~ Trending exists, skipping.")
            return

        periods = ["DAILY", "WEEKLY", "MONTHLY"]
        count = 0
        for period in periods:
            ranked = random.sample(books, len(books))
            for rank, book in enumerate(ranked, 1):
                TrendingBook.objects.create(
                    book=book, period=period, rank=rank,
                    borrow_count=random.randint(3, 60),
                    view_count=random.randint(10, 300),
                    review_count=random.randint(0, 15),
                    score=round(random.uniform(5, 100), 2),
                )
                count += 1

        self.stdout.write(f"  → {count} trending entries")

    # ------------------------------------------------------------------
    # Audit Logs  (50+)
    # ------------------------------------------------------------------
    def _seed_audit_logs(self, users, books):
        from apps.governance.domain.models import AuditLog

        if AuditLog.objects.count() > 10:
            self.stdout.write("  ~ Audit logs exist, skipping.")
            return

        admin = users["admin@nova.local"]
        librarian = users["librarian@nova.local"]
        count = 0

        # System events
        for desc in ["Database seeded with test data", "System backup completed", "Cache cleared", "Celery workers restarted"]:
            AuditLog.objects.create(
                action="SYSTEM", resource_type="System", description=desc,
                actor_id=admin.id, actor_email=admin.email, actor_role=admin.role,
                ip_address="127.0.0.1",
            )
            count += 1

        # Login events
        for email in list(users.keys())[:15]:
            u = users[email]
            AuditLog.objects.create(
                action="LOGIN", resource_type="User", description=f"{u.email} logged in.",
                actor_id=u.id, actor_email=u.email, actor_role=u.role,
                ip_address=f"192.168.1.{random.randint(10, 200)}",
            )
            count += 1

        # Borrow events
        for email in [e for e in users if users[e].role == "USER"][:10]:
            u = users[email]
            book = random.choice(books)
            AuditLog.objects.create(
                action="BORROW", resource_type="BorrowRecord",
                description=f"{u.email} borrowed '{book.title}'.",
                actor_id=u.id, actor_email=u.email, actor_role=u.role,
                ip_address=f"192.168.1.{random.randint(10, 200)}",
            )
            count += 1

        # Register events
        for email in [e for e in users if users[e].role == "USER"][:10]:
            u = users[email]
            AuditLog.objects.create(
                action="REGISTER", resource_type="User", resource_id=str(u.id),
                description=f"New user registered: {u.email}",
                actor_id=u.id, actor_email=u.email, actor_role=u.role,
                ip_address=f"192.168.1.{random.randint(10, 200)}",
            )
            count += 1

        # Return events
        for email in [e for e in users if users[e].role == "USER"][:8]:
            u = users[email]
            book = random.choice(books)
            AuditLog.objects.create(
                action="RETURN", resource_type="BorrowRecord",
                description=f"{u.email} returned '{book.title}'.",
                actor_id=u.id, actor_email=u.email, actor_role=u.role,
                ip_address=f"192.168.1.{random.randint(10, 200)}",
            )
            count += 1

        # Settings changes
        for setting in ["max_borrows_per_user", "daily_kp_cap", "reservation_window_hours"]:
            AuditLog.objects.create(
                action="SETTINGS_CHANGE", resource_type="SystemSetting",
                description=f"Admin updated {setting}.",
                actor_id=admin.id, actor_email=admin.email, actor_role=admin.role,
                ip_address="127.0.0.1",
            )
            count += 1

        self.stdout.write(f"  → {count} audit logs")

    # ------------------------------------------------------------------
    # Physical Assets  (25+ assets, 8 categories)
    # ------------------------------------------------------------------
    def _seed_assets(self, users):
        from apps.asset_management.domain.models import AssetCategory, Asset, MaintenanceLog

        if Asset.objects.exists():
            self.stdout.write("  ~ Assets exist, skipping.")
            return

        today = date.today()
        librarian = users.get("librarian@nova.local")

        # Categories
        furniture = AssetCategory.objects.create(name="Furniture", slug="furniture", icon="chair", description="Library furniture")
        electronics = AssetCategory.objects.create(name="Electronics", slug="electronics", icon="computer", description="Electronic equipment")
        hvac = AssetCategory.objects.create(name="HVAC", slug="hvac", icon="air", description="Heating, ventilation, AC")
        tables = AssetCategory.objects.create(name="Tables", slug="tables", icon="table", description="Reading and study tables", parent=furniture)
        shelving = AssetCategory.objects.create(name="Shelving", slug="shelving", icon="bookshelf", description="Book shelves", parent=furniture)
        chairs = AssetCategory.objects.create(name="Chairs", slug="chairs", icon="seat", description="Seating", parent=furniture)
        printers = AssetCategory.objects.create(name="Printers", slug="printers", icon="printer", description="Printing equipment", parent=electronics)
        computers = AssetCategory.objects.create(name="Computers", slug="computers", icon="desktop", description="Computers and terminals", parent=electronics)

        statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "UNDER_MAINTENANCE", "IN_STORAGE"]
        conditions = ["EXCELLENT", "GOOD", "GOOD", "FAIR", "POOR"]
        cat_choices = [tables, shelving, chairs, printers, computers, hvac, electronics, furniture]
        manufacturers = ["OakCraft", "SteelMax", "HP", "Dell", "Lenovo", "CoolAir", "ErgoSeating", "KioskPro"]

        asset_data = []
        for i in range(1, 26):
            cat = random.choice(cat_choices)
            asset_data.append({
                "asset_tag": f"AST-{i:03d}",
                "name": f"{cat.name} Unit #{i}",
                "category": cat,
                "status": random.choice(statuses),
                "condition": random.choice(conditions),
                "floor_number": random.randint(1, 3),
                "room": random.choice(["Main Reading Hall", "Study Area", "Entrance Lobby", "Print Station", "Computer Lab", "Mechanical Room", "Children Section", "Reference Desk"]),
                "purchase_date": today - timedelta(days=random.randint(90, 2000)),
                "purchase_price": Decimal(str(round(random.uniform(200, 10000), 2))),
                "supplier": random.choice(["LibFurniture Inc", "TechLib Solutions", "CoolAir Ltd", "ShelfMax", "HP Direct", "Dell Enterprise"]),
                "useful_life_years": random.randint(5, 20),
                "manufacturer": random.choice(manufacturers),
                "serial_number": f"SN-{uuid4().hex[:8].upper()}",
            })

        created = []
        for data in asset_data:
            created.append(Asset.objects.create(**data))

        # Maintenance logs
        for asset in created[:10]:
            for _ in range(random.randint(1, 3)):
                MaintenanceLog.objects.create(
                    asset=asset,
                    maintenance_type=random.choice(["PREVENTIVE", "CORRECTIVE", "INSPECTION"]),
                    description=f"Routine maintenance on {asset.name}",
                    performed_by=librarian,
                    performed_date=today - timedelta(days=random.randint(5, 180)),
                    cost=Decimal(str(round(random.uniform(50, 500), 2))),
                    vendor=random.choice(["TechLib Solutions", "HP Service", "General Maintenance Co"]),
                    condition_after=random.choice(["EXCELLENT", "GOOD"]),
                )

        self.stdout.write(f"  → {len(created)} assets, 8 categories")

    # ------------------------------------------------------------------
    # HR  (6 departments, 8 employees, 6 vacancies, 5 applications)
    # ------------------------------------------------------------------
    def _seed_hr(self, users):
        from apps.hr.domain.models import Department, Employee, JobVacancy, JobApplication

        if Department.objects.exists():
            self.stdout.write("  ~ HR exists, skipping.")
            return

        today = date.today()

        # Departments
        circ_dept = Department.objects.create(name="Circulation Services", code="CIRC", description="Book lending, returns, and reservations")
        ref_dept = Department.objects.create(name="Reference & Research", code="REF", description="Research queries and reference materials")
        it_dept = Department.objects.create(name="IT & Digital Services", code="IT", description="Technology infrastructure and digital library")
        admin_dept = Department.objects.create(name="Administration", code="ADMIN", description="Library management")
        child_dept = Department.objects.create(name="Children & Youth Services", code="CHILD", description="Programs for young readers")
        acq_dept = Department.objects.create(name="Acquisitions & Cataloging", code="ACQ", description="Book purchasing and cataloging")

        admin_user = users.get("admin@nova.local")
        librarian_user = users.get("librarian@nova.local")
        assistant_user = users.get("assistant@nova.local")

        # Extra staff users for employees
        from apps.identity.domain.models import User
        extra_staff = []
        for i, (fn, ln) in enumerate([
            ("Priya", "Dharmasena"), ("Roshan", "Weerakoon"),
            ("Nadeeka", "Gunawardena"), ("Tharindu", "Liyanage"), ("Chamari", "Fonseka"),
        ]):
            u, created = User.objects.get_or_create(
                email=f"staff{i+1}@nova.local",
                defaults={"first_name": fn, "last_name": ln, "role": "ASSISTANT", "is_staff": True, "is_verified": True, "is_active": True, "verification_status": "APPROVED"},
            )
            if created:
                u.set_password(DEFAULT_PASSWORD)
                u.save()
            extra_staff.append(u)

        admin_emp = Employee.objects.create(
            user=admin_user, employee_id="EMP-001", department=admin_dept,
            job_title="Library Director", hire_date=today - timedelta(days=2190),
            employment_type="FULL_TIME", status="ACTIVE", salary=85000, salary_currency="USD",
        )
        librarian_emp = Employee.objects.create(
            user=librarian_user, employee_id="EMP-002", department=circ_dept,
            job_title="Senior Librarian", hire_date=today - timedelta(days=1460),
            employment_type="FULL_TIME", status="ACTIVE", salary=62000, salary_currency="USD",
            reports_to=admin_emp,
        )
        assistant_emp = Employee.objects.create(
            user=assistant_user, employee_id="EMP-003", department=circ_dept,
            job_title="Library Assistant", hire_date=today - timedelta(days=365),
            employment_type="FULL_TIME", status="ACTIVE", salary=38000, salary_currency="USD",
            reports_to=librarian_emp,
        )

        depts = [ref_dept, it_dept, child_dept, acq_dept, circ_dept]
        titles = ["Reference Librarian", "Systems Administrator", "Youth Services Coordinator", "Cataloging Specialist", "Circulation Clerk"]
        for i, staff_user in enumerate(extra_staff):
            Employee.objects.create(
                user=staff_user, employee_id=f"EMP-{i+4:03d}",
                department=depts[i % len(depts)],
                job_title=titles[i % len(titles)],
                hire_date=today - timedelta(days=random.randint(90, 1000)),
                employment_type=random.choice(["FULL_TIME", "PART_TIME"]),
                status="ACTIVE", salary=random.randint(32000, 58000), salary_currency="USD",
                reports_to=librarian_emp,
            )

        admin_dept.head = admin_emp
        admin_dept.save()
        circ_dept.head = librarian_emp
        circ_dept.save()

        # Job Vacancies
        vacancy_data = [
            {"title": "Digital Services Librarian", "dept": it_dept, "desc": "Manage growing digital collections and online resources.", "exp": "MID", "etype": "FULL_TIME", "pos": 1, "min_sal": 52000, "max_sal": 65000, "status": "OPEN"},
            {"title": "Part-Time Reference Assistant", "dept": ref_dept, "desc": "Help patrons navigate research databases.", "exp": "ENTRY", "etype": "PART_TIME", "pos": 2, "min_sal": 18, "max_sal": 22, "status": "OPEN"},
            {"title": "Summer Intern - Children's Section", "dept": child_dept, "desc": "Help organize summer reading programs.", "exp": "ENTRY", "etype": "INTERN", "pos": 3, "min_sal": None, "max_sal": None, "status": "DRAFT"},
            {"title": "Senior Systems Engineer", "dept": it_dept, "desc": "Lead technology infrastructure modernization.", "exp": "SENIOR", "etype": "FULL_TIME", "pos": 1, "min_sal": 75000, "max_sal": 95000, "status": "OPEN"},
            {"title": "Cataloging Assistant", "dept": acq_dept, "desc": "Process new acquisitions and maintain catalog records.", "exp": "ENTRY", "etype": "FULL_TIME", "pos": 1, "min_sal": 35000, "max_sal": 42000, "status": "OPEN"},
            {"title": "Outreach Coordinator", "dept": child_dept, "desc": "Develop community engagement programs.", "exp": "MID", "etype": "FULL_TIME", "pos": 1, "min_sal": 45000, "max_sal": 55000, "status": "OPEN"},
        ]

        vacancies = []
        for vd in vacancy_data:
            v = JobVacancy.objects.create(
                title=vd["title"], department=vd["dept"], description=vd["desc"],
                requirements="See full job posting for details.",
                experience_level=vd["exp"], employment_type=vd["etype"],
                positions_available=vd["pos"], salary_range_min=vd["min_sal"],
                salary_range_max=vd["max_sal"], status=vd["status"],
                posted_by=admin_user,
                posted_date=today - timedelta(days=random.randint(3, 30)) if vd["status"] == "OPEN" else None,
                closing_date=today + timedelta(days=random.randint(14, 60)) if vd["status"] == "OPEN" else None,
                location="Nova Library - Main Campus",
            )
            vacancies.append(v)

        # Applications
        applicant_emails = ["alice@nova.local", "bob@nova.local", "frank@nova.local", "grace@nova.local", "henry@nova.local"]
        statuses = ["SUBMITTED", "UNDER_REVIEW", "SHORTLISTED", "INTERVIEW", "SUBMITTED"]
        for i, email in enumerate(applicant_emails):
            u = users.get(email)
            if u and i < len(vacancies):
                JobApplication.objects.create(
                    vacancy=vacancies[i % len(vacancies)], applicant=u,
                    applicant_name=f"{u.first_name} {u.last_name}",
                    applicant_email=u.email,
                    cover_letter=f"I am excited to apply for the {vacancies[i % len(vacancies)].title} position.",
                    status=statuses[i],
                    reviewed_by=admin_user if statuses[i] != "SUBMITTED" else None,
                )

        self.stdout.write(f"  → 6 departments, 8 employees, {len(vacancies)} vacancies, {len(applicant_emails)} applications")

    # ------------------------------------------------------------------
    # Members  (25 library patrons)
    # ------------------------------------------------------------------
    def _seed_members(self, users):
        from apps.identity.domain.models import Member

        if Member.objects.exists():
            self.stdout.write("  ~ Members exist, skipping.")
            return

        today = date.today()
        members_raw = [
            ("LIB-2025-0001", "Amara", "Perera", "amara.perera@example.com", "+94 71 234 5678", date(1990, 5, 14), "PUBLIC", "ACTIVE", 5),
            ("LIB-2025-0002", "Kavindu", "Silva", "kavindu.s@campus.lk", "+94 76 543 2100", date(2002, 3, 22), "STUDENT", "ACTIVE", 8),
            ("LIB-2025-0003", "Dr. Lakshmi", "Fernando", "l.fernando@uni.lk", "+94 77 888 9999", date(1975, 11, 8), "FACULTY", "ACTIVE", 15),
            ("LIB-2025-0004", "Dilshan", "Jayawardena", "dilshan.j@lib.org", "+94 75 321 0000", date(1988, 7, 30), "STAFF", "ACTIVE", 10),
            ("LIB-2025-0005", "Malini", "Wickramasinghe", "", "+94 71 000 1111", date(1955, 1, 12), "SENIOR", "ACTIVE", 5),
            ("LIB-2025-0006", "Ishara", "Bandara", "ishara.b@example.com", "+94 76 444 5555", date(2015, 9, 5), "CHILD", "ACTIVE", 3),
            ("LIB-2024-0050", "Tharushi", "Rathnayake", "tharushi@old.lk", "+94 77 111 0000", date(1995, 4, 18), "PUBLIC", "EXPIRED", 5),
            ("LIB-2024-0051", "Nuwan", "Dissanayake", "nuwan.d@example.com", "+94 75 222 3333", date(2000, 12, 1), "STUDENT", "SUSPENDED", 0),
            ("LIB-2025-0007", "Rashmi", "Cooray", "rashmi.c@mail.com", "+94 71 555 6666", date(1992, 8, 20), "PUBLIC", "ACTIVE", 5),
            ("LIB-2025-0008", "Asanka", "Kumara", "asanka.k@campus.lk", "+94 76 777 8888", date(2001, 1, 15), "STUDENT", "ACTIVE", 8),
            ("LIB-2025-0009", "Prof. Sunil", "Ratnayake", "s.ratnayake@uni.lk", "+94 77 999 0000", date(1968, 6, 25), "FACULTY", "ACTIVE", 15),
            ("LIB-2025-0010", "Chaminda", "Vaas", "chaminda.v@lib.org", "+94 75 111 2222", date(1985, 3, 10), "STAFF", "ACTIVE", 10),
            ("LIB-2025-0011", "Padma", "Gunasekara", "", "+94 71 333 4444", date(1948, 12, 5), "SENIOR", "ACTIVE", 5),
            ("LIB-2025-0012", "Sachini", "Perera", "sachini.p@school.lk", "+94 76 555 6666", date(2013, 4, 20), "CHILD", "ACTIVE", 3),
            ("LIB-2025-0013", "Nadeesha", "Wijesuriya", "nadeesha@mail.com", "+94 77 777 8888", date(1994, 9, 1), "PUBLIC", "ACTIVE", 5),
            ("LIB-2025-0014", "Ruwan", "Abeyratne", "ruwan.a@campus.lk", "+94 75 999 0000", date(2003, 2, 14), "STUDENT", "ACTIVE", 8),
            ("LIB-2025-0015", "Dr. Kumari", "Jayasekara", "k.jayasekara@uni.lk", "+94 71 222 3333", date(1972, 7, 8), "FACULTY", "ACTIVE", 15),
            ("LIB-2025-0016", "Gayan", "Wickremasinghe", "gayan.w@lib.org", "+94 76 444 5555", date(1990, 11, 22), "STAFF", "ACTIVE", 10),
            ("LIB-2025-0017", "Sita", "Ranasinghe", "", "+94 77 666 7777", date(1952, 3, 30), "SENIOR", "ACTIVE", 5),
            ("LIB-2025-0018", "Hirusha", "De Silva", "hirusha.d@school.lk", "+94 75 888 9999", date(2016, 1, 12), "CHILD", "ACTIVE", 3),
            ("LIB-2024-0052", "Lasith", "Malinga", "lasith.m@old.lk", "+94 71 000 1234", date(1983, 8, 28), "PUBLIC", "EXPIRED", 5),
            ("LIB-2024-0053", "Dinusha", "Perera", "dinusha.p@example.com", "+94 76 000 5678", date(1999, 5, 5), "STUDENT", "SUSPENDED", 0),
            ("LIB-2025-0019", "Amila", "Thilakarathne", "amila.t@mail.com", "+94 77 000 9012", date(1997, 10, 15), "PUBLIC", "ACTIVE", 5),
            ("LIB-2025-0020", "Sanduni", "Mendis", "sanduni.m@campus.lk", "+94 75 000 3456", date(2004, 6, 1), "STUDENT", "ACTIVE", 8),
            ("LIB-2025-0021", "Prof. Ranjith", "Seneviratne", "r.sene@uni.lk", "+94 71 000 7890", date(1965, 4, 12), "FACULTY", "ACTIVE", 15),
        ]

        count = 0
        for num, fn, ln, email, phone, dob, mtype, status, max_b in members_raw:
            expiry = today + timedelta(days=365) if status == "ACTIVE" else None
            Member.objects.create(
                membership_number=num, first_name=fn, last_name=ln,
                email=email, phone_number=phone, date_of_birth=dob,
                membership_type=mtype, status=status, max_borrows=max_b,
                expiry_date=expiry,
            )
            count += 1

        self.stdout.write(f"  → {count} library members")

    # ------------------------------------------------------------------
    # Notifications  (20+ per active user)
    # ------------------------------------------------------------------
    def _seed_notifications(self, users, books):
        from apps.intelligence.infrastructure.notification_engine import UserNotification

        if UserNotification.objects.exists():
            self.stdout.write("  ~ Notifications exist, skipping.")
            return

        ntypes = [
            ("RECOMMENDATION", "New book recommendation", "We think you'll love \"{book}\" based on your reading history.", "LOW"),
            ("ACHIEVEMENT", "Achievement unlocked!", "Congratulations! You've earned a new badge.", "MEDIUM"),
            ("STREAK_REMINDER", "Keep your streak alive!", "You're on a reading streak. Don't forget to read today!", "MEDIUM"),
            ("NEW_ARRIVAL", "New book arrival", "A new book in your favorite category has arrived: \"{book}\".", "LOW"),
            ("RESERVATION_READY", "Your reservation is ready!", "The book \"{book}\" is ready for pickup at the circulation desk.", "HIGH"),
            ("DUE_DATE_REMINDER", "Due date approaching", "Your borrowed book \"{book}\" is due in 2 days.", "HIGH"),
            ("OVERDUE_WARNING", "Overdue warning", "The book \"{book}\" is overdue. Please return it to avoid fines.", "URGENT"),
            ("KP_MILESTONE", "Level up!", "You've reached a new Knowledge Points milestone!", "MEDIUM"),
            ("RE_ENGAGEMENT", "We miss you!", "It's been a while since your last visit. Check out what's new!", "MEDIUM"),
        ]

        verified = [e for e in users if users[e].is_verified and users[e].role == "USER"]
        count = 0
        now = timezone.now()

        for email in verified:
            user = users[email]
            num_notifs = random.randint(15, 25)
            for i in range(num_notifs):
                ntype, title_tpl, body_tpl, priority = random.choice(ntypes)
                book = random.choice(books)
                title = title_tpl.format(book=book.title) if "{book}" in title_tpl else title_tpl
                body = body_tpl.format(book=book.title) if "{book}" in body_tpl else body_tpl
                is_read = random.random() > 0.4
                created_at = now - timedelta(hours=random.randint(1, 720))

                notif = UserNotification(
                    user=user, notification_type=ntype, channel="IN_APP",
                    priority=priority, title=title, body=body,
                    data={"book_id": str(book.id)} if "book" in ntype.lower() or random.random() > 0.5 else {},
                    is_read=is_read,
                    read_at=created_at + timedelta(minutes=random.randint(5, 120)) if is_read else None,
                    is_sent=True, sent_at=created_at,
                )
                notif.save()
                # Override auto-generated created_at
                UserNotification.objects.filter(id=notif.id).update(created_at=created_at)
                count += 1

        self.stdout.write(f"  → {count} notifications")

    # ------------------------------------------------------------------
    # Book Views (browse history — 20+ per user)
    # ------------------------------------------------------------------
    def _seed_book_views(self, users, books):
        from apps.intelligence.domain.models import BookView

        if BookView.objects.exists():
            self.stdout.write("  ~ Book views exist, skipping.")
            return

        verified = [e for e in users if users[e].is_verified]
        count = 0
        now = timezone.now()

        for email in verified:
            user = users[email]
            viewed_books = random.sample(books, min(random.randint(15, 25), len(books)))
            for book in viewed_books:
                BookView.objects.create(
                    user=user, book=book,
                    viewed_at=now - timedelta(hours=random.randint(1, 500)),
                    duration_seconds=random.randint(10, 300),
                    source=random.choice(["CATALOG", "SEARCH", "RECOMMENDATION", "TRENDING"]),
                )
                count += 1

        self.stdout.write(f"  → {count} book views")

    # ------------------------------------------------------------------
    # KP Ledger (20+ entries per active user)
    # ------------------------------------------------------------------
    def _seed_kp_ledger(self, users):
        from apps.governance.domain.models import KPLedger

        if KPLedger.objects.exists():
            self.stdout.write("  ~ KP ledger exists, skipping.")
            return

        verified = [e for e in users if users[e].is_verified and users[e].role == "USER"]
        count = 0
        actions = ["AWARD", "AWARD", "AWARD", "BONUS", "DEDUCT"]
        dimensions = ["explorer", "scholar", "connector", "achiever", "dedicated"]
        sources = ["BORROW", "RETURN", "REVIEW", "READING_SESSION", "ACHIEVEMENT", "STREAK_BONUS", "DAILY_LOGIN"]

        for email in verified:
            user = users[email]
            balance = 0
            num_entries = random.randint(18, 30)
            for _ in range(num_entries):
                action = random.choice(actions)
                pts = random.randint(5, 50) if action != "DEDUCT" else -random.randint(5, 20)
                balance = max(0, balance + pts)
                source = random.choice(sources)

                KPLedger.objects.create(
                    user_id=user.id, action=action, points=pts,
                    balance_after=balance,
                    source_type=source, source_id=str(uuid4()),
                    dimension=random.choice(dimensions),
                    description=f"KP {action.lower()} from {source.lower().replace('_', ' ')}.",
                )
                count += 1

        self.stdout.write(f"  → {count} KP ledger entries")

    # ------------------------------------------------------------------
    # Search Logs  (50+)
    # ------------------------------------------------------------------
    def _seed_search_logs(self, users):
        from apps.intelligence.domain.models import SearchLog

        if SearchLog.objects.exists():
            self.stdout.write("  ~ Search logs exist, skipping.")
            return

        queries = [
            "python programming", "design patterns", "machine learning", "algorithms",
            "clean code", "web development", "microservices", "database design",
            "data structures", "javascript", "system design", "operating systems",
            "artificial intelligence", "domain driven design", "refactoring",
            "software architecture", "networking", "java", "devops", "cloud computing",
            "react", "typescript", "docker", "kubernetes", "agile methodology",
        ]
        verified = [e for e in users if users[e].is_verified]
        count = 0
        now = timezone.now()

        for _ in range(60):
            email = random.choice(verified)
            user = users[email]
            q = random.choice(queries)
            SearchLog.objects.create(
                query_text=q, user=user,
                results_count=random.randint(0, 30),
                clicked_result_id=None,
                filters_applied={},
                ip_address=f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            )
            count += 1

        self.stdout.write(f"  → {count} search logs")

    # ------------------------------------------------------------------
    # Security Events  (25+)
    # ------------------------------------------------------------------
    def _seed_security_events(self, users):
        from apps.governance.domain.models import SecurityEvent

        if SecurityEvent.objects.exists():
            self.stdout.write("  ~ Security events exist, skipping.")
            return

        events = []
        now = timezone.now()

        event_types = [
            ("FAILED_LOGIN", "MEDIUM", "Failed login attempt"),
            ("BRUTE_FORCE", "HIGH", "Multiple failed login attempts detected"),
            ("RATE_LIMIT", "LOW", "Rate limit exceeded"),
            ("SUSPICIOUS_ACTIVITY", "MEDIUM", "Unusual access pattern detected"),
            ("FAILED_LOGIN", "MEDIUM", "Failed login attempt from unknown IP"),
        ]

        for i in range(25):
            etype, severity, desc = random.choice(event_types)
            email = random.choice(list(users.keys()))
            user = users[email]
            admin_user = users.get("admin@nova.local")
            is_resolved = random.random() > 0.4
            SecurityEvent.objects.create(
                event_type=etype, severity=severity,
                description=f"{desc} for {user.email}",
                user_id=user.id,
                ip_address=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                resolved=is_resolved,
                resolved_by=admin_user if is_resolved and admin_user else None,
            )

        self.stdout.write(f"  → 25 security events")

    # ------------------------------------------------------------------
    # Role Configs  (4 built-in + 2 custom)
    # ------------------------------------------------------------------
    def _seed_role_configs(self):
        from apps.identity.domain.models import RoleConfig

        if RoleConfig.objects.exists():
            self.stdout.write("  ~ Role configs exist, skipping.")
            return

        roles = [
            {"role_key": "SUPER_ADMIN", "display_name": "Super Administrator", "is_system": True,
             "permissions": {m: ["create", "read", "update", "delete"] for m in ["books", "authors", "digital_content", "users", "employees", "circulation", "assets", "analytics", "ai", "audit", "settings", "roles", "members"]}},
            {"role_key": "LIBRARIAN", "display_name": "Librarian", "is_system": True,
             "permissions": {"books": ["create", "read", "update", "delete"], "authors": ["create", "read", "update", "delete"], "digital_content": ["create", "read", "update", "delete"], "users": ["read"], "circulation": ["create", "read", "update", "delete"], "assets": ["read", "update"], "analytics": ["read"], "members": ["create", "read", "update"]}},
            {"role_key": "ASSISTANT", "display_name": "Library Assistant", "is_system": True,
             "permissions": {"books": ["read"], "authors": ["read"], "digital_content": ["read"], "circulation": ["read", "update"], "members": ["read"]}},
            {"role_key": "USER", "display_name": "Library Patron", "is_system": True,
             "permissions": {"books": ["read"], "authors": ["read"], "digital_content": ["read"], "circulation": ["read"]}},
            {"role_key": "SENIOR_LIBRARIAN", "display_name": "Senior Librarian", "is_system": False,
             "permissions": {"books": ["create", "read", "update", "delete"], "authors": ["create", "read", "update", "delete"], "digital_content": ["create", "read", "update", "delete"], "users": ["read", "update"], "circulation": ["create", "read", "update", "delete"], "assets": ["create", "read", "update"], "analytics": ["read"], "ai": ["read"], "audit": ["read"], "members": ["create", "read", "update", "delete"]}},
            {"role_key": "DATA_ANALYST", "display_name": "Data Analyst", "is_system": False,
             "permissions": {"analytics": ["read"], "ai": ["read", "update"], "audit": ["read"], "books": ["read"], "circulation": ["read"]}},
        ]

        for rd in roles:
            RoleConfig.objects.create(
                role_key=rd["role_key"], display_name=rd["display_name"],
                is_system=rd["is_system"], permissions=rd["permissions"],
                description=f"Permissions for {rd['display_name']}.",
            )

        self.stdout.write(f"  → {len(roles)} role configs")

    # ------------------------------------------------------------------
    # System Settings
    # ------------------------------------------------------------------
    def _seed_system_settings(self):
        from apps.common.domain.settings_model import SystemSetting
        count = SystemSetting.sync_defaults()
        self.stdout.write(f"  → {count} system settings synced")

    # ------------------------------------------------------------------
    # Print credentials
    # ------------------------------------------------------------------
    def _print_credentials(self, users):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Test Credentials ==="))
        self.stdout.write(f"  Password for ALL accounts: {DEFAULT_PASSWORD}\n")
        self.stdout.write(f"  {'Email':<35} {'Role':<15} {'Verified':<10} {'Active':<8}")
        self.stdout.write(f"  {'─' * 35} {'─' * 15} {'─' * 10} {'─' * 8}")
        for email, user in users.items():
            verified = "Yes" if user.is_verified else "No"
            active = "Yes" if user.is_active else "No"
            self.stdout.write(f"  {email:<35} {user.role:<15} {verified:<10} {active:<8}")
