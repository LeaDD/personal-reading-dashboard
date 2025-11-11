from backend.app.database import engine, Base
from backend.app.models.book import Book

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    
