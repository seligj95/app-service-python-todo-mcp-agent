"""
Application entry point for Azure deployment.
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup to avoid linting issues
from src.app import create_app  # noqa: E402
from src.models import db  # noqa: E402

# Create Flask app
app = create_app()

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Get port from environment variable (Azure sets this as WEBSITES_PORT)
    port = int(os.environ.get('WEBSITES_PORT', os.environ.get('PORT', 8000)))
    app.run(debug=False, host='0.0.0.0', port=port)
