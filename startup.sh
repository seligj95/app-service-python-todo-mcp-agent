#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.app import create_app
from src.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"

# Start the application
exec gunicorn --bind=0.0.0.0:$PORT --workers=2 --timeout=600 --keep-alive=2 --max-requests=1000 --max-requests-jitter=50 --preload main:app
