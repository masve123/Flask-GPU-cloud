"""
This is where we set up our API endpoints
"""

from flask import request, jsonify
from app.models import User, GPU_instance
from flask import current_app as app
from app import db

from flask import Blueprint

bp = Blueprint('bp', __name__) # this is necessary to avoid circular imports


####### Create functions #######
@bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
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


####### Getter functions #######

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a user by id."""
    user = User.query.get(user_id)
    return jsonify(user.to_dict()) if user else ('', 404)

@bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users."""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

####### Update functions #######
@bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update a user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    data = request.json
    user.from_dict(data)
    db.session.commit()
    return jsonify({'message': 'User updated successfully!'}), 200


@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user based on the user id."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully!'}), 200


# List Available GPU Instances: An endpoint to fetch available GPU instances.
@bp.route('/gpu_instances', methods=['GET'])
def get_all_gpu_instances():
    """Get all GPU instances."""
    gpu_instances = GPU_instance.query.all()
    return jsonify([gpu.to_dict() for gpu in gpu_instances])

# Book a GPU Instance: An endpoint for users to book an available GPU instance.
@bp.route('/gpu_instances', methods=['POST'])
def book_gpu_instance():
    """Book a GPU instance."""
    data = request.json
    gpu_instance = GPU_instance(name=data['name'], gpu_type=data['gpu_type'], gpu_memory=data['gpu_memory'])
    db.session.add(gpu_instance)
    db.session.commit()
    return jsonify({'message': 'GPU instance booked successfully!'}), 201

# Release/Unbook GPU Instance: An endpoint to release a GPU instance after use.
@bp.route('/gpu_instances/<int:gpu_instance_id>', methods=['DELETE'])
def delete_gpu_instance(gpu_instance_id):
    """Delete a GPU instance based on the id."""
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404
    db.session.delete(gpu_instance)
    db.session.commit()
    return jsonify({'message': 'GPU instance deleted successfully!'}), 200

# View GPU Instance Details: An endpoint to view details of a specific GPU instance.
@bp.route('/gpu_instances/<int:gpu_instance_id>', methods=['GET'])
def get_gpu_instance(gpu_instance_id):
    """Get a GPU instance by id."""
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    return jsonify(gpu_instance.to_dict()) if gpu_instance else ('', 404)

# Update GPU Instance Details: An endpoint to update the details of a GPU instance.
@bp.route('/gpu_instances/<int:gpu_instance_id>', methods=['PUT'])
def update_gpu_instance(gpu_instance_id):
    """Update a specific GPU instance."""
    gpu_instance = GPU_instance.query.get(gpu_instance_id)
    if not gpu_instance:
        return jsonify({'message': 'GPU instance not found'}), 404

    data = request.json
    gpu_instance.from_dict(data)
    db.session.commit()
    return jsonify({'message': 'GPU instance updated successfully!'}), 200

