from backend.app.database import engine, Base
from backend.app.models.book_model import Book

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    
