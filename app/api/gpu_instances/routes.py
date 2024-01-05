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

gpu_instances_blueprint = Blueprint('gpu_instances', __name__, url_prefix='/api')

############## GPU Instance endpoint functions ##############
# Endpoint to create a new GPU instance.
@gpu_instances_blueprint.route('/gpu_instances', methods=['POST'])
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
@gpu_instances_blueprint.route('/gpu_instances', methods=['GET'])
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


# Endpoint to release a GPU instance after use.
@gpu_instances_blueprint.route('/gpu_instances/<int:gpu_instance_id>', methods=['DELETE'])
def delete_gpu_instance(gpu_instance_id):
    """
    Delete a GPU instance.
    NOTE: This is not the same as cancelling a GPU instance booking. Instead, 
    this endpoint is used to delete a new GPU instance in the database. This means
    registering a GPU instance as a physical GPU, as one GPU instance would equate to
    one physical GPU in the data center.
    ---
    tags:
      - GPU Instances
    description: Delete a specific GPU instance by its ID.
    parameters:
      - name: gpu_instance_id
        in: path
        type: integer
        required: true
        description: Unique ID of the GPU instance to delete.
    responses:
      200:
        description: GPU instance deleted successfully.
      404:
        description: GPU instance not found.
    """
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404
    db.session.delete(gpu_instance)
    db.session.commit()
    return jsonify({'message': 'GPU instance deleted successfully!'}), 200

# Edpoint to view details of a specific GPU instance.
@gpu_instances_blueprint.route('/gpu_instances/<int:gpu_instance_id>', methods=['GET'])
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
@gpu_instances_blueprint.route('/gpu_instances/<int:gpu_instance_id>', methods=['PUT'])
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
    gpu_instance.from_dict(data)
    db.session.commit()
    return jsonify({'message': 'GPU instance updated successfully!'}), 200