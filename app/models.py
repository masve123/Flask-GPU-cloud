"""
ORM Concept: SQLAlchemy is an ORM library. ORM allows you to work with databases 
using high-level entities such as classes and objects rather than low-level database commands. 
It maps (or connects) these classes to database tables.

Class-to-Table Mapping: In SQLAlchemy, each class that inherits from ```db.Model``` is automatically 
mapped to a table in the database. The class name typically corresponds to the table name (in a lowercase format), 
and the class attributes correspond to the columns in the table.
"""

from datetime import datetime
from . import db

class User(db.Model):
    """Each user represents a user in the database"""
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
        """
        Converts the GPU instance into a dictionary, typically for JSON serialization.
        
        Purpose: This is typically used when sending data from the server to the client.
        """
        return {
            'id': self.id,
            'name': self.name,
            'gpu_type': self.gpu_type,
            'gpu_memory': self.gpu_memory,
            'status': self.status
        }
    
    def from_dict(self, data):
        """
        Updates the GPU instance based on a dictionary of new data, 
        typically coming from a JSON request.
        """
        for field in ['name', 'gpu_type', 'gpu_memory', 'status']:
            if field in data:
                setattr(self, field, data[field])

class GPU_booking(db.Model):
    """
    To track the booking/reservation of GPU instances.

    GPU_booking: This table should track the reservations or bookings 
    of the GPU instances. When a user books a GPU instance, a record 
    should be created in this table, linking the user to the specific 
    GPU instance they have booked, along with the booking time frame 
    (start_time and end_time)."""

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
    """
    To track usage statistics of GPU instances.
    
    This table could be used to track the actual usage of the GPU instances, 
    such as how long they were used, by whom, and other usage statistics. 
    This could be updated in real-time as the GPU is being used, or after 
    the usage has completed, depending on your application's design."""

    usage_id = db.Column(db.Integer, primary_key=True)
    gpu_id = db.Column(db.Integer, db.ForeignKey('gpu_instance.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('gpu_booking.booking_id'))
    usage_duration = db.Column(db.Integer, nullable=False)  # Example field

    # Relationship with GPU_instance
    gpu = db.relationship('GPU_instance', backref='usage', lazy=True)


    def __repr__(self):
        return '<GPU_usage %r>' % self.usage_id


