"""
This is where we set up our API endpoints for users.
"""

from flask import request, jsonify
from app.models import GPU_booking, GPU_usage, User, GPU_instance, GPU_status, GPU_queue_entry, GPU_queue_status
from flask import current_app as app
from app import db

from flask import Blueprint
from sqlalchemy import func

users_blueprint = Blueprint('users', __name__)

############## User endpoint functions ##############

@users_blueprint.route('/register', methods=['POST'])
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


@users_blueprint.route('/<int:user_id>', methods=['GET'])
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
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict()) if user else ('', 404)


@users_blueprint.route('/', methods=['GET'])
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
    if not users:
        return jsonify({'message': 'No users found.'}), 404
    return jsonify([user.to_dict() for user in users])



@users_blueprint.route('/<int:user_id>', methods=['PUT'])
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
    # Validate data here

    try:
        user.from_dict(data)
        db.session.commit()
        return jsonify({'message': 'User updated successfully!', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Update failed', 'error': str(e)}), 500





@users_blueprint.route('/<int:user_id>', methods=['DELETE'])
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

