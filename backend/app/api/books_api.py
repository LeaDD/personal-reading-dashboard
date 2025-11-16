from fastapi import APIRouter, Depends, HTTPException, status
import logging
from backend.app.database import get_db
from backend.app.schemas.books_schema import BookCreate
from sqlalchemy.orm import Session
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
    """
    Ingest books into the database.
    
    Accepts a list of books validated against the BookCreate Pydantic schema.
    FastAPI automatically validates incoming JSON and converts types (e.g., date strings to date objects).
    Each book is converted from a Pydantic model to a SQLAlchemy model and saved to the database.
    
    Args:
        books: List of BookCreate instances (automatically created by FastAPI from JSON)
        db: Database session (injected by FastAPI dependency)
        
    Returns:
        dict with success message and count of books ingested
        
    Raises:
        HTTPException: If database operation fails (500 status)
    """
    logger.info(f"Ingesting {len(books)} books")

    try:
        book_instances = []
        for book_create in books:
            # Convert Pydantic model to dict, then unpack into SQLAlchemy model
            # Pydantic handles validation and type conversion (dates, etc.) automatically
            book_data = book_create.model_dump()
            book_instance = Book(**book_data)
            book_instances.append(book_instance)
        
        db.add_all(book_instances)
        db.commit()
        logger.info(f"Successfully ingested {len(book_instances)} books")
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting books: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"message": "Books ingested successfully", "count": len(book_instances)}




