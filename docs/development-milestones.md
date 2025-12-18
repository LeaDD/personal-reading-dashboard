# Development Milestones & Decision Log

This document tracks the development process, the order in which features were implemented, and the reasoning behind each decision. Use this as a reference for understanding the development workflow and decision-making process.

## Milestone 1: Project Foundation & Planning ✅

**What we did:**
- Project concept finalized (FastAPI + Goodreads API + Dashboard)
- Architecture documented (data strategy, database schema, API design)
- Technology stack decided
- Project structure planned

**Why this order:**
- **Planning before coding:** Prevents rework. Architecture decisions (like storing Goodreads data locally vs API calls) impact everything downstream.
- **Documentation first:** Creates shared understanding. When you return weeks later, you know why decisions were made.
- **Structure before implementation:** Directory layout guides where code belongs and prevents refactoring later.

**Key decision:** Store Goodreads data locally instead of making API calls each request
- Reason: Performance, reliability, enables complex analytics queries
- Impact: Need database layer before API endpoints can work

## Milestone 2: Basic FastAPI Application ✅

**What we did:**
- Created project directory structure (`backend/app/`, `models/`, `schemas/`, `api/`, `services/`)
- Created `requirements.txt` with core dependencies
- Built minimal FastAPI app with health check endpoints
- Tested that uvicorn server runs successfully

**Why this order:**
- **Directory structure first:** Foundation before code. Know where files belong. Prevents scattered code that needs refactoring.
- **Requirements before code:** Documents dependencies. Makes environment reproducible (`pip install -r requirements.txt`).
- **Minimal app before features:** Validate the setup works. FastAPI installation, uvicorn startup, imports - catch issues early.
- **Health check endpoints:** Quick win to confirm everything works before adding complexity.

**Key decisions:**
- **Loose version constraints (`>=`):** Allows security patches while protecting against major breaking changes. Exact versions (`==`) for production lock files later.
- **Module path syntax:** `backend.app.main:app` (dots, not slashes) - Python imports use dot notation.
- **Separation of concerns:** Models, schemas, API routes in separate directories from the start (prevents spaghetti code later).

**Lessons learned:**
- Uvicorn module path must use dots: `backend.app.main:app` not `backend/app/main:app`
- SQLite needs `check_same_thread: False` when used with FastAPI (multi-threading concern)

## Milestone 3: Database Setup (Partially Complete)

**What we completed:**
- ✅ Created `database.py` for SQLAlchemy connection management
  - Environment variable support for database URL with SQLite default
  - Conditional SQLite parameters (`check_same_thread=False` only for SQLite)
  - Engine, SessionLocal factory, Base class configured
- ✅ Created Book model (`models/book_model.py` - renamed Nov 15, 2025)
  - Used modern SQLAlchemy 2.0 syntax (`Mapped`, `mapped_column`)
  - **Final Architecture:** Goodreads CSV + Google Books API
  - Fields: google_books_id, google_books_link, title, authors (JSON), ISBNs, thumbnails, categories (JSON), goodreads_id, status, dates
  - Proper nullable constraints, string lengths, DateTime fields
  - JSON type for lists (SQLite/PostgreSQL compatibility)

**Key decisions made:**
- **Keep author as string field** (not separate Authors table)
  - Rationale: No author-specific endpoints planned, simple filtering is sufficient
  - YAGNI principle: Can add relationship later if needed
- **Conditional database parameters** using `**kwargs` unpacking pattern
  - SQLite-specific settings only applied when needed
  - Makes code portable between SQLite (dev) and PostgreSQL (prod)
- **Finalized on Goodreads CSV + Google Books API**
  - Open Library rejected (inconsistent data, missing genre)
  - Google Books API tested and working well
  - Clear separation: CSV for reading data, Google Books for book metadata

**Why this order:**
- **Database connection before models:** Models need to inherit from `Base` (from database.py). Dependency order matters.
- **Models before endpoints:** Endpoints need models to query. Can't build `/books` endpoint without a Book model.
- **Goodreads API validation before finalizing:** Validate model matches actual API response structure

**What's left:**
- ⏳ CSV Parser service to extract Goodreads data
- ⏳ Initialize database and create tables
- ⏳ Test database connectivity
- ⏳ Wire database into FastAPI (dependency injection)

**Additional work completed (Nov 2, 2025):**
- ✅ Google Books service with proper logging, error handling, type hints
- ✅ Book model finalized with JSON fields for SQLite/PostgreSQL compatibility
- ✅ Implemented JSON over ARRAY decision for portable database support

**Next steps (in order - Phase 1A, B, C):**

**Phase 1A: Build Independent Components**
1. ✅ Google Books API client (`services/google_books.py`) - Complete with logging, error handling
2. ✅ CSV Parser (`services/csv_parser.py`) - **COMPLETE**
   - ✅ Core parsing logic implemented
   - ✅ Column validation
   - ✅ Row-level validation (skips invalid rows)
   - ✅ Date parsing (string to date object with error handling)
   - ✅ Empty date handling (None instead of empty string)
   - ✅ Logging and error handling
   - ✅ Test setup with logging configuration
   - ✅ Refactored to use Pydantic `CSVBook` schema (Nov 18, 2025)
     - Returns `list[CSVBook]` instead of `list[dict]`
     - Manual date parsing still required (Pydantic doesn't parse "YYYY/MM/DD" format)
     - ValidationError handling for invalid rows
3. ✅ Logging Configuration (`config/logging_config.py`) - **COMPLETE**
   - ✅ Environment-based configuration (DEBUG dev, INFO prod)
   - ✅ Console logging in development
   - ✅ Console + file logging in production
   - ✅ Log file: `logs/app.log`
   - ✅ Integrated into main.py
   - ✅ All modules use proper logger pattern
4. ✅ Create Database Tables (`init_db.py`) - **COMPLETE**
   - ✅ `init_db()` script creates schema via `Base.metadata.create_all`
   - ✅ SQLite `check_same_thread` handled via `connect_args`
   - ✅ `books.db` generated and schema verified

**Phase 1B: Wire Components Together**
1. ✅ Deduplication Service (`services/deduplication.py`) - **COMPLETE**
   - ✅ Single query (`IN (...)`) to fetch existing Goodreads IDs
   - ✅ Filters incoming list using set membership
   - ✅ Read-only for now; returns books missing from DB
   - ✅ Updated to work with `CSVBook` objects (Nov 18, 2025)
     - Changed from `list[dict]` to `list[CSVBook]`
     - Uses attribute access instead of dict access
2. ✅ FastAPI Database Dependency - Wire DB session into FastAPI
   - ✅ `get_db()` generator function for dependency injection
3. ✅ FastAPI Ingestion Endpoint (`api/books_api.py` - renamed Nov 15, 2025) - POST endpoint to receive and write data
   - ✅ Basic implementation with `list[dict[str, Any]]` request body (initial)
   - ✅ Refactored to use Pydantic `BookCreate` schema (Nov 16, 2025)
   - ✅ Automatic validation and type conversion (dates, etc.)
   - ✅ Removed manual date parsing (Pydantic handles it)
   - ✅ Tested successfully via Swagger/FastAPI docs
   - ✅ Router wired into main.py
   - ✅ Comprehensive docstring and inline comments added
   - ✅ CSV parser refactored to use `CSVBook` schema (Nov 18, 2025)

**Additional work completed (Nov 15, 2025):**
- ✅ File naming convention standardized: `{domain}_{type}.py` pattern
  - `models/book_model.py`, `api/books_api.py`, `schemas/books_schema.py`
  - Rationale: Eliminates confusion between model, API, and schema files
- ✅ Package structure completed: Added `__init__.py` to `schemas/` and `services/`
- ✅ Logging configuration: File handler creation made conditional on environment

**Additional work completed (Nov 16, 2025):**
- ✅ Pydantic schemas implemented (`schemas/books_schema.py`)
  - `BookCreate` - Validates combined data for ingestion endpoint
  - `CSVBook` - Validates CSV data (ready for future CSV parser refactor)
  - Automatic date string → date object conversion
  - Schema fields match Book model nullability exactly
- ✅ Ingestion endpoint refactored to use Pydantic
  - Request body changed from `list[dict[str, Any]]` to `list[BookCreate]`
  - Removed manual date parsing (Pydantic handles automatically)
  - Simplified conversion using `Book(**book_create.model_dump())`
- ✅ Database model updated: `goodreads_id` set to `nullable=False` (required for deduplication)
- ✅ Database recreated with updated schema

**Additional work completed (Nov 18, 2025):**
- ✅ CSV Parser refactored to use Pydantic `CSVBook` schema
  - Returns `list[CSVBook]` instead of `list[dict]`
  - Manual date parsing for "YYYY/MM/DD" format (Pydantic doesn't parse this automatically)
  - ValidationError handling to skip invalid rows gracefully
  - Maps CSV column names to schema field names
- ✅ Deduplication service updated to work with `CSVBook` objects
  - Changed from `list[dict]` to `list[CSVBook]`
  - Uses attribute access (`book.goodreads_id`) instead of dict access
- ✅ `CSVBook` schema enhanced with `Literal` type for status validation
- **Key Learning:** Pydantic most valuable at API boundaries (endpoints) for automatic documentation. For internal services, simpler approaches may be sufficient, but learning value can justify using it.

**Phase 1C: Orchestration**
1. ✅ Update CSVBook schema to include `additional_authors` field (completed earlier)
2. ✅ Update CSV parser to read "Additional Authors" column (completed earlier)
3. ✅ Create `book_transformer.py` service to merge CSVBook + Google Books data → BookCreate (Nov 20, 2025)
   - Handles None google_books_data gracefully (creates BookCreate from CSV only)
   - Proper error handling (ValidationError and Exception)
   - Uses CSV data for: status, goodreads_id, finish_date
   - Uses Google Books data for metadata (title, authors, pages, etc.)
   - Author priority: Google Books authors (if available) → CSV author (fallback)
4. ✅ Implement date parsing in `google_books.py` (Nov 22, 2025)
   - Parse publishedDate string → date object
   - Handle formats: "2006" (year only), "2006-01" (year-month), "2006-01-15" (full date)
   - Extract year_published from parsed date
   - Handle None case and unexpected formats
   - Updated docstring to reflect date | None return type
5. ✅ Main Processing Script - Orchestrate full pipeline (Nov 27, 2025)
   - Created `orchestrate_csv_to_db.py` script
   - Full pipeline: CSV → parse → dedupe → enrich → transform → ingest
   - Batch processing (100 books per batch)
   - Error handling for individual book failures
   - Comprehensive logging at each stage
6. ✅ Test End-to-End - Process your Goodreads CSV (Nov 27, 2025)
   - Successfully processed all 200 books
   - 100% Google Books match rate
   - Rate limiting handled with retry logic
   - All books ingested successfully

**Additional work completed (Nov 20, 2025):**
- ✅ book_transformer.py service complete
- ✅ google_books.py bug fixes: Fixed `book.title` reference (didn't exist), added fallbacks for title/authors
- ✅ google_books.py now guarantees title and authors will always have values
- ✅ book_transformer.py simplified (removed if conditions since google_books.py guarantees those fields)
- **Key Decision:** Date parsing will be done in google_books.py (separation of concerns - parsing at API boundary)
- **Key Learning:** When a service guarantees certain fields, dependent services can rely on those guarantees and simplify code

**Additional work completed (Nov 22, 2025):**
- ✅ Date parsing implemented in google_books.py
  - Handles three date formats: year-only (4 chars), year-month (7 chars), full date (10 chars)
  - Returns `date` objects instead of strings
  - Extracts `year_published` from parsed date
  - Handles None case and unexpected formats (defensive programming)
  - Updated docstring to reflect actual return types
- **Key Learning:** Defensive programming matters - else clauses for unexpected formats prevent runtime errors

**Additional work completed (Nov 27, 2025):**
- ✅ Google Books API improvements
  - ISBN-based search with fallback chain (ISBN-13 → ISBN-10 → title/author)
  - Retry logic with exponential backoff for rate limit errors (429 status)
  - 0.5s delay between API calls to prevent cascading rate limits
  - Enhanced logging to track search method success
  - Result: 100% match rate on 200 books
- ✅ Data priority refinements
  - CSV title now primary (more reliable than Google Books)
  - CSV page_count now primary (Google Books often returns 0 or None)
  - Updated `book_transformer.py` accordingly
- ✅ Orchestration pipeline complete
  - End-to-end pipeline tested and working
  - Batch processing (100 books per batch)
  - Individual book failure handling (logs but continues)
  - Comprehensive logging at each stage
- ✅ Documentation updates
  - Updated README to reflect CSV exports (not API)
  - Created comprehensive data flow diagram
  - Updated architecture and milestones
- ✅ Testing framework decision: Use `unittest` instead of `pytest` (consistency with work)
- ✅ Update Books Service (`services/update_books.py`) - Dec 9, 2025
  - Syncs book status changes from CSV exports to database
  - Batch query optimization (single query instead of N queries)
  - Takes session parameter for transaction control
  - Proper error handling with SQLAlchemyError and Exception
  - Removed HTTPException from services (proper separation of concerns)
  - Self-contained: detects and updates in one function
- ✅ Delete Books Service (`services/delete_books.py`) - Dec 14, 2025
  - Deletes books present in DB but not in incoming CSV (delta delete)
  - Batch query optimization (single query with `not_in()` filter)
  - Proper error handling and logging
  - Returns count of deleted books
- ✅ Orchestration Script Refactored (`scripts/orchestrate_csv_to_db.py`) - Dec 14, 2025
  - Integrated update and delete services
  - Moved DB session context to top level (single transaction)
  - Order: Parse → Update → Delete → Deduplicate → Enrich → Ingest
  - Added logging setup in `__main__` block
  - End-to-end testing successful
- ✅ Google Books Service Bug Fix - Dec 14, 2025
  - Fixed `process_api_response()` to accept `title` and `author` parameters
  - Prevents `NameError` when Google Books doesn't return author data
- **Phase 1 Status: ✅ COMPLETE** (All services complete, orchestration integrated)

**Phase 2: Analytics Endpoints (Features-First Approach)** ✅ **COMPLETE**

**Phase 2.5: CRUD API Endpoints** ✅ **COMPLETE** - Dec 17, 2025
- ✅ Full CRUD operation coverage
  - Create: `POST /books/ingest` (batch ingest)
  - Read: `GET /books`, `GET /books/{book_id}`, `GET /reading-stats`, `GET /reading-trends`
  - Update: `PUT /books/{book_id}` (single update), `POST /books/batch-update` (orchestration)
  - Delete: `DELETE /books/{book_id}` (single delete), `POST /books/delta-delete` (orchestration)
- ✅ Standard REST endpoints for general API use
- ✅ Workflow-specific endpoints for orchestration pipeline
- ✅ Comprehensive docstrings on all endpoints
- ✅ Production-ready exception handling
  - Preserves HTTPExceptions (404, etc.) unchanged
  - Logs full details server-side
  - Returns generic messages to clients
- ✅ Type validation with `Literal` types
  - Automatic validation for status values
  - Auto-documented in Swagger
  - No manual validation code needed
- **Rationale:** Provide both standard REST patterns and workflow-specific endpoints. Different use cases, both valid.
- ✅ GET /books endpoint with filtering (Nov 28, 2025)
  - Query parameters: status, genre, author, year_published
  - Conditional filter chaining pattern
  - Database-agnostic JSON array handling (PostgreSQL vs SQLite)
  - Case-insensitive matching for genre and author
  - Partial string matching for author search
- ✅ GET /books endpoint improvements (Dec 1, 2025)
  - ✅ BookResponse Pydantic schema with `from_attributes=True`
  - ✅ Comprehensive logging with module-level logger
  - ✅ Exception handling with reusable handler function
  - ✅ Proper error messages and HTTP status codes
- ✅ GET /books/{book_id} endpoint (Dec 1, 2025)
  - Returns single book by ID
  - 404 handling for not found
  - Consistent exception handling
- ✅ GET /reading-trends endpoint (Dec 3, 2025)
  - Database-specific date extraction (strftime for SQLite, extract for PostgreSQL)
  - Groups by year_read, month_read, and genre
  - Returns time-based reading analysis
  - Fixed recursion error (expression objects vs row values)
- ✅ GET /reading-stats endpoint (Dec 4, 2025)
  - Complete return structure (dict with totals + genre breakdown list)
  - Pydantic response schemas created (StatsResponse, GenreCount)
  - Genre breakdown integrated into stats endpoint (no separate endpoint needed)
  - Comprehensive None handling for aggregate results
  - Proper logging and error handling
- **Rationale:** Build complete feature set locally before cloud migration. Analytics endpoints are database queries that don't depend on cloud infrastructure.
- **Goal:** Power personal website dashboard with reading insights
- **Approach:** User writing 75-80% of code, AI assists with 20-25% (complex SQLAlchemy patterns, database-specific logic)

**Phase 3: Cloud Migration & Production Pipeline (Future)**
- ⏳ S3 bucket setup
- ⏳ Airflow DAG with S3 sensor
- ⏳ Replace local file handling with S3 operations
- ⏳ Deploy to AWS (EC2 + RDS)
- ⏳ Configure logging, monitoring, and performance tuning
- **AWS Cost Estimate:** ~$30-35/month for personal use (see architecture.md for details)

**Key learning:**
- Validate external APIs before building (Open Library had too many issues)
- Pivot when external dependencies don't work (Goodreads deprecated, Open Library inconsistent)
- Test components independently before wiring together (reduces debugging complexity)
- Logical construction order: Independent → Database → API → Orchestration

## Development Patterns & Principles

### 1. Foundation → Functionality
Always build the foundation (structure, database, basic setup) before adding features. You can't build endpoints without a database.

### 2. Test Early, Test Small
Validate each component works (FastAPI runs, database connects) before moving to the next layer. Catches issues when they're easy to fix.

### 3. Document Decisions
Record WHY you made choices (loose vs tight versioning, SQLite vs PostgreSQL for dev). Future you (or teammates) will thank you.

### 4. Separation of Concerns
Models (database), Schemas (API validation), API routes (HTTP), Services (business logic) - each in their own directory. Makes code maintainable.

### 5. Incremental Complexity
Start simple (SQLite), then upgrade (PostgreSQL). Start with basic endpoints, then add filtering. Build in layers.

## Decision Rationale Reference

| Decision | Options Considered | Choice Made | Rationale |
|----------|-------------------|-------------|-----------|
| Version constraints | Exact (`==`), Loose (`>=`), None | Loose (`>=`) | Allows security patches, protects against major breaks, easier maintenance |
| Database for dev | PostgreSQL, SQLite | SQLite | No server setup needed, file-based, easy to reset |
| Testing library | httpx, requests | requests (user preference) | User familiarity, async can come later |
| Module path syntax | Dots, slashes | Dots (`backend.app.main`) | Python import syntax requirement |
| Directory structure | Flat, nested | Nested by concern | Separation of concerns, scalable structure |

## Upcoming Milestones (Planned)

### Milestone 4: First API Endpoint
- Wire database session into FastAPI
- Create `GET /books` endpoint with basic querying
- Test with sample data

### Milestone 5: Filtering & Query Parameters
- Add query parameters (status, genre, author, year)
- Implement filtering logic
- Test various filter combinations

### Milestone 6: Data Ingestion
- Integrate with Goodreads API
- Build data sync mechanism
- Handle API rate limits and errors

### Milestone 7: Analytics Endpoints
- `GET /reading-stats` - aggregate statistics
- `GET /reading-trends` - time-based analysis
- `GET /genre-breakdown` - genre distribution

### Milestone 8: Frontend Dashboard
- HTML/CSS dashboard structure
- JavaScript API integration
- Chart.js visualizations

### Milestone 9: Production Deployment
- AWS EC2 setup
- PostgreSQL on RDS
- Domain and SSL configuration

