from fastapi import APIRouter, Depends, HTTPException, status
import logging
from backend.app.database import get_db
from sqlalchemy.orm import Session
from backend.app.models import Book
from typing import Any
from datetime import datetime, date

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

@router.post("/ingest", status_code=201)
async def ingest_books(
    books: list[dict[str, Any]],
    db: Session = Depends(get_db)
) -> dict[str, int | str]:
    logger.info("Ingesting new books")

    try:
        book_instances = []
        for book_dict in books:
            # Parse date strings to date objects
            if "published_date" in book_dict and isinstance(book_dict["published_date"], str):
                book_dict["published_date"] = datetime.strptime(book_dict["published_date"], "%Y-%m-%d").date()
            if "finish_date" in book_dict and isinstance(book_dict["finish_date"], str):
                book_dict["finish_date"] = datetime.strptime(book_dict["finish_date"], "%Y-%m-%d").date()
            
            book_instance = Book(**book_dict)
            book_instances.append(book_instance)
        db.add_all(book_instances)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error ingesting books: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"message": "Books ingested successfully", "count": len(books)}




