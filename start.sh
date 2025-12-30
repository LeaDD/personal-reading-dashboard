#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Run migrations and initialize DB if needed
python -m backend.app.init_db

# Start fastapi server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
