"""
ORM Concept: SQLAlchemy is an ORM library. ORM allows you to work with databases 
using high-level entities such as classes and objects rather than low-level database commands. 

It maps (or connects) these classes to database tables.
Class-to-Table Mapping: In SQLAlchemy, each class that inherits from db.Model is automatically 
mapped to a table in the database. The class name typically corresponds to the table name (in a lowercase format), 
and the class attributes correspond to the columns in the table.
"""

from datetime import datetime
from . import db

class User(db.Model):
    """User model."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # add additional fields as needed

    def __repr__(self):
        return '<User %r>' % self.username
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
    
    def from_dict(self, data):
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])


class GPU_instance(db.Model):
    """To represent each GPU instance that users can rent."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    gpu_type = db.Column(db.String(80), nullable=False)
    gpu_memory = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(80), nullable=False, default='available')
    # Relationship example (if you have bookings related to an instance)
    bookings = db.relationship('GPU_booking', backref='gpu', lazy=True)

    def __repr__(self):
        return '<GPU_instance %r>' % self.name
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gpu_type': self.gpu_type,
            'gpu_memory': self.gpu_memory
        }
    
    def from_dict(self, data):
        for field in ['name', 'gpu_type', 'gpu_memory']:
            if field in data:
                setattr(self, field, data[field])

class GPU_booking(db.Model):
    """To track the booking/reservation of GPU instances."""
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gpu_id = db.Column(db.Integer, db.ForeignKey('gpu_instance.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


    def __repr__(self):
        return '<GPU_booking %r>' % self.booking_id
    
    def to_dict(self):
        return {
            'id': self.booking_id,
            'user_id': self.user_id,
            'gpu_id': self.gpu_id,
            'start_time': self.start_time,
            'end_time': self.end_time
        }   
    
    def from_dict(self, data):
        for field in ['user_id', 'gpu_id', 'start_time', 'end_time']:
            if field in data:
                setattr(self, field, data[field])
    



class GPU_usage(db.Model):
    """To track usage statistics of GPU instances."""
    usage_id = db.Column(db.Integer, primary_key=True)
    gpu_id = db.Column(db.Integer, db.ForeignKey('gpu_instance.id'), nullable=False)
    usage_duration = db.Column(db.Integer, nullable=False)  # Example field

    def __repr__(self):
        return '<GPU_usage %r>' % self.usage_id


