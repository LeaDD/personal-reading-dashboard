import httpx
import logging
import time
from datetime import date

logger = logging.getLogger(__name__)

def get_google_books_data(title: str, author: str, isbn_10: str | None = None, isbn_13: str | None = None) -> dict | None:
    """
    Query Google Books for a specific title/author combination.

    Args:
        title: Book title used for the Google Books search (required).
        author: Author name used for the search (required).
        isbn_10: ISBN-10 of the book (optional).
        isbn_13: ISBN-13 of the book (optional).

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

    def call_google_books_api(query: str, max_retries: int = 3) -> dict | None:
        """Helper function to make API call and return data if items found.
        
        Handles rate limiting (429) with exponential backoff retry logic.
        """
        params = {
            "q": query,
            "maxResults": 5,
            "orderBy": "relevance"
        }
        
        for attempt in range(max_retries):
            response = httpx.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data
                else:
                    return None  # No items found
            elif response.status_code == 429:  # Rate limit exceeded
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                    logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries} attempts for query: {query}")
                    return None
            else:
                logger.error(f"Error: status code {response.status_code} for query: {query}")
                logger.error(response.text)
                return None
        
        return None

    def process_api_response(data: dict) -> dict:
        """Process API response data into book dictionary."""
        first_result = data["items"][0]
        volume_info = first_result.get("volumeInfo", {})     

        # Parse the ISBNs from Google Books response
        google_books_isbn_10 = None
        google_books_isbn_13 = None

        for identifier in volume_info.get("industryIdentifiers", []):
            if identifier.get("type") == "ISBN_10":
                google_books_isbn_10 = identifier.get("identifier")
            elif identifier.get("type") == "ISBN_13":
                google_books_isbn_13 = identifier.get("identifier")

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
            "isbn_10": google_books_isbn_10 if google_books_isbn_10 else None,
            "isbn_13": google_books_isbn_13 if google_books_isbn_13 else None,
            "small_thumbnail": volume_info.get("imageLinks", {}).get("smallThumbnail"),
            "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail")        
        }
        
        return book

    # Try ISBN-13 first, then ISBN-10, then fallback to title/author
    if isbn_13:
        logger.info(f"Trying ISBN-13 search: {isbn_13}")
        result = call_google_books_api(f"isbn:{isbn_13}")
        if result:
            matched_title = result["items"][0].get("volumeInfo", {}).get("title", "Unknown")
            logger.info(f"✓ Match found via ISBN-13: '{matched_title}'")
            return process_api_response(result)
        else:
            logger.info(f"  No results for ISBN-13: {isbn_13}, falling back...")

    if isbn_10:
        logger.info(f"Trying ISBN-10 search: {isbn_10}")
        result = call_google_books_api(f"isbn:{isbn_10}")
        if result:
            matched_title = result["items"][0].get("volumeInfo", {}).get("title", "Unknown")
            logger.info(f"✓ Match found via ISBN-10: '{matched_title}'")
            return process_api_response(result)
        else:
            logger.info(f"  No results for ISBN-10: {isbn_10}, falling back...")

    # Fallback to title/author search
    logger.info(f"Trying title/author search: '{title}' by '{author}'")
    result = call_google_books_api(f"intitle:{title}+inauthor:{author}")
    if result:
        matched_title = result["items"][0].get("volumeInfo", {}).get("title", "Unknown")
        matched_authors = result["items"][0].get("volumeInfo", {}).get("authors", [])
        logger.info(f"✓ Match found via title/author: '{matched_title}' by {matched_authors}")
        return process_api_response(result)
    
    # No results found
    logger.warning(f"✗ No results found for '{title}' by '{author}' (tried ISBN-13: {isbn_13}, ISBN-10: {isbn_10})")
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


