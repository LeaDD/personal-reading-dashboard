from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models.book_model import Book
from backend.app.schemas.books_schema import BookCreate
import logging

logger = logging.getLogger(__name__)

def ingest_books_to_db(books: list[BookCreate], db: Session) -> dict[str, int | str]:

    """
    Ingest books into the database.
    
    Accepts a list of BookCreate Pydantic objects and writes them to the database.
    This function can be called directly (e.g., from orchestration scripts) or from API endpoints.
    When called from an API endpoint, FastAPI automatically converts incoming JSON to BookCreate objects
    before passing them to this function. When called directly, BookCreate objects are passed as-is.
    
    Each book is converted from a Pydantic model to a SQLAlchemy model and saved to the database.
    
    Args:
        books: List of BookCreate instances (Pydantic objects, not JSON)
        db: Database session (SQLAlchemy Session object)
        
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

