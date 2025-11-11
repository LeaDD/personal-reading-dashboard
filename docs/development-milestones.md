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
- ✅ Created Book model (`models/book.py`)
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
3. ✅ Logging Configuration (`config/logging_config.py`) - **COMPLETE**
   - ✅ Environment-based configuration (DEBUG dev, INFO prod)
   - ✅ Console logging in development
   - ✅ Console + file logging in production
   - ✅ Log file: `logs/app.log`
   - ✅ Integrated into main.py
   - ✅ All modules use proper logger pattern
4. ⏳ Create Database Tables - Simple script to initialize schema

**Phase 1B: Wire Components Together**
1. ⏳ Deduplication Service - Filter out books already in DB
2. ⏳ FastAPI Database Dependency - Wire DB session into FastAPI
3. ⏳ FastAPI Ingestion Endpoint - POST endpoint to receive and write data

**Phase 1C: Orchestration**
1. ⏳ Main Processing Script - Orchestrate full pipeline
2. ⏳ Test End-to-End - Process your Goodreads CSV

**Phase 2: AWS/Airflow Integration (Future)**
- S3 bucket setup
- Airflow DAG with S3 sensor
- Replace local file handling with S3 operations

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

