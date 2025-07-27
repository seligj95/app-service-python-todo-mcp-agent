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
flask_app = create_app()

# Initialize database tables
with flask_app.app_context():
    db.create_all()

# Create ASGI app for Uvicorn
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402
flask_app.wsgi_app = ProxyFix(
    flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# For Uvicorn
try:
    from asgiref.wsgi import WsgiToAsgi  # noqa: E402
    app = WsgiToAsgi(flask_app)
except ImportError:
    # Fallback: use Flask directly
    app = flask_app

if __name__ == '__main__':
    flask_app.run(debug=False, host='0.0.0.0', port=8000)
