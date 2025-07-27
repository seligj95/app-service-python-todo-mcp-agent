"""
Application entry point for Azure deployment.
"""
import os
import sys

# Add the current directory to Python path FIRST
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"Python path: {sys.path}")
print(f"Current directory: {current_dir}")
print(f"Files in current directory: {os.listdir(current_dir)}")

try:
    # Import after path setup to avoid linting issues
    from src.app import create_app  # noqa: E402
    from src.models import db  # noqa: E402
    print("Imports successful")
    
    # Create Flask app (this happens when Gunicorn imports this file)
    app = create_app()
    print("Flask app created successfully")
    
    # Initialize database tables (this needs to happen when the module loads)
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
        
except ImportError as e:
    print(f"Import error: {e}")
    print(f"sys.path: {sys.path}")
    # Fallback: create a simple Flask app
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return "Hello, deployment debugging!"
    
    @app.route('/health')
    def health():
        return {"status": "healthy", "message": "Basic Flask app running"}

if __name__ == '__main__':
    # This only runs when executed directly, not through Gunicorn
    port = int(os.environ.get('WEBSITES_PORT', os.environ.get('PORT', 8000)))
    app.run(debug=False, host='0.0.0.0', port=port)
