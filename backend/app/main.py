from fastapi import FastAPI, status
# from fastapi.middleware.cors import CORSMiddleware
from backend.app.config.logging_config import setup_logging
from backend.app.api import books_api

setup_logging()

app = FastAPI(
    title="Personal Reading Dashboard API",
    description="API for personal reading analytics and insights",
    version="0.1.0"
)

# # Add CORS middleware to allow requests from your Flask frontend
# # For production, restrict allow_origins to your actual domain(s)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for testing - restrict in production
#     allow_credentials=False,  # Must be False when using allow_origins=["*"]
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Personal Reading Dashboard API is running"}

@app.get("/healthy", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}

app.include_router(books_api.router)

# start with uvicorn backend.app.main:app --reload