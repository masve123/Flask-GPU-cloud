"""
This is where we set up our API endpoints for the gpu bookings.
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db

from flask import Blueprint

from datetime import datetime, timedelta
from sqlalchemy import func

gpu_bookings_blueprint = Blueprint('gpu_bookings', __name__, url_prefix='/api')



############## GPU Booking endpoint functions ##############

# Endpoint for users to book an available GPU instance.
@gpu_bookings_blueprint.route('/gpu_bookings', methods=['POST'])
def book_gpu_instance():
    """
    Book an available GPU instance
    ---
    tags:
      - GPU Bookings
    description: Book an existing GPU instance.
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
        description: GPU instance not available or not found.
      500:
        description: Error in booking process.
    """
    data = request.json
    gpu_instance = GPU_instance.query.get(data['gpu_id'])

    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    if gpu_instance.status != GPU_status.AVAILABLE:
        return jsonify({'message': 'GPU instance not available'}), 400

    booking = GPU_booking(
        user_id=data['user_id'],
        gpu_id=gpu_instance.id,
        start_time=data.get('start_time', datetime.utcnow()),
        end_time=data.get('end_time')
    )
    db.session.add(booking)
    gpu_instance.status = GPU_status.BOOKED  # Update the GPU instance status
    db.session.commit()
    return jsonify({'message': 'GPU instance booked successfully!'}), 201


# Endpoint for users to cancel a GPU instance booking.
@gpu_bookings_blueprint.route('/gpu_bookings/cancel/<int:booking_id>', methods=['POST'])
def cancel_gpu_booking(booking_id):
    """
    Cancel a GPU booking
    ---
    tags:
      - GPU Bookings
    description: Cancel an existing GPU booking.
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
        description: ID of the booking to cancel.
    responses:
      200:
        description: GPU booking cancelled successfully.
      404:
        description: Booking not found.
      400:
        description: Booking already cancelled or not cancellable.
    """
    booking = GPU_booking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

    gpu_instance = GPU_instance.query.get(booking.gpu_id)
    if gpu_instance:
        gpu_instance.status = GPU_status.AVAILABLE

    db.session.delete(booking)
    db.session.commit()
    return jsonify({'message': 'GPU booking cancelled successfully'}), 200


# Endpoint to list all GPU bookings.
@gpu_bookings_blueprint.route('/gpu_bookings', methods=['GET'])
def get_all_gpu_bookings():
    """
    List all GPU bookings
    ---
    tags:
      - GPU Bookings
    description: Retrieve a list of all GPU bookings.
    responses:
      200:
        description: A list of all GPU bookings.
    """
    bookings = GPU_booking.query.all()
    return jsonify([booking.to_dict() for booking in bookings])

# Endpoint to update the details of a GPU booking.
@gpu_bookings_blueprint.route('/gpu_bookings/update/<int:booking_id>', methods=['PUT'])
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
    if not booking:
        return jsonify({'message': 'Booking not found'}), 404

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
                GPU_booking.end_time > booking.start_time
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