from datetime import datetime
import uuid
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
    share_id = db.Column(db.String(50), unique=True)
    task = db.relationship('Task', backref=db.backref('spottings', lazy=True))
    badges = db.relationship('Badge', secondary='spotting_badges', back_populates='spottings')

    def generate_share_id(self):
        if not self.share_id:
            self.share_id = str(uuid.uuid4())[:8]
        return self.share_id

    @property
    def share_url(self):
        return f"/share/{self.share_id}"

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    icon_class = db.Column(db.String(50))  # Font Awesome icon class
    criteria = db.Column(db.String(100), nullable=False)  # e.g., 'first_spot', 'daily_5', 'weekly_complete'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    spottings = db.relationship('AnimalSpotting', secondary='spotting_badges', back_populates='badges')

# Association table for many-to-many relationship between AnimalSpotting and Badge
spotting_badges = db.Table('spotting_badges',
    db.Column('spotting_id', db.Integer, db.ForeignKey('animal_spotting.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True),
    db.Column('awarded_at', db.DateTime, default=datetime.utcnow)
)
