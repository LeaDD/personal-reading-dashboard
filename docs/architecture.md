# Personal Reading Analytics Dashboard - Architecture

## Project Overview
A FastAPI-based personal reading analytics system that pulls data from Goodreads API, processes it for personal insights, and serves it via REST endpoints with a simple frontend dashboard.

## Architecture Decisions

### Data Strategy
**Decision:** Store Goodreads data locally in our database
**Rationale:** 
- Eliminates API roundtrips for better performance
- Provides reliability (local data availability)
- Enables complex analytics queries
- Allows integration with Airflow for scheduled data pulls

### Database Design

#### Books Table
```sql
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    goodreads_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    genre VARCHAR(100),
    pages INTEGER,
    year_published INTEGER,
    status VARCHAR(20) DEFAULT 'want-to-read', -- want-to-read, reading, read
    start_date DATE,
    finish_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Key Design Decisions:**
- Use auto-incrementing `id` as primary key for flexibility
- Store `goodreads_id` as unique field for API integration
- Use `DATE` type for start/finish dates to enable date calculations
- Include `status` field to track reading progress

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
   - Airflow scheduled job pulls data from Goodreads API
   - Data is cleaned and transformed
   - Data is loaded into local database

2. **API Layer**
   - FastAPI serves data from local database
   - Endpoints provide filtered and aggregated data
   - Real-time responses (no external API calls)

3. **Frontend**
   - JavaScript fetches data from FastAPI endpoints
   - Charts and visualizations display the data
   - Interactive filtering and exploration

### Development Approach

#### Phase 1: Foundation
- Set up basic FastAPI application
- Create database schema
- Implement basic CRUD operations

#### Phase 2: Data Integration
- Integrate with Goodreads API
- Build data ingestion pipeline
- Test with real data

#### Phase 3: Analytics
- Implement reading statistics calculations
- Build trend analysis endpoints
- Add data visualization

#### Phase 4: Frontend
- Create dashboard interface
- Implement charts and graphs
- Add interactive features

#### Phase 5: Production
- Deploy to AWS
- Set up monitoring and logging
- Optimize performance

### Key Learning Goals
- FastAPI patterns and best practices
- Database design and ORM usage
- External API integration
- Data pipeline development
- Full-stack application development
- AWS deployment and operations

## Next Steps
1. Set up development environment
2. Create basic FastAPI application
3. Design and implement database schema
4. Build first API endpoint
5. Test with sample data
