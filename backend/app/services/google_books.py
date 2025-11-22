import httpx
import logging
from datetime import date

logger = logging.getLogger(__name__)

def get_google_books_data(title: str, author: str) -> dict | None:
    """
    Query Google Books for a specific title/author combination.

    Args:
        title: Book title used for the Google Books search (required).
        author: Author name used for the search (required).

    Returns:
        dict | None: 
            A dictionary with the most relevant volume data, including keys:
            - google_books_id: str
            - google_books_link: str
            - title: str
            - authors: list[str] | None
            - published_date: date | None
            - year_published: int | None
            - page_count: int | None
            - categories: list[str] | None
            - genre: str | None
            - description: str | None
            - isbn_10: str | None
            - isbn_13: str | None
            - small_thumbnail: str | None
            - thumbnail: str | None
            Returns None when no items are found.

    Notes:
        - Logs INFO when the lookup starts, WARNING when no results are found, and ERROR when the API returns a non-200 response.
        - Any HTTP or parsing exceptions from httpx are propagated to the caller.
    """
    logger.info(f"Getting Google Books data for {title} by {author}")

    base_url = "https://www.googleapis.com/books/v1/volumes"

    query = f"intitle:{title}+inauthor:{author}"

    params = {
        "q": query,
        "maxResults": 5,
        "orderBy": "relevance"  # Sort by relevance
    }

    response = httpx.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data.get("items"):
            first_result = data["items"][0]
            volume_info = first_result.get("volumeInfo", {})     

            # Parse the ISBNs
            isbn_10 = None
            isbn_13 = None

            for identifier in volume_info.get("industryIdentifiers", []):
                if identifier.get("type") == "ISBN_10":
                    isbn_10 = identifier.get("identifier")
                elif identifier.get("type") == "ISBN_13":
                    isbn_13 = identifier.get("identifier")

        
            # Parse the published date
            if volume_info.get("publishedDate"):
                date_parts = volume_info.get("publishedDate").split("-")

                if len(volume_info.get("publishedDate")) == 4:
                    book_publish_date = date(int(volume_info.get("publishedDate")), 1, 1)
                elif len(volume_info.get("publishedDate")) == 7:
                    book_publish_date = date(int(date_parts[0]), int(date_parts[1]), 1)
                elif len(volume_info.get("publishedDate")) == 10:
                    book_publish_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                else:
                    book_publish_date = None
            else:
                book_publish_date = None

            # Assemble the book dictionary
            book = {
                "google_books_id": first_result.get("id"),
                "google_books_link": first_result.get("selfLink"),
                "title": volume_info.get("title") if volume_info.get("title") else title,
                "authors": volume_info.get("authors") if volume_info.get("authors") else [author],
                "published_date": book_publish_date,
                "year_published": book_publish_date.year if book_publish_date else None,
                "page_count": volume_info.get("pageCount"),
                "categories": volume_info.get("categories"),
                "genre": volume_info.get("categories")[0] if volume_info.get("categories") else None,
                "description": volume_info.get("description"),
                "isbn_10": isbn_10 if isbn_10 else None,
                "isbn_13": isbn_13 if isbn_13 else None,
                "small_thumbnail": volume_info.get("imageLinks", {}).get("smallThumbnail"),
                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail")        }

            
            return book
        else: 
            logger.warning(f"No results found for {title} by {author}")
            return None
            
    else:
        logger.error(f"error: status code {response.status_code}")
        logger.error(response.text)
        return None

if __name__ == "__main__":
    from backend.app.config.logging_config import setup_logging
    setup_logging()

    # Test with a known book from user's CSV
    logger.info("=== TEST 1: Restaurant at End of Universe ===\n")
    book1 = get_google_books_data("The Restaurant at the End of the Universe", "Douglas Adams")
    logger.info(book1)
    
    # Test with another book to check for categories
    print("\n\n=== TEST 2: Testing for Categories ===\n")
    book2 = get_google_books_data("The Sign of Four", "Sir Arthur Conan Doyle")       
    logger.info(book2)


