import logging
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def setup_logging():
    """
    Configure logging based on environment.
    - Development: Console logging at DEBUG level
    - Production: File logging at INFO level
    """

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create formatter for logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create handlers for logging to file or console
    if os.getenv("ENVIRONMENT") == "production":
        file_handler = logging.FileHandler(log_dir/"app.log")
        file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler() # Logs to console
    console_handler.setFormatter(formatter)

    # Create root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level based on environment
    if os.getenv("ENVIRONMENT") == "development":
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Set log level FIRST
    root_logger.setLevel(log_level)

    # Suppress verbose logging from third-party libraries (httpx returns a lot of DEBUG content)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Then add handlers
    if os.getenv("ENVIRONMENT") == "development":
        root_logger.addHandler(console_handler)
    else:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

if __name__ == "__main__":
    setup_logging()
