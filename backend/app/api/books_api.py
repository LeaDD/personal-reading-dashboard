from fastapi import APIRouter, Depends, Query, HTTPException, Path
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import String, cast, func
from backend.app.database import get_db, engine
from backend.app.schemas.books_schema import BookCreate, BookResponse, StatsResponse, TrendsResponse
from backend.app.services.ingest_books_to_db import ingest_books_to_db
from backend.app.models.book_model import Book
from typing import Annotated

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

def endpoint_exception_handler(e: Exception, exc_category: str, function_name: str):
    logger.error(f"An {exc_category} exception occurred: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail=f"While {function_name}: {exc_category} error occurred while fetching books."
    )


@router.post("/ingest", status_code=201)
async def ingest_books(
    books: list[BookCreate],
    db: Session = Depends(get_db)
) -> dict[str, int | str]:
    logger.info(f"Ingesting {len(books)} books via API endpoint")
    return ingest_books_to_db(books, db)
    

@router.get("/", status_code=200)
async def get_books(
    status: Annotated[str, Query(description="Filter by status")] = None,
    genre: Annotated[str, Query(description="Filter by genre")] = None,
    author: Annotated[str, Query(description="Filter by author")] = None,
    year_published: Annotated[int, Query(description="Filter by publication year")] = None,
    # title: str | None = Query(None, "Filter by book title."),
    db: Session = Depends(get_db)
) -> list[BookResponse]:
    """
    Retrieve a list of BookResponse objects using one (or more) of the four available query parameters.
    """
    query = db.query(Book)

    if status:
        query = query.filter(Book.status == status)
    if genre:
        query = query.filter(func.lower(Book.genre) == genre.lower())
    if author:
        # Check if author exists in JSON array - database-specific approach
        db_dialect = engine.dialect.name
        if db_dialect == 'postgresql':
            # PostgreSQL JSONB: use native contains operator
            query = query.filter(Book.authors.contains([author]))
        else:
            # SQLite: cast JSON to text and search (simple but works for testing)
            query = query.filter(func.lower(cast(Book.authors, String)).contains(f'{author.lower()}'))
    if year_published:
        query = query.filter(Book.year_published == year_published)

    try:
        books = query.all()
        logger.info(f"Query returned {len(books)} results.")

         # Convert SQLAlchemy models to Pydantic models using from_attributes (see schema definition in books_schema)
        return [BookResponse.model_validate(book) for book in books]

    except SQLAlchemyError as e:
        endpoint_exception_handler(e, "database", "get_books")
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "get_books")

@router.get("/reading-stats", status_code=200)
async def get_reading_stats(db: Session = Depends(get_db)) -> StatsResponse:
    try:     
        # Aggregate genres data
        genres = db.query(
            Book.genre,
            func.count(Book.title).label("books_count"),
            func.sum(Book.page_count).label("pages_count")
        ).filter(
            Book.status == "read"
        ).group_by(
            Book.genre
        ).all()

        # And place in collection
        genre_breakdown = [
            {
                "genre": row.genre,
                "books_count": row.books_count,
                "pages_count": row.pages_count or 0  # Handle None from sum() when page_count is null
            }
            for row in genres
        ]

        # Reading totals
        results = db.query(
            func.sum(Book.page_count).label("total_pages_read"), 
            func.count(Book.title).label("total_books_read"),
            func.round(func.avg(Book.page_count), 2).label("avg_pages_per_book")
        ).filter(
            Book.status == "read"
        ).first()

        stats = {
                "total_pages_read": results.total_pages_read or 0,  # Handle None from sum() when no books or all page_count are null
                "total_books_read": results.total_books_read or 0,  # Handle None from count() (shouldn't happen, but defensive)
                "avg_pages_per_book": float(results.avg_pages_per_book) if results.avg_pages_per_book else 0.0,  # Handle None from avg()
                "genre_breakdown": genre_breakdown
        }
            
        # Pass stats into response schema (Pydantic will validate genre_breakdown dicts against GenreCount schema)
        stats_response = StatsResponse.model_validate(stats)
        
        logger.info(f"Reading stats: {stats_response.total_books_read} books, {stats_response.total_pages_read} pages, {len(stats_response.genre_breakdown)} genres")
        return stats_response

    except SQLAlchemyError as e:
        endpoint_exception_handler(e, "database", "get_reading_stats")
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "get_reading_stats")

@router.get("/reading-trends", status_code=200)
async def get_reading_trends(
    db: Session = Depends(get_db)
) -> list[TrendsResponse]:
    try:
        # Database-specific date extraction
        db_dialect = engine.dialect.name
        if db_dialect == 'postgresql':
            year_read = func.extract('year', Book.finish_date).label("year_read")
            month_read = func.extract('month', Book.finish_date).label("month_read")
        else:  # SQLite
            year_read = func.strftime('%Y', Book.finish_date).label("year_read")
            month_read = func.strftime('%m', Book.finish_date).label("month_read")

        results = db.query(
            year_read,
            month_read,
            func.sum(Book.page_count).label("pages_read"), 
            func.count(Book.title).label("books_read"),
            Book.genre
        ).filter(
            Book.status == "read",
            Book.finish_date.isnot(None)
        ).group_by(
            year_read,
            month_read,
            Book.genre
        ).all()
        
        trends = [
            {
                "year_read": row.year_read,
                "month_read": row.month_read,
                "pages_read": row.pages_read or 0,  # Handle None from sum() when page_count is null
                "books_read": row.books_read,
                "genre": row.genre or "Unknown"  # Handle None genre (shouldn't happen due to filter, but defensive)
            }
            for row in results
        ]

        # Pass trends into response schema
        trends_response = [TrendsResponse.model_validate(row) for row in trends]
        
        return trends_response

    except SQLAlchemyError as e:
        endpoint_exception_handler(e, "database", "get_reading_trends")
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "get_reading_trends")

@router.get("/{book_id}", status_code=200)
async def get_book_by_id(
    book_id: Annotated[int, Path(description="Unique ID of book to be returned.")],
    db: Session = Depends(get_db) 
) -> BookResponse:

    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            book_response = BookResponse.model_validate(book)
            return book_response
        else:
            raise HTTPException(status_code=404, detail="Record not found.")

    except SQLAlchemyError as e:
        endpoint_exception_handler(e, "database", "get_book_by_id")
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "get_book_by_id")





