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
from sqlalchemy import Column, Integer, String, Enum
from enum import Enum as PyEnum

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



class GPU_status(PyEnum):
    """Enum helper class to represent the status of a GPU instance
    Note; this class inherits from the ENUM python standard library, not the SQLAlchemy Enum class."""
    AVAILABLE = 'available'
    IN_USE = 'in use'
    BOOKED = 'booked'
    MAINTENANCE = 'maintenance'
    # Add any other statuses you need



class GPU_instance(db.Model):
    """
    To represent each GPU instance that users can rent.

    Note; A ```GPU instance``` represents a single GPU entry, i.e a single
    GPU in the data center.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    gpu_type = db.Column(db.String(80), nullable=False)
    gpu_memory = db.Column(db.Integer, nullable=False)
    status = db.Column(Enum(GPU_status), default=GPU_status.AVAILABLE, nullable=False)
    # Relationship example (if you have bookings related to an instance)
    bookings = db.relationship('GPU_booking', backref='gpu', lazy=True)

    # additional fields, not implemented yet
    utilization_percentage = db.Column(db.Float, nullable=True)
    peak_memory_usage = db.Column(db.Integer, nullable=True)  # in MB or GB
    average_load = db.Column(db.Float, nullable=True)
    error_count = db.Column(db.Integer, nullable=True, default=0)
    energy_consumption = db.Column(db.Float, nullable=True)  # in kWh, if available
    max_temperature = db.Column(db.Float, nullable=True)  # in Celsius
    network_usage = db.Column(db.Float, nullable=True)  # in MB or GB

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
            'status': self.status.value,
            # additioal fields, not implemented yet
            'utilization_percentage': self.utilization_percentage,
            'peak_memory_usage': self.peak_memory_usage,
            'average_load': self.average_load,
            'error_count': self.error_count,
            'energy_consumption': self.energy_consumption,
            'max_temperature': self.max_temperature,
            'network_usage': self.network_usage
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
            'booking_id': self.booking_id,
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
    To track actual usage statistics of GPU instances.
    
    Tracks real-time usage of GPU instances, including start and end times,
    and calculates the duration of usage.

    Note; the start and end time of this class represents the actual usage,
    not the booking time as they can differ. For example, a user can book a GPU
    instance for 1 hour, but only use it for 30 minutes. In this case, the booking
    start and end time will be 1 hour apart, but the usage start and end time will
    be 30 minutes apart.
    """

    usage_id = db.Column(db.Integer, primary_key=True)
    gpu_id = db.Column(db.Integer, db.ForeignKey('gpu_instance.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('gpu_booking.booking_id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)  # Nullable as it's set when usage stops
    usage_duration = db.Column(db.Integer, nullable=True)  # Calculated after usage ends

    # Relationship with GPU_instance
    gpu = db.relationship('GPU_instance', backref='usage', lazy=True)

    def __repr__(self):
        return '<GPU_usage %r>' % self.usage_id
    

    def to_dict(self):
        """Converts GPU usage object to a dictionary."""
        return {
            'usage_id': self.usage_id,
            'gpu_id': self.gpu_id,
            'booking_id': self.booking_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'usage_duration': self.usage_duration
        }




