from datetime import datetime
from app import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    animal = db.Column(db.String(100), nullable=False)
    task_type = db.Column(db.String(10), nullable=False)  # 'daily' or 'weekly'
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

class AnimalSpotting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    image_path = db.Column(db.String(255))
    recognition_result = db.Column(db.String(100))
    confidence_score = db.Column(db.Float)
    spotted_at = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(100))
