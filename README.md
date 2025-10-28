# Personal Reading Analytics Dashboard

A FastAPI-based personal reading analytics system that pulls data from Goodreads API, processes it for personal insights, and serves it via REST endpoints with a simple frontend dashboard.

## Project Structure

```
personal-reading-dashboard/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── schemas/        # Pydantic schemas for API
│   │   ├── api/           # API route handlers
│   │   ├── services/      # Business logic
│   │   └── database.py    # Database configuration
│   ├── tests/             # Test files
│   └── alembic/           # Database migrations
├── frontend/              # Simple HTML/CSS/JS dashboard
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md
```

## Features

### Backend (FastAPI)
- **Data ingestion** - Pull from Goodreads API
- **Personal analytics** - Custom insights and trends
- **Data storage** - SQLite (dev) / PostgreSQL (prod)
- **API endpoints** - RESTful API for all analytics

### Frontend (Dashboard)
- **Reading statistics** - Books read, pages, genres
- **Trends visualization** - Charts showing reading patterns
- **Interactive filtering** - Filter by date, genre, rating
- **Real-time updates** - Live data from API

## API Endpoints

```
GET /books - List all books with filters
GET /books/{book_id} - Get specific book details
GET /reading-stats - Personal reading statistics
GET /reading-trends - Reading patterns over time
GET /genre-breakdown - Genre distribution analysis
POST /reading-sessions - Log reading time
GET /goals/progress - Track reading goals
GET /recommendations - Personalized suggestions
```

## Getting Started

1. **Set up environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Goodreads API key and database settings
   ```

3. **Run the development server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

4. **Open the dashboard:**
   ```bash
   # Open frontend/index.html in your browser
   ```

## Learning Goals

- ✅ FastAPI patterns and best practices
- ✅ API design and data modeling
- ✅ External API integration
- ✅ Database design and migrations
- ✅ Data visualization
- ✅ AWS deployment
- ✅ Full-stack development

## Technology Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL/SQLite
- **Frontend:** Vanilla JavaScript, Chart.js
- **Deployment:** AWS (EC2, RDS)
- **Testing:** pytest
- **Data:** Goodreads API