import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, 'static', 'uploads')

# Ensure upload directory exists with proper permissions
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.chmod(app.config["UPLOAD_FOLDER"], 0o755)

db.init_app(app)

# Register routes after db initialization
with app.app_context():
    from routes import register_routes
    register_routes(app)
    
    import models
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
