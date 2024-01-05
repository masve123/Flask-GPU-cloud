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

queue_blueprint = Blueprint('queue', __name__, url_prefix='/api')

############## QUEUEING SYSTEM ##############
@queue_blueprint.route('/gpu_queue/join', methods=['POST'])
def join_gpu_queue():
    """
    Add a user to the GPU queue
    ---
    tags:
      - Queueing System
    description: Add a user to the queue for GPU resource allocation.
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
        description: User ID is required.
    """
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    queue_entry = GPU_queue_entry(user_id=user_id)
    db.session.add(queue_entry)
    db.session.commit()

    return jsonify({'message': 'Added to GPU queue', 'queue_entry': queue_entry.to_dict()}), 201

@queue_blueprint.route('/gpu_queue/status', methods=['GET'])
def check_queue_status():
    """
    Check the status of a user in the GPU queue
    ---
    tags:
      - Queueing System
    description: Check the queue status for a specific user.
    parameters:
      - name: user_id
        in: query
        type: integer
        required: true
        description: The user ID to check the queue status for.
    responses:
      200:
        description: Queue status retrieved successfully.
      400:
        description: User ID is required.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    queue_entries = GPU_queue_entry.query.filter_by(user_id=user_id).order_by(GPU_queue_entry.requested_at).all()
    return jsonify([entry.to_dict() for entry in queue_entries])

@queue_blueprint.route('/gpu_queue/cancel/<int:queue_entry_id>', methods=['POST'])
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

    queue_entry.status = GPU_queue_status.CANCELLED
    db.session.commit()

    return jsonify({'message': 'Queue entry cancelled successfully'}), 200

@queue_blueprint.route('/gpu_queue', methods=['GET'])
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

@queue_blueprint.route('/gpu_queue/next', methods=['GET'])
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



@queue_blueprint.route('/gpu_queue/move/<int:queue_entry_id>/<string:position>', methods=['POST'])
def move_queue_entry(queue_entry_id, position):
    """
    Move a user in the queue to a specified position.
    NOTE; this is an endpoint meant for admin users only.
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