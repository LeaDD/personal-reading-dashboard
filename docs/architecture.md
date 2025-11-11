# Personal Reading Analytics Dashboard - Architecture

## Project Overview
A FastAPI-based personal reading analytics system that ingests Goodreads CSV exports, enriches them with Google Books metadata, and serves insights via REST endpoints with a simple frontend dashboard.

## Architecture Decisions

### Data Strategy
**Decision:** Ingest Goodreads CSV exports, enrich each title with Google Books metadata, and store the combined result locally.
**Rationale:** 
- Goodreads API is deprecated; CSV export is the reliable source of reading activity
- Google Books provides rich metadata (pages, categories, ISBNs, thumbnails) unavailable in the CSV
- Local storage enables low-latency analytics queries and historical trend analysis
- Architecture mirrors production workflow (S3 + Airflow later) while keeping Phase 1 local for simplicity

### Database Design

#### Books Table
```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    google_books_id VARCHAR(40) UNIQUE,
    google_books_link VARCHAR(500),
    title VARCHAR(255) NOT NULL,
    authors JSONB NOT NULL,
    published_date DATE,
    year_published INTEGER,
    page_count INTEGER,
    categories JSONB,
    genre VARCHAR(100),
    description TEXT,
    isbn_10 VARCHAR(10),
    isbn_13 VARCHAR(13),
    small_thumbnail VARCHAR(500),
    thumbnail VARCHAR(500),
    status VARCHAR(20) NOT NULL,
    goodreads_id VARCHAR(50) UNIQUE NOT NULL,
    finish_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Design Decisions:**
- Use auto-incrementing `id` as primary key for flexibility
- Persist both Goodreads and Google Books identifiers for deduplication and API traceability
- Store authors and categories as JSON to remain portable across SQLite and PostgreSQL
- Capture optional metadata (genre, description, ISBN, thumbnails) when Google Books returns it
- Track reading status and finish date from Goodreads CSV export

### API Design

#### Core Endpoints
```
GET /books
- Query params: status, year, genre, author, year_published
- Returns: List of books with basic info

GET /books/{book_id}
- Returns: Detailed book information

GET /reading-stats
- Returns: Personal reading statistics (books read, pages, etc.)

GET /reading-trends
- Query params: year, month
- Returns: Reading patterns over time
```

#### Query Parameters
- `status` - Filter by reading status (read/reading/want-to-read)
- `year` - Filter by year read
- `genre` - Filter by book genre
- `author` - Filter by author name
- `year_published` - Filter by publication year

### Technology Stack

#### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Production database
- **SQLite** - Development database
- **pytest** - Testing framework

#### Frontend
- **Vanilla JavaScript** - No framework complexity
- **Chart.js** - Data visualization
- **HTML/CSS** - Simple dashboard

#### Infrastructure
- **AWS EC2** - Application hosting
- **AWS RDS** - Database hosting
- **Airflow** - Data pipeline scheduling

### Data Flow

1. **Data Ingestion**
   - User exports Goodreads library to CSV (manual upload cadence)
   - Pipeline parses CSV, filters out books already stored locally
   - For new titles, Google Books API is queried for enriched metadata
   - Combined record (CSV + Google Books) is written to the database

2. **API Layer**
   - FastAPI serves data from local database
   - Endpoints provide filtered and aggregated data
   - Real-time responses (no external API calls)

3. **Frontend**
   - JavaScript fetches data from FastAPI endpoints
   - Charts and visualizations display the data
   - Interactive filtering and exploration

### Development Approach

#### Phase 1: Foundation & Local Pipeline
- Set up FastAPI application and project structure
- Implement Google Books service, CSV parser, logging, and database initialization (Phase 1A)
- Wire components together: deduplication, DB dependency, ingestion endpoint (Phase 1B)
- Build orchestration script to process CSV end-to-end (Phase 1C)

#### Phase 2: Production Pipeline Enhancements
- Move CSV uploads to S3 and add Airflow DAG to orchestrate ingestion
- Introduce retries, monitoring, and alerting for the pipeline

#### Phase 3: Analytics Endpoints
- Implement reading statistics, trends, and genre breakdown APIs
- Add aggregation queries leveraging local database

#### Phase 4: Frontend Dashboard
- Create dashboard interface with filtering and visualizations
- Integrate Chart.js components with backend endpoints

#### Phase 5: Deployment & Operations
- Deploy to AWS (EC2 + RDS)
- Configure logging, monitoring, and performance tuning

### Key Learning Goals
- FastAPI patterns and best practices
- Database design and ORM usage
- External API integration
- Data pipeline development
- Full-stack application development
- AWS deployment and operations

## Next Steps
1. Initialize database schema (`Base.metadata.create_all`) and verify tables
2. Implement deduplication service to filter existing books before enrichment
3. Add FastAPI database dependency and ingestion endpoint
4. Build orchestration script to run CSV → Google Books → DB pipeline locally
5. Add tests and documentation for the ingestion workflow
