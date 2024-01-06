"""
This is where we set up our API endpoints for the gpu instances.
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db

from flask import Blueprint

from datetime import datetime, timedelta
from sqlalchemy import func

gpu_instances_blueprint = Blueprint('gpu_instances', __name__)

############## GPU Instance endpoint functions ##############
# Endpoint to create a new GPU instance.
@gpu_instances_blueprint.route('/', methods=['POST'])
def create_gpu_instance():
    """
    Create a new GPU instance.
    NOTE: This is not the same as booking a GPU instance. Instead, 
    this endpoint is used to create a new GPU instance in the database. This means
    registering a GPU instance as a physical GPU, as one GPU instance would equate to
    one physical GPU in the data center.
    ---
    tags:
      - GPU Instances
    description: Register a new GPU instance in the database.
    parameters:
      - in: body
        name: body
        schema:
          id: GPUInstanceCreation
          required:
            - name
            - gpu_type
            - gpu_memory
          properties:
            name:
              type: string
              description: The name of the GPU instance.
            gpu_type:
              type: string
              description: The type of GPU.
            gpu_memory:
              type: integer
              description: The memory of the GPU in MB.
    responses:
      201:
        description: GPU instance created successfully.
      400:
        description: GPU instance already exists.
      500:
        description: Failed to create GPU instance.
    """

    data = request.json

    # Validate request data
    if not data or 'name' not in data or 'gpu_type' not in data or 'gpu_memory' not in data:
        return jsonify({'message': 'Missing or invalid data.'}), 400

    # Check if the data types are correct
    if not isinstance(data['name'], str) or not isinstance(data['gpu_type'], str) or not isinstance(data['gpu_memory'], int):
        return jsonify({'message': 'Invalid data format. Name and GPU type should be strings, and GPU memory should be an integer.'}), 400

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
@gpu_instances_blueprint.route('/', methods=['GET'])
def get_all_gpu_instances():
    """
    Get all GPU instances
    ---
    tags:
      - GPU Instances
    description: Retrieve a list of all GPU instances.
    responses:
      200:
        description: A list of GPU instances.
    """
    gpu_instances = GPU_instance.query.all()
    return jsonify([gpu.to_dict() for gpu in gpu_instances])


@gpu_instances_blueprint.route('/<int:gpu_instance_id>', methods=['DELETE'])
def delete_gpu_instance(gpu_instance_id):
    """
    Delete a specific GPU instance along with its related bookings.
    
    This function first retrieves the specified GPU instance by its ID.
    If the instance exists, it proceeds to check for any related GPU bookings.
    These bookings are then either deleted or handled according to specific logic 
    (e.g., reassigned to another instance). After handling related bookings, 
    the GPU instance itself is deleted.
    ---
    tags:
      - GPU Instances
    description: Delete a specific GPU instance and handle its related bookings.
    parameters:
      - name: gpu_instance_id
        in: path
        type: integer
        required: true
        description: Unique ID of the GPU instance to delete.
    responses:
      200:
        description: GPU instance and related bookings deleted successfully.
      404:
        description: GPU instance not found.
      500:
        description: Error occurred during deletion.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    # Handling related GPU bookings
    related_bookings = GPU_booking.query.filter_by(gpu_id=gpu_instance_id).all()
    for booking in related_bookings:
        # Option 1: Delete the booking
        db.session.delete(booking)
        # Option 2: Reassign or handle the booking differently
        # e.g., booking.gpu_id = new_gpu_id

    db.session.delete(gpu_instance)
    try:
        db.session.commit()
        return jsonify({'message': 'GPU instance deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error deleting GPU instance', 'error': str(e)}), 500


# Endpoint to view details of a specific GPU instance.
@gpu_instances_blueprint.route('/<int:gpu_instance_id>', methods=['GET'])
def get_gpu_instance(gpu_instance_id):
    """
    Get a GPU instance by ID
    ---
    tags:
      - GPU Instances
    description: Retrieve details of a specific GPU instance by its ID.
    parameters:
      - name: gpu_instance_id
        in: path
        type: integer
        required: true
        description: Unique ID of the GPU instance.
    responses:
      200:
        description: Details of the GPU instance.
      404:
        description: GPU instance not found.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    return jsonify(gpu_instance.to_dict()) if gpu_instance else ('', 404)

# Endpoint to update the details of a GPU instance.
@gpu_instances_blueprint.route('/<int:gpu_instance_id>', methods=['PUT'])
def update_gpu_instance(gpu_instance_id):
    """
    Update a specific GPU instance.
    
    This endpoint will update the details of a GPU instance, such as the name,
    GPU type, GPU memory, etc.
    NOTE; This should be admin-only functionality.
    ---
    tags:
      - GPU Instances
    description: Update details of a specific GPU instance.
    parameters:
      - name: gpu_instance_id
        in: path
        type: integer
        required: true
        description: Unique ID of the GPU instance to update.
      - in: body
        name: body
        schema:
          id: GPUInstanceUpdate
          required:
            - name
            - gpu_type
            - gpu_memory
          properties:
            name:
              type: string
              description: The new name of the GPU instance.
            gpu_type:
              type: string
              description: The new type of GPU.
            gpu_memory:
              type: integer
              description: The new memory of the GPU in MB.
    responses:
      200:
        description: GPU instance updated successfully.
      404:
        description: GPU instance not found.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    data = request.json

    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # Validate request data
    if 'name' not in data or 'gpu_type' not in data or 'gpu_memory' not in data:
        return jsonify({'message': 'Missing required data.'}), 400

    # Check if the data types are correct
    if not isinstance(data['name'], str) or not isinstance(data['gpu_type'], str) or not isinstance(data['gpu_memory'], int):
        return jsonify({'message': 'Invalid data format. Name and GPU type should be strings, and GPU memory should be an integer.'}), 400
    
    try:
        gpu_instance.from_dict(data)
        db.session.commit()
        return jsonify({'message': 'GPU instance updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating GPU instance', 'error': str(e)}), 500
    



# Endpoint to get the status of a specific GPU instance.
@gpu_instances_blueprint.route('/status/<int:gpu_instance_id>', methods=['GET'])
def get_gpu_instance_status(gpu_instance_id):
    """
    Get the status of a specific GPU instance along with additional details.
    ---
    tags:
      - GPU Instances
    description: Retrieve the status and relevant details of a specific GPU instance by its ID.
    parameters:
      - name: gpu_instance_id
        in: path
        type: integer
        required: true
        description: Unique ID of the GPU instance.
    responses:
      200:
        description: Status and details of the GPU instance.
      404:
        description: GPU instance not found.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    # Convert the status enum to a string
    status_str = gpu_instance.status.name if gpu_instance.status else None

    response_data = {
        'gpu_instance_id': gpu_instance_id,
        'gpu_instance_name': gpu_instance.name,
        'status': status_str
    }

    # If the GPU is booked, include the booking ID
    if gpu_instance.status == GPU_status.BOOKED:
        booking = GPU_booking.query.filter_by(gpu_id=gpu_instance_id, is_cancelled=False).first()
        if booking:
            response_data['booking_id'] = booking.booking_id

    return jsonify(response_data), 200
