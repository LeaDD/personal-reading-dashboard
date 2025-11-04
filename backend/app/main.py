from fastapi import FastAPI, status
import logging 

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Personal Reading Dashboard API",
    description="API for personal reading analytics and insights",
    version="0.1.0"
)

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Personal Reading Dashboard API is running"}

@app.get("/healthy", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}

