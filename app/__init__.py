from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

# Initialize database globally
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import and register blueprints (routes)
    from app.routes import main
    app.register_blueprint(main)

    return app
