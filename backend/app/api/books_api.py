from fastapi import APIRouter, Depends, Query, HTTPException, Path
import logging
from typing import Annotated, Literal

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import String, cast, func

from backend.app.database import get_db, engine
from backend.app.dependencies import verify_api_key
from backend.app.schemas.books_schema import BookCreate, BookResponse, StatsResponse, TrendsResponse, CSVBook
from backend.app.services.ingest_books_to_db import ingest_books_to_db
from backend.app.services.delete_books import delete_books
from backend.app.services.update_books import update_books
from backend.app.models.book_model import Book


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/books",
    tags=["books"],
    dependencies=[Depends(verify_api_key)],  # Require API key for all /books endpoints
)

def endpoint_exception_handler(e: Exception, exc_category: str, function_name: str):
    # If it's already an HTTPException, re-raise it unchanged
    if isinstance(e, HTTPException):
        raise e

    # Log full details server-side (for debugging)
    logger.error(f"An {exc_category} exception occurred: {e}", exc_info=True)
    # Return generic message to client (no internal details)

    raise HTTPException(
        status_code=500,
        detail=f"An internal server error occurred while {function_name}. Please try again later or contact support if the issue persists."
    )


@router.post("/ingest", status_code=201)
async def ingest_books(
    books: list[BookCreate],
    db: Session = Depends(get_db)
) -> dict[str, int | str]:
    """
    Ingest one or more books into the database.
    
    Accepts a list of BookCreate objects (enriched with Google Books metadata)
    and persists them to the database. Books are validated using Pydantic schemas
    before insertion.
    
    Args:
        books: List of BookCreate objects to be ingested
        db: Database session (injected via dependency)
    
    Returns:
        dict containing count of books ingested: {"books_ingested": int}
    
    Raises:
        HTTPException: 500 if database operation fails
    """
    logger.info(f"Ingesting {len(books)} books via API endpoint")
    return ingest_books_to_db(books, db)

@router.post("/delta-delete", status_code=200)
async def delete_books_delta(
    books_to_delete: list[CSVBook],
    db: Session = Depends(get_db)
) -> dict[str, int]:
    """
    Delete books from the database that are no longer in the CSV export.
    
    Compares incoming CSV book list with existing database records and
    deletes any books that are present in the database but not in the
    incoming CSV (indicating they were removed from Goodreads library).
    
    Args:
        books_to_delete: List of CSVBook objects from the CSV export    
        db: Database session
    
    Returns:
        dict with count of books deleted: {"books_deleted": int}
    """
    try:
        result = delete_books(books_to_delete, db)
        logger.info(f"Deleting {result.get('books_deleted')} records.")
        return result
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "batch-delete")

@router.post("/batch-update", status_code=200)
async def batch_update_books(
    books_to_update: list[CSVBook],
    db: Session = Depends(get_db)
) -> dict[str, int]:
    """
    Batch update book statuses from CSV export data.
    
    Compares incoming CSV book list with existing database records and
    updates the status field for any books where the status has changed.
    Only books that exist in the database and have a different status
    than the incoming CSV will be updated.
    
    Args:
        books_to_update: List of CSVBook objects from the CSV export
        db: Database session (injected via dependency)
    
    Returns:
        dict with count of books updated: {"books_updated": int}
    
    Raises:
        HTTPException: 500 if database operation fails
    
    Note:
        This endpoint is designed for syncing book statuses from Goodreads
        CSV exports. It only updates the status field and does not modify
        other book properties.
    """
    try:
        result = update_books(books_to_update, db)
        logger.info(f"Updating {result.get('books_updated')} records.")
        return result
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "batch-update")
    

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
    """
    Retrieve aggregate reading statistics.
    
    Returns comprehensive reading statistics including total books read,
    total pages read, average pages per book, and a genre breakdown.
    Only includes books with status "read".
    
    Args:
        db: Database session (injected via dependency)
    
    Returns:
        StatsResponse containing:
        - total_pages_read: Sum of all page counts
        - total_books_read: Count of all read books
        - avg_pages_per_book: Average pages per book
        - genre_breakdown: List of genre counts with books and pages per genre
    
    Raises:
        HTTPException: 500 if database operation fails
    """
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
    """
    Retrieve reading trends over time.
    
    Returns time-based reading analysis grouped by year, month, and genre.
    Only includes books with status "read" that have a finish_date.
    
    Args:
        db: Database session (injected via dependency)
    
    Returns:
        List of TrendsResponse objects, each containing:
        - year_read: Year in which reading was completed
        - month_read: Month in which reading was completed
        - pages_read: Total pages read for that time period
        - books_read: Number of books read for that time period
        - genre: Genre of books read
    
    Raises:
        HTTPException: 500 if database operation fails
    """
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
    """
    Retrieve a single book by its database ID.
    
    Args:
        book_id: Unique database ID of the book to retrieve
        db: Database session (injected via dependency)
    
    Returns:
        BookResponse containing complete book information
    
    Raises:
        HTTPException: 
            - 404 if book with the given ID is not found
            - 500 if database operation fails
    """

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

@router.delete("/{book_id}", status_code=204)
async def delete_book_by_id(
    book_id: Annotated[int, Path(description="Unique ID of book to be deleted.")],
    db: Session = Depends(get_db)
):
    """
    Delete a book from the database by its ID.
    
    Args:
        book_id: Unique database ID of the book to delete
        db: Database session (injected via dependency)
    
    Returns:
        None (204 No Content on success)
    
    Raises:
        HTTPException:
            - 404 if book with the given ID is not found
            - 500 if database operation fails
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            db.delete(book)
            db.commit()
            logger.info(f"{book.title} successfully deleted.")
        else:
            raise HTTPException(status_code=404, detail="Record not found.")

    except SQLAlchemyError as e:
        endpoint_exception_handler(e, "database", "delete_book_by_id")
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "delete_book_by_id")

@router.put("/{book_id}", status_code=204)
async def update_book_by_id(
    book_id: Annotated[int, Path(description="Unique ID of book to be updated.")],
    new_status: Annotated[Literal["read", "currently-reading", "to-read"], Query(description="New status of book.")],
    db: Session = Depends(get_db)
):
    """
    Update a book's status by its database ID.
    
    Updates the status field of a book record. Valid status values are:
    "read", "currently-reading", "to-read".
    
    Args:
        book_id: Unique database ID of the book to update
        new_status: New status value for the book
        db: Database session (injected via dependency)
    
    Returns:
        None (204 No Content on success)
    
    Raises:
        HTTPException:
            - 404 if book with the given ID is not found
            - 500 if database operation fails
    
    Note:
        Currently only updates the status field. Future versions may support
        updating additional fields.
    """
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            book.status = new_status
            db.commit()
            logger.info(f"{book.title} has been updated to status {book.status}")
    
    except SQLAlchemyError as e:
        endpoint_exception_handler(e, "database", "update_book_by_id")
    except Exception as e:
        endpoint_exception_handler(e, "unexpected", "update_book_by_id")
