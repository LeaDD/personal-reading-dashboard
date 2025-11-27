from fastapi import APIRouter, Depends
import logging
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.books_schema import BookCreate
from backend.app.services.ingest_books_to_db import ingest_books_to_db

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
    




