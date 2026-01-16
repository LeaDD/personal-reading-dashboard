"""
Dependencies for FastAPI routes (authentication, etc.)
"""
from fastapi import Header, HTTPException, status
import os
from typing import Annotated

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")


def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    """
    Dependency to verify API key in request headers.
    
    Expects 'X-API-Key' header with the API key value.
    Raises 401 if key is missing or invalid.
    
    Args:
        x_api_key: API key from 'X-API-Key' header
        
    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    # If no API_KEY is configured, allow all requests (development mode)
    if not API_KEY:
        return
    
    # If API_KEY is configured, require it in the request
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include 'X-API-Key' header."
        )
    
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )



