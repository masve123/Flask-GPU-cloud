"""
This is where we set up our API endpoints for the queueing system.
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db

from flask import Blueprint

from datetime import datetime, timedelta
from sqlalchemy import func

queue_blueprint = Blueprint('queue', __name__)

############## QUEUEING SYSTEM ##############
@queue_blueprint.route('/join', methods=['POST'])
def join_gpu_queue():
    """
    Add a user to the GPU queue
    ---
    tags:
      - Queueing System
    description: Add a user to the queue for GPU resource allocation. Ensures the user exists and is not already in the queue.
    parameters:
      - in: body
        name: body
        schema:
          id: QueueJoin
          required:
            - user_id
          properties:
            user_id:
              type: integer
              description: The user ID requesting to join the GPU queue.
    responses:
      201:
        description: User added to GPU queue successfully.
      400:
        description: Invalid request (missing user ID, user does not exist, or user already in queue).
    """
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if user is already in the queue
    existing_entry = GPU_queue_entry.query.filter_by(user_id=user_id, status=GPU_queue_status.PENDING).first()
    if existing_entry:
        # Calculate the user's position in the queue
        user_position = GPU_queue_entry.query.filter(
            GPU_queue_entry.requested_at <= existing_entry.requested_at,
            GPU_queue_entry.status == GPU_queue_status.PENDING
        ).count()

        return jsonify({
            'message': 'User already in the queue',
            'queue_entry': existing_entry.to_dict(),
            'position_in_queue': user_position
        }), 200

    queue_entry = GPU_queue_entry(user_id=user_id)
    db.session.add(queue_entry)
    db.session.commit()
    return jsonify({'message': 'Added to GPU queue', 'queue_entry': queue_entry.to_dict()}), 201



@queue_blueprint.route('/status', methods=['GET'])
def check_queue_status():
    """
    Check the status of a user in the GPU queue
    ---
    tags:
      - Queueing System
    description: Check the queue status for a specific user, including their position in the queue.
    parameters:
      - name: user_id
        in: query
        type: integer
        required: true
        description: The user ID to check the queue status for.
    responses:
      200:
        description: Queue status and positions retrieved successfully.
      400:
        description: User ID is required.
      404:
        description: User not found.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    queue_entries = GPU_queue_entry.query.filter_by(user_id=user_id).order_by(GPU_queue_entry.requested_at).all()
    
    # Check if the user has any queue entries
    if not queue_entries:
        return jsonify({'message': 'User is currently not in the queue'}), 200
    
    # Add position information for each queue entry
    enhanced_entries = []
    for entry in queue_entries:
        user_position = GPU_queue_entry.query.filter(
            GPU_queue_entry.requested_at <= entry.requested_at,
            GPU_queue_entry.status == GPU_queue_status.PENDING
        ).count()
        entry_dict = entry.to_dict()
        entry_dict['position'] = user_position
        enhanced_entries.append(entry_dict)

    return jsonify(enhanced_entries)

   

@queue_blueprint.route('/cancel/<int:queue_entry_id>', methods=['POST'])
def cancel_queue_entry(queue_entry_id):
    """
    Cancel a user's queue entry
    ---
    tags:
      - Queueing System
    description: Cancel a specific user's entry in the GPU queue.
    parameters:
      - name: queue_entry_id
        in: path
        type: integer
        required: true
        description: The ID of the queue entry to cancel.
    responses:
      200:
        description: Queue entry cancelled successfully.
      400:
        description: Queue entry is already cancelled or cannot be cancelled.
      404:
        description: Queue entry not found.
    """
    queue_entry = GPU_queue_entry.query.get(queue_entry_id)
    if not queue_entry:
        return jsonify({'message': 'Queue entry not found'}), 404

    if queue_entry.status == GPU_queue_status.CANCELLED:
        return jsonify({'message': 'Queue entry is already cancelled'}), 400
    
    if queue_entry.status == GPU_queue_status.ALLOCATED:
        return jsonify({'message': 'Cannot cancel an allocated queue entry'}), 400
    
    if queue_entry.status != GPU_queue_status.PENDING:
        # This should never happen, but just in case other queue statuses are added in the future
        return jsonify({'message': 'Queue entry cannot be cancelled as it is not in a PENDING state'}), 400

    queue_entry.status = GPU_queue_status.CANCELLED
    db.session.commit()

    return jsonify({'message': 'Queue entry cancelled successfully'}), 200

@queue_blueprint.route('/', methods=['GET'])
def get_gpu_queue():
    """
    Retrieve the entire GPU queue
    ---
    tags:
      - Queueing System
    description: Get a list of all entries in the GPU queue.
    responses:
      200:
        description: List of all GPU queue entries retrieved successfully.
    """
    queue_entries = GPU_queue_entry.query.order_by(GPU_queue_entry.requested_at).all()
    return jsonify([entry.to_dict() for entry in queue_entries])

@queue_blueprint.route('/next', methods=['GET'])
def get_next_in_queue():
    """
    Get the next user in the queue
    ---
    tags:
      - Queueing System
    description: Retrieve the next user in line in the GPU queue.
    responses:
      200:
        description: Next user in the GPU queue retrieved successfully.
      404:
        description: No users in the queue.
      500:
        description: Error retrieving the next queue entry.
    """
    try:
        queue_entry = GPU_queue_entry.query.filter_by(status=GPU_queue_status.PENDING).order_by(GPU_queue_entry.requested_at).first()
        return jsonify(queue_entry.to_dict()) if queue_entry else ('', 404)
    except Exception as e:
        return jsonify({'message': 'Error retrieving the next queue entry', 'error': str(e)}), 500



@queue_blueprint.route('/move/<int:queue_entry_id>/<string:position>', methods=['POST'])
def move_queue_entry(queue_entry_id, position):
    """
    NOTE; this is an endpoint meant for admin users only.
    NOTE; This function could potentially be optimized, 
    as it currently updates the queue_order of all entries 
    in the queue when moving a specific entry. For simplicity,
    this is the approach taken for this example.
    
    Move a user in the queue to a specified position
    ---
    tags:
      - Queueing System
    description: Move a user to a specified position in the GPU queue.
    parameters:
      - name: queue_entry_id
        in: path
        type: integer
        required: true
        description: The ID of the queue entry to move.
      - name: position
        in: path
        type: string
        required: true
        enum: [front, back]
        description: The position to move the user to in the queue.
    responses:
      200:
        description: Queue entry moved successfully.
      400:
        description: Invalid position or queue entry already in the desired position.
      404:
        description: Queue entry not found.
      500:
        description: Error moving the queue entry.
    """
    queue_entry = GPU_queue_entry.query.get(queue_entry_id)
    if not queue_entry:
        return jsonify({'message': 'Queue entry not found'}), 404

    if position not in ['front', 'back']:
        return jsonify({'message': 'Invalid position'}), 400
    
    try:
        if position == 'front':
            # Increment the queue_order of all other entries
            GPU_queue_entry.query.update({GPU_queue_entry.queue_order: GPU_queue_entry.queue_order + 1})
            db.session.flush() # used to update the queue_order of all entries in the queue before setting a specific entry's queue_order

            # Move this entry to the front
            queue_entry.queue_order = 1

        elif position == 'back':
            # Find the maximum queue order and set this entry just behind it
            max_order = db.session.query(func.max(GPU_queue_entry.queue_order)).scalar() or 0
            queue_entry.queue_order = max_order + 1

        db.session.commit()
        return jsonify({'message': f'Queue entry moved to {position}', 'queue_order': queue_entry.queue_order}), 200
    except Exception as e:
        return jsonify({'message': 'Error moving queue entry', 'error': str(e)}), 500
