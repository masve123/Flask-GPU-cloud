"""
This is where we set up our API endpoints
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db

from flask import Blueprint

from datetime import datetime, timedelta
from . import db
from sqlalchemy import func

bp = Blueprint('bp', __name__) # this is necessary to avoid circular imports


############## User endpoint functions ##############

@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Users
    description: Register a new user with a username and email.
    parameters:
      - name: username
        in: formData
        type: string
        required: true
        description: The user's username.
      - name: email
        in: formData
        type: string
        required: true
        description: The user's email.
    responses:
      201:
        description: User registered successfully.
      400:
        description: Bad request - user already exists.
      500:
        description: Error in registration process.
    """
    data = request.json

    # Check if user already exists
    existing_user = User.query.filter(
        (User.username == data['username']) | 
        (User.email == data['email'])
    ).first()
    if existing_user:
        return jsonify({'message': 'User already exists.'}), 400

    try:
        user = User(username=data['username'], email=data['email'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed.', 'error': str(e)}), 500


@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Get a user by id
    ---
    tags:
      - Users
    description: Retrieve details of a specific user by their user ID.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: Unique ID of the user.
    responses:
      200:
        description: Details of the user.
      404:
        description: User not found.
    """
    user = User.query.get(user_id)
    return jsonify(user.to_dict()) if user else ('', 404)

@bp.route('/users', methods=['GET'])
def get_all_users():
    """
    Get all users
    ---
    tags:
      - Users
    description: Retrieve details of all users.
    responses:
      200:
        description: A list of users.
    """
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])


@bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update a user
    ---
    tags:
      - Users
    description: Update details of a specific user.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: Unique ID of the user.
      - in: body
        name: body
        schema:
          id: UserUpdate
          required:
            - username
            - email
          properties:
            username:
              type: string
              description: The user's new username.
            email:
              type: string
              description: The user's new email.
    responses:
      200:
        description: User updated successfully.
      404:
        description: User not found.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    data = request.json
    user.from_dict(data)
    db.session.commit()
    return jsonify({'message': 'User updated successfully!'}), 200


@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user
    ---
    tags:
      - Users
    description: Delete a specific user by their user ID.
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: Unique ID of the user.
    responses:
      200:
        description: User deleted successfully.
      404:
        description: User not found.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully!'}), 200



############## GPU Instance endpoint functions ##############
# Endpoint to create a new GPU instance.
@bp.route('/gpu_instances', methods=['POST'])
def create_gpu_instance():
    """Create a new GPU instance.
    Note: This is not the same as booking a GPU instance. Instead, 
    this endpoint is used to create a new GPU instance in the database. This means
    registering a GPU instance as a physical GPU, as one GPU instance would equate to
    one physical GPU in the data center."""

    data = request.json

    # Check if the GPU instance already exists
    existing_instance = GPU_instance.query.filter_by(name=data['name']).first()
    if existing_instance:
        return jsonify({'message': 'GPU instance already exists.'}), 400

    try:
        gpu_instance = GPU_instance(name=data['name'], gpu_type=data['gpu_type'], gpu_memory=data['gpu_memory'])
        db.session.add(gpu_instance)
        db.session.commit()
        return jsonify({'message': 'GPU instance created successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create GPU instance.', 'error': str(e)}), 500



# Endpoint to fetch all GPU instances.
@bp.route('/gpu_instances', methods=['GET'])
def get_all_gpu_instances():
    """Get all GPU instances."""
    gpu_instances = GPU_instance.query.all()
    return jsonify([gpu.to_dict() for gpu in gpu_instances])


# Endpoint to release a GPU instance after use.
@bp.route('/gpu_instances/<int:gpu_instance_id>', methods=['DELETE'])
def delete_gpu_instance(gpu_instance_id):
    """
    Delete a GPU instance based on the id, from the GPU instance database.

    Note; This is not just canceling or unbooking a reservation; it's removing 
    the GPU instance from your available resources. This operation should typically 
    be reserved for administrators who manage the actual hardware or virtual instances 
    in the data center.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404
    db.session.delete(gpu_instance)
    db.session.commit()
    return jsonify({'message': 'GPU instance deleted successfully!'}), 200

# Edpoint to view details of a specific GPU instance.
@bp.route('/gpu_instances/<int:gpu_instance_id>', methods=['GET'])
def get_gpu_instance(gpu_instance_id):
    """Get a GPU instance by id."""
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    return jsonify(gpu_instance.to_dict()) if gpu_instance else ('', 404)

# Endpoint to update the details of a GPU instance.
@bp.route('/gpu_instances/<int:gpu_instance_id>', methods=['PUT'])
def update_gpu_instance(gpu_instance_id):
    """Update a specific GPU instance.
    
    This endpoint will update the details of a GPU instance, such as the name,
    GPU type, GPU memory, etc.
    Note; This should be admin-only functionality.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    data = request.json
    gpu_instance.from_dict(data)
    db.session.commit()
    return jsonify({'message': 'GPU instance updated successfully!'}), 200



############## GPU Booking endpoint functions ##############

# Endpoint for users to book an available GPU instance.
@bp.route('/gpu_bookings', methods=['POST'])
def book_gpu_instance():
    """
    Functionality: This method currently books an existing GPU instance 
    and adds a record to the GPU_booking table.
    Purpose: It is intended for users to reserve an available GPU instance for their use.
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
@bp.route('/gpu_bookings/cancel/<int:booking_id>', methods=['POST'])
def cancel_gpu_booking(booking_id):
    """Cancel a GPU booking."""
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
@bp.route('/gpu_bookings', methods=['GET'])
def get_all_gpu_bookings():
    """Get all GPU bookings."""
    bookings = GPU_booking.query.all()
    return jsonify([booking.to_dict() for booking in bookings])

# Endpoint to update the details of a GPU booking.
@bp.route('/gpu_bookings/update/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    """Update a specific booking."""
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






############## GPU Usage endpoint functions ##############
@bp.route('/gpu_usage/update/<int:usage_id>', methods=['PUT'])
def update_gpu_usage(usage_id):
    """Update the usage details of a GPU instance."""
    usage = GPU_usage.query.get(usage_id)
    if not usage:
        return jsonify({'message': 'GPU usage record not found'}), 404

    data = request.json
    usage.usage_duration = data.get('usage_duration', usage.usage_duration)
    db.session.commit()
    return jsonify({'message': 'GPU usage updated successfully!'}), 200

# An endpoint to start tracking the usage of a GPU instance.
@bp.route('/gpu_usage/start', methods=['POST'])
def start_gpu_usage():
    """
    Start tracking the usage of a GPU instance.

    A tracking and a booking is not the same. This is because
    a user can book a GPU instance, but not use it. This endpoint
    is used to start tracking the actual usage of a GPU instance.
    """
    try:
        data = request.json

        # Check if GPU instance exists
        gpu_instance = GPU_instance.query.get(data['gpu_id'])
        if not gpu_instance:
            return jsonify({'message': 'GPU instance not found'}), 404

        # Check if booking exists
        booking = GPU_booking.query.get(data['booking_id'])
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404

        # Check if the booking corresponds to the GPU instance
        if booking.gpu_id != gpu_instance.id:
            return jsonify({'message': 'Booking does not match GPU instance'}), 400

        # Start tracking GPU usage
        usage = GPU_usage(
            gpu_id=gpu_instance.id,
            booking_id=booking.booking_id,
            usage_duration=0  # Initialize with zero
        )

        gpu_instance.status = GPU_status.IN_USE
        db.session.add(usage)
        db.session.commit()

        return jsonify({'message': 'GPU usage tracking started!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500




# An endpoint to stop tracking the usage of a GPU instance.
@bp.route('/gpu_usage/stop/<int:usage_id>', methods=['POST'])
def stop_gpu_usage(usage_id):
    usage = GPU_usage.query.get(usage_id)
    if not usage:
        return jsonify({'message': 'GPU usage record not found'}), 404

    # Update the usage record
    usage.end_time = datetime.utcnow()
    db.session.commit()

    # Update the GPU instance status
    gpu_instance = GPU_instance.query.get(usage.gpu_id)
    if gpu_instance:
        gpu_instance.status = GPU_status.AVAILABLE
        db.session.commit()

    return jsonify({'message': 'GPU usage tracking stopped!'}), 200

# An endpoint to get all active GPU usage records.
@bp.route('/gpu_usage/active', methods=['GET'])
def get_active_gpus():
    """Get all active GPU usage records."""
    active_usages = GPU_usage.query.filter(GPU_usage.end_time.is_(None)).all()
    return jsonify([usage.to_dict() for usage in active_usages])


# An endpoint to generate a report for a specific GPU's usage over the past 24 hours.
@bp.route('/gpu_usage/report/<int:gpu_id>', methods=['GET'])
def gpu_usage_report(gpu_id): # look at GPUtils python package for further development
    """
    Generate a report for a specific GPU's usage over the past 24 hours.
    """
    last_24_hours = datetime.utcnow() - timedelta(days=1)
    usage_records = GPU_usage.query.filter(
        GPU_usage.gpu_id == gpu_id,
        GPU_usage.start_time >= last_24_hours
    ).all()

    # Aggregating metrics
    total_usage_duration = sum([record.usage_duration for record in usage_records if record.usage_duration])
    average_utilization = sum([record.utilization_percentage for record in usage_records if record.utilization_percentage]) / len(usage_records)
    peak_memory_usage = max([record.peak_memory_usage for record in usage_records if record.peak_memory_usage], default=0)
    average_load = sum([record.average_load for record in usage_records if record.average_load]) / len(usage_records)

    # Creating the report
    report = {
        'gpu_id': gpu_id,
        'total_usage_duration_last_24_hours': total_usage_duration,
        'average_utilization_percentage': average_utilization,
        'peak_memory_usage_MB': peak_memory_usage,
        'average_load_percentage': average_load
    }

    return jsonify(report)



############## QUEUEING SYSTEM ##############
@bp.route('/gpu_queue/join', methods=['POST'])
def join_gpu_queue():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    queue_entry = GPU_queue_entry(user_id=user_id)
    db.session.add(queue_entry)
    db.session.commit()

    return jsonify({'message': 'Added to GPU queue', 'queue_entry': queue_entry.to_dict()}), 201

@bp.route('/gpu_queue/status', methods=['GET'])
def check_queue_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    queue_entries = GPU_queue_entry.query.filter_by(user_id=user_id).order_by(GPU_queue_entry.requested_at).all()
    return jsonify([entry.to_dict() for entry in queue_entries])

@bp.route('/gpu_queue/cancel/<int:queue_entry_id>', methods=['POST'])
def cancel_queue_entry(queue_entry_id):
    queue_entry = GPU_queue_entry.query.get(queue_entry_id)
    if not queue_entry:
        return jsonify({'message': 'Queue entry not found'}), 404

    if queue_entry.status == GPU_queue_status.CANCELLED:
        return jsonify({'message': 'Queue entry is already cancelled'}), 400
    
    if queue_entry.status == GPU_queue_status.ALLOCATED:
        return jsonify({'message': 'Cannot cancel an allocated queue entry'}), 400

    queue_entry.status = GPU_queue_status.CANCELLED
    db.session.commit()

    return jsonify({'message': 'Queue entry cancelled successfully'}), 200

@bp.route('/gpu_queue', methods=['GET'])
def get_gpu_queue():
    """
    Retrieve the entire GPU queue.
    """
    queue_entries = GPU_queue_entry.query.order_by(GPU_queue_entry.requested_at).all()
    return jsonify([entry.to_dict() for entry in queue_entries])

@bp.route('/gpu_queue/next', methods=['GET'])
def get_next_in_queue():
    """
    Retrieve the next user in the GPU queue.
    """
    try:
        queue_entry = GPU_queue_entry.query.filter_by(status=GPU_queue_status.PENDING).order_by(GPU_queue_entry.requested_at).first()
        return jsonify(queue_entry.to_dict()) if queue_entry else ('', 404)
    except Exception as e:
        return jsonify({'message': 'Error retrieving the next queue entry', 'error': str(e)}), 500



@bp.route('/gpu_queue/move/<int:queue_entry_id>/<string:position>', methods=['POST'])
def move_queue_entry(queue_entry_id, position):
    """
    NOTE; this is an endpoint meant for admin users only.
    Move a user in the queue to a specified position.

    :param queue_entry_id: The ID of the queue entry to move.
    :param position: The new position in the queue ('front' or 'back').
    """
    queue_entry = GPU_queue_entry.query.get(queue_entry_id)
    if not queue_entry:
        return jsonify({'message': 'Queue entry not found'}), 404

    if position not in ['front', 'back']:
        return jsonify({'message': 'Invalid position'}), 400
    
    try:
        # Logic to update queue_order based on position
        if position == 'front':
            # Set to a value lower than the current minimum
            min_order = db.session.query(func.min(GPU_queue_entry.queue_order)).scalar()
            queue_entry.queue_order = (min_order or 0) - 1
        elif position == 'back':
            # Set to a value higher than the current maximum
            max_order = db.session.query(func.max(GPU_queue_entry.queue_order)).scalar()
            queue_entry.queue_order = (max_order or 0) + 1

        db.session.commit()
        return jsonify({'message': f'Queue entry moved to {position}'}), 200
    except Exception as e:
        return jsonify({'message': 'Error moving queue entry', 'error': str(e)}), 500

