from sqlalchemy import Column, DateTime, String
from datetime import datetime, timezone


from app import db

class Image(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    red_pixels = db.Column(db.Integer, nullable=False)
    green_pixels = db.Column(db.Integer, nullable=False)
    blue_pixels = db.Column(db.Integer, nullable=False)
    original_image_url = db.Column(db.String(255), nullable=False)
    processed_image_url = db.Column(db.String(255), nullable=False)
    user_name             = Column(String(100), nullable=False) 
    reception_date        = Column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),nullable=False)