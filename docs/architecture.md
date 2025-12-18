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

**Create:**
- `POST /books/ingest` - Batch ingest books (accepts list of BookCreate objects)

**Read:**
- `GET /books` - List books with filtering (query params: status, genre, author, year_published)
- `GET /books/{book_id}` - Get single book by database ID
- `GET /reading-stats` - Aggregate reading statistics (totals, averages, genre breakdown)
- `GET /reading-trends` - Time-based reading analysis (grouped by year, month, genre)

**Update:**
- `PUT /books/{book_id}` - Update book status by ID (query param: new_status)
- `POST /books/batch-update` - Batch update from CSV data (for orchestration workflow)

**Delete:**
- `DELETE /books/{book_id}` - Delete single book by database ID
- `POST /books/delta-delete` - Delta delete from CSV data (for orchestration workflow)

#### Query Parameters
- `status` - Filter by reading status (read/currently-reading/to-read)
- `genre` - Filter by book genre (case-insensitive)
- `author` - Filter by author name (case-insensitive, partial match)
- `year_published` - Filter by publication year

#### Request/Response Schemas
- All endpoints use Pydantic schemas for validation
- Request bodies automatically validated before function execution
- Response schemas ensure consistent output format
- Automatic OpenAPI/Swagger documentation generation

### Data Validation & Schemas

**Decision:** Use Pydantic models for data validation and type conversion.

**Schema Structure:**
- `GoodreadsCSVRow` - Validates raw CSV data from Goodreads export
  - Handles column validation, type conversion, whitespace stripping
  - Replaces manual validation logic in CSV parser
- `BookCreate` - Validates combined data (CSV + Google Books) for ingestion endpoint
  - Ensures all required fields are present
  - Automatically converts date strings to date objects
  - Validates data types before database insertion

**Benefits:**
- Automatic validation and type conversion
- Clear error messages for invalid data
- Reduces manual validation code in services
- Better IDE support and type safety
- Automatic API documentation generation

**Rationale:**
- Pydantic is core to FastAPI ecosystem
- Eliminates repetitive validation code (strip(), type checks, etc.)
- Provides consistent validation across CSV parsing and API endpoints
- Makes codebase more maintainable and less error-prone

### Technology Stack

#### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Production database
- **SQLite** - Development database
- **unittest** - Testing framework (Python standard library)

#### Frontend
- **Vanilla JavaScript** - No framework complexity
- **Chart.js** - Data visualization
- **HTML/CSS** - Simple dashboard

#### Infrastructure
- **AWS EC2** - Application hosting (can combine FastAPI + Airflow on single instance)
- **AWS RDS** - Database hosting (PostgreSQL)
- **AWS S3** - CSV file storage
- **Airflow** - Data pipeline scheduling

#### AWS Cost Estimates (Personal Use, Low Traffic)
**Option 1: Combined Instance (Recommended)**
- EC2 t3.small (FastAPI + Airflow): ~$15/month
- RDS db.t3.micro: ~$15/month
- S3 (storage + requests): ~$0.50-1/month
- **Total: ~$30-31/month**

**Option 2: Separate Instances**
- EC2 t3.micro (FastAPI): ~$7-8/month
- EC2 t3.micro (Airflow): ~$7-8/month
- RDS db.t3.micro: ~$15/month
- S3: ~$0.50-1/month
- **Total: ~$30-32/month**

**AWS Free Tier (First 12 Months):**
- EC2 t2.micro: 750 hours/month free
- RDS db.t2.micro: Free tier eligible
- S3: 5GB free
- **After free tier: ~$30-35/month**

**Note:** Costs are for personal use with minimal traffic. Can be reduced further with spot instances or reserved instances, but adds complexity.

### Data Flow

1. **Data Ingestion & Sync**
   - User exports Goodreads library to CSV (manual upload cadence)
   - Pipeline parses CSV, filters out books already stored locally
   - Update service syncs status changes from CSV exports
   - Delete service removes books no longer in CSV
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

#### Phase 2: Analytics Endpoints (Features-First Approach)
- Implement reading statistics, trends, and genre breakdown APIs
- Add aggregation queries leveraging local database
- Build complete feature set locally before cloud migration
- **Rationale:** Analytics endpoints are database queries that don't depend on cloud infrastructure. Building features first allows full local testing and validation before investing in cloud setup.

#### Phase 3: Cloud Migration & Production Pipeline
- Move CSV uploads to S3 and add Airflow DAG to orchestrate ingestion
- Deploy to AWS (EC2 + RDS)
- Introduce retries, monitoring, and alerting for the pipeline
- Configure logging, monitoring, and performance tuning
- **Rationale:** Migrate complete feature set to cloud once all features are working locally. Cloud migration is primarily orchestration/file handling changes, not endpoint changes.

#### Phase 4: Frontend Dashboard
- Create dashboard interface with filtering and visualizations
- Integrate Chart.js components with backend endpoints

### Key Learning Goals
- FastAPI patterns and best practices
- Database design and ORM usage
- External API integration
- Data pipeline development
- Full-stack application development
- AWS deployment and operations

## Next Steps
1. ~~Initialize database schema~~ ✅ Complete
2. ~~Implement deduplication service~~ ✅ Complete
3. ~~Add FastAPI database dependency and ingestion endpoint~~ ✅ Complete
4. ~~Build orchestration script~~ ✅ Complete
5. ~~Add CRUD API endpoints~~ ✅ Complete
6. **Phase 3:** Cloud Migration (S3 + Airflow + AWS deployment)
7. **Phase 4:** Frontend Dashboard
