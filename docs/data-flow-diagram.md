# Data Flow Diagram - Personal Reading Dashboard

## Application Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ONE-TIME SETUP                                  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  init_db         │
                    │  Create tables   │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  books.db       │
                    │  (SQLite)       │
                    └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION PIPELINE                              │
│              (orchestrate_csv_to_db.py)                                │
└─────────────────────────────────────────────────────────────────────────┘

    Goodreads CSV Export
            │
            ▼
    ┌───────────────────────┐
    │  csv_parser.py        │
    │  parse_goodreads_csv() │
    │                       │
    │  • Validates columns  │
    │  • Parses rows        │
    │  • Handles dates      │
    │  • Strips ISBNs       │
    └───────────────────────┘
            │
            │ Returns: list[CSVBook]
            ▼
    ┌───────────────────────┐
    │  update_books()       │
    │  delete_books()       │
    │                       │
    │  • Sync status        │
    │    changes from CSV   │
    │  • Remove books no    │
    │    longer in CSV      │
    └───────────────────────┘
            │
            ▼
    ┌───────────────────────┐
    │  deduplication.py     │
    │  deduplicate_books()  │
    │                       │
    │  • Queries DB for     │
    │    existing IDs       │
    │  • Filters out        │
    │    duplicates         │
    └───────────────────────┘
            │
            │ Returns: list[CSVBook] (new books only)
            ▼
    ┌───────────────────────────────────────────────────────────┐
    │  For each book:                                           │
    │                                                           │
    │  1. Clean title (strip parentheticals)                    │
    │  2. google_books.py → get_google_books_data()            │
    │     • Try ISBN-13 search                                  │
    │     • Fallback to ISBN-10 search                          │
    │     • Fallback to title/author search                     │
    │     • Retry logic (exponential backoff)                   │
    │     • Rate limit handling (0.5s delay between calls)      │
    │                                                           │
    │  3. book_transformer.py → transform_book()               │
    │     • Merge CSVBook + Google Books dict                   │
    │     • Priority: CSV title, CSV page_count                 │
    │     • Google Books for metadata                           │
    └───────────────────────────────────────────────────────────┘
            │
            │ Returns: list[BookCreate]
            ▼
    ┌───────────────────────┐
    │  ingest_books_to_db() │
    │  (batched: 100/book)   │
    │                       │
    │  • Convert Pydantic    │
    │    → SQLAlchemy       │
    │  • Commit to DB        │
    └───────────────────────┘
            │
            ▼
    ┌───────────────────────┐
    │  books.db             │
    │  (SQLite dev /        │
    │   PostgreSQL prod)    │
    └───────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                         API ENDPOINT                                    │
│                    (Alternative path)                                   │
└─────────────────────────────────────────────────────────────────────────┘

    HTTP POST /books/ingest
            │
            │ Request Body: list[BookCreate] (JSON)
            ▼
    ┌───────────────────────┐
    │  books_api.py         │
    │  ingest_books()       │
    │                       │
    │  • FastAPI validates  │
    │    JSON → BookCreate   │
    │  • Calls service       │
    └───────────────────────┘
            │
            ▼
    ┌───────────────────────┐
    │  ingest_books_to_db() │
    │  (same as above)       │
    └───────────────────────┘
```

## Data Structures

### CSVBook (Pydantic Schema)
**Source:** Goodreads CSV export  
**Fields:**
- `title: str` - Book title
- `author: str` - Primary author (singular)
- `isbn_10: str | None` - ISBN-10 identifier
- `isbn_13: str | None` - ISBN-13 identifier
- `num_pages: int | None` - Page count from CSV
- `goodreads_id: str` - Unique Goodreads identifier (required)
- `status: Literal["read", "currently-reading", "to-read"]` - Reading status
- `finish_date: date | None` - Date book was finished
- `additional_authors: str | None` - Additional authors (comma-separated string)

**Purpose:** Validates and structures raw CSV data before processing

---

### Google Books API Response (dict)
**Source:** Google Books API  
**Fields:**
- `google_books_id: str` - Unique Google Books identifier
- `google_books_link: str` - API self-link
- `title: str` - Book title (fallback to CSV if None)
- `authors: list[str]` - List of authors (fallback to CSV if None)
- `published_date: date | None` - Parsed publication date
- `year_published: int | None` - Extracted year
- `page_count: int | None` - Page count (often 0 or None)
- `categories: list[str] | None` - Book categories
- `genre: str | None` - Primary genre (first category)
- `description: str | None` - Book description
- `isbn_10: str | None` - ISBN-10 from Google Books
- `isbn_13: str | None` - ISBN-13 from Google Books
- `small_thumbnail: str | None` - Small image URL
- `thumbnail: str | None` - Full-size image URL

**Purpose:** Enriches CSV data with metadata

---

### BookCreate (Pydantic Schema)
**Source:** Merged CSVBook + Google Books data  
**Fields:** (Combines both sources with priority rules)
- `title: str` - **Priority: CSV** (more reliable)
- `authors: list[str]` - **Priority: Google Books** (handles multiple authors)
- `page_count: int | None` - **Priority: CSV** (more accurate)
- `status: str` - From CSV only
- `goodreads_id: str` - From CSV only
- `finish_date: date | None` - From CSV only
- All Google Books metadata fields (when available)

**Purpose:** Validates combined data before database insertion

---

### Book (SQLAlchemy Model)
**Source:** Database table  
**Fields:** (Matches BookCreate + auto-generated)
- All BookCreate fields
- `id: int` - Auto-incrementing primary key
- `created_at: datetime` - Auto-generated timestamp
- `updated_at: datetime` - Auto-generated timestamp

**Purpose:** Database representation of book records

## Ancillary Logic

### Rate Limiting & Retries
- **Delay between calls:** 0.5 seconds (prevents cascading rate limits)
- **Retry logic:** Exponential backoff (2s → 4s → 8s) for 429 errors
- **Max retries:** 3 attempts per search method
- **Search fallback chain:** ISBN-13 → ISBN-10 → title/author

### Deduplication
- **Method:** Single query to fetch existing `goodreads_id` values
- **Efficiency:** Uses set membership (O(1) lookup) for filtering
- **Result:** Only new books proceed to enrichment

### Data Priority Rules
1. **Title:** CSV (more reliable than Google Books)
2. **Page Count:** CSV (Google Books often returns 0 or None)
3. **Authors:** Google Books (handles multiple authors, CSV is singular)
4. **Metadata:** Google Books (categories, description, thumbnails, etc.)

### Error Handling
- **CSV parsing:** Invalid rows logged and skipped (ValidationError)
- **Google Books API:** Failures return None, pipeline continues
- **Database ingestion:** Unique constraint on `goodreads_id`; orchestration deduplicates before ingest so only new books are inserted
- **Transformation:** ValidationError raised if data doesn't match schema

### Batch Processing
- **Ingestion batches:** 100 books per batch
- **Rationale:** Better error recovery (if one batch fails, previous batches saved)
- **Database performance:** Optimizes commit frequency

## Key Design Decisions

1. **CSV as source of truth** for reading data (status, finish_date, page_count)
2. **Google Books for enrichment** (metadata, thumbnails, categories)
3. **Pydantic for validation** at API boundaries and CSV parsing
4. **Separation of concerns:** Each service has single responsibility
5. **Graceful degradation:** Missing Google Books data doesn't stop pipeline

