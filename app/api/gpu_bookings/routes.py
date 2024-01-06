"""
This is where we set up our API endpoints for the gpu bookings.
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db
from app.utils import validate_booking_dates

from flask import Blueprint

from datetime import datetime, timedelta
from sqlalchemy import func

gpu_bookings_blueprint = Blueprint('gpu_bookings', __name__)



############## GPU Booking endpoint functions ##############

# Endpoint for users to book an available GPU instance.
@gpu_bookings_blueprint.route('/', methods=['POST'])
def book_gpu_instance():
    """
    Book an available GPU instance
    ---
    tags:
      - GPU Bookings
    description: Book an existing GPU instance. Ensures that start and end times are valid.
    parameters:
      - in: body
        name: body
        schema:
          id: GPUBooking
          required:
            - user_id
            - gpu_id
            - start_time
            - end_time
          properties:
            user_id:
              type: integer
              description: ID of the user booking the GPU.
            gpu_id:
              type: integer
              description: ID of the GPU instance to be booked.
            start_time:
              type: string
              format: date-time
              description: The start time of the booking.
            end_time:
              type: string
              format: date-time
              description: The end time of the booking.
    responses:
      201:
        description: GPU instance booked successfully.
      400:
        description: Validation error (instance not available, invalid time, etc.).
      500:
        description: Error in booking process.
    """
    data = request.json
    gpu_instance = GPU_instance.query.get(data['gpu_id'])

    # Validate GPU instance existence and availability
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404
    if gpu_instance.status != GPU_status.AVAILABLE:
        return jsonify({'message': 'GPU instance not available'}), 400

    # Parse and validate start and end times
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'message': 'Invalid date format'}), 400

    valid_dates, message = validate_booking_dates(start_time, end_time)
    if not valid_dates:
        return jsonify({'message': message}), 400
    
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404


    # Create and commit the booking
    booking = GPU_booking(user_id=data['user_id'], gpu_id=gpu_instance.id, start_time=start_time, end_time=end_time)
    db.session.add(booking)
    gpu_instance.status = GPU_status.BOOKED
    db.session.commit()

    return jsonify({'message': 'GPU instance booked successfully!'}), 201



@gpu_bookings_blueprint.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel_gpu_booking(booking_id):
    # Retrieve the booking
    booking = GPU_booking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    if booking.is_cancelled:
        return jsonify({'message': 'Booking is already cancelled'}), 400

    # Perform the soft delete
    booking.soft_delete()

    # Retrieve the associated GPU instance and update its status
    gpu_instance = GPU_instance.query.get(booking.gpu_id)
    if gpu_instance:
        gpu_instance.status = GPU_status.AVAILABLE

    # Commit the changes to the database
    db.session.commit()

    return jsonify({'message': 'GPU booking cancelled successfully'}), 200




def is_available(gpu_id, start_time, end_time):
    """
    Checks if a GPU instance is available for booking during the specified time frame.
    """
    # Check if the GPU instance is available
    gpu_instance = GPU_instance.query.get(gpu_id)
    if not gpu_instance or gpu_instance.status != GPU_status.AVAILABLE:
        return False

    # Check for booking conflicts
    conflicting_bookings = GPU_booking.query.filter(
        GPU_booking.gpu_id == gpu_id,
        GPU_booking.start_time < end_time,
        GPU_booking.end_time > start_time,
        GPU_booking.is_cancelled == False  # Exclude cancelled bookings
    ).all()
    if conflicting_bookings:
        return False

    return True





# Endpoint to list all GPU bookings.
@gpu_bookings_blueprint.route('/', methods=['GET'])
def get_all_active_gpu_bookings():
    """
    List all active GPU bookings 
    ---
    tags:
      - GPU Bookings
    description: Retrieve a list of all GPU bookings.
    responses:
      200:
        description: A list of all GPU bookings.
    """
    bookings = GPU_booking.query.filter_by(is_cancelled=False).all()  # Exclude cancelled bookings
    return jsonify([booking.to_dict() for booking in bookings])

# Endpoint to list all cancelled GPU bookings.
@gpu_bookings_blueprint.route('/cancelled', methods=['GET'])
def get_cancelled_gpu_bookings():
    """
    List all cancelled GPU bookings.
    The limit is set to the 100 most recent cancelled bookings.
    ---
    tags:
      - GPU Bookings
    description: Retrieve a list of all cancelled GPU bookings.
    responses:
      200:
        description: A list of all cancelled GPU bookings.
    """
    cancelled_bookings = GPU_booking.query.filter_by(is_cancelled=True).order_by(GPU_booking.booking_id.desc()).limit(100)  # Get the most recent 100 cancelled bookings
    return jsonify([booking.to_dict() for booking in cancelled_bookings])


# Endpoint to update the details of a GPU booking.
@gpu_bookings_blueprint.route('/update/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """
    Update a GPU booking
    ---
    tags:
      - GPU Bookings
    description: Update the details of a specific GPU booking.
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
        description: ID of the booking to be updated.
      - in: body
        name: body
        schema:
          id: GPUBookingUpdate
          properties:
            gpu_id:
              type: integer
              description: The new ID of the GPU instance to book.
            end_time:
              type: string
              format: date-time
              description: The new end time of the booking.
    responses:
      200:
        description: Booking updated successfully.
      404:
        description: Booking not found.
      400:
        description: New GPU instance not available or end time conflicts with other bookings.
    """
    booking = GPU_booking.query.get(booking_id)
    if not booking or booking.is_cancelled:
        return jsonify({'message': 'Booking not found or already cancelled'}), 404

    data = request.json
    new_gpu_id = data.get('gpu_id')
    new_end_time = data.get('end_time')

    # Check if the new GPU instance is different and available
    if new_gpu_id and new_gpu_id != booking.gpu_id:
        new_gpu_instance = GPU_instance.query.get(new_gpu_id)
        if not new_gpu_instance or new_gpu_instance.status != GPU_status.AVAILABLE:
            return jsonify({'message': 'New GPU instance not available'}), 400

    # Check if the new end time is valid and does not conflict with other bookings
    if new_end_time:
        new_end_time = datetime.strptime(new_end_time, '%Y-%m-%dT%H:%M:%S')  # Assuming ISO format
        if new_end_time > booking.end_time:
            # Check for booking conflicts
            conflicting_bookings = GPU_booking.query.filter(
                GPU_booking.gpu_id == booking.gpu_id,
                GPU_booking.booking_id != booking.booking_id,
                GPU_booking.start_time < new_end_time,
                GPU_booking.end_time > booking.start_time,
                GPU_booking.is_cancelled == False  # Exclude cancelled bookings
            ).all()
            if conflicting_bookings:
                return jsonify({'message': 'New end time conflicts with other bookings'}), 400

    # Apply updates
    if new_gpu_id:
        booking.gpu_id = new_gpu_id
    if new_end_time:
        booking.end_time = new_end_time

    db.session.commit()
    return jsonify({'message': 'Booking updated successfully!'}), 200