from fastapi import APIRouter, Depends, Query, HTTPException
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import String, cast, func
from backend.app.database import get_db, engine
from backend.app.schemas.books_schema import BookCreate, BookResponse
from backend.app.services.ingest_books_to_db import ingest_books_to_db
from backend.app.models.book_model import Book

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/books",
    tags=["books"],
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
    status: str | None = Query(None, description="Filter by status"),
    genre: str | None = Query(None, description="Filter by genre"),
    author: str | None = Query(None, description="Filter by author"),
    year_published: int | None = Query(None, description="Filter by publication year"),
    # title: str | None = Query(None, "Filter by book title."),
    db: Session = Depends(get_db)
) -> list[BookResponse]:
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
        logger.error(f"Database exception occurred: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while fetching books."
        )
    except Exception as e:
        logger.error(f"Unexpected exception occurred while fetching books from database: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching books."
        )

@router.get("/{book_id}", status_code=200)
async def get_book_by_id(
    book_id: int,
    db: Session = Depends(get_db) 
) -> BookResponse:

    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        book_response = BookResponse.model_validate(book)
        return book_response
    except SQLAlchemyError as e:
        logger.error(f"Database exception occurred: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database error occurred while fetching books."
        )
    except Exception as e:
        logger.error(f"Unexpected exception occurred while fetching books from database: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching books."
        )


# Disable code hints/completions: settings -> tab -> de-select cursror tab