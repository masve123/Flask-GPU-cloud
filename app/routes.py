from flask import request, jsonify
from app.models import User
from flask import current_app as app
from app import db

from flask import Blueprint

bp = Blueprint('bp', __name__)



@bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201

@bp.route('/users', methods=['GET'])
def get_user(user_id):
    """Get a user by id."""
    return User.query.get(user_id)

@bp.route('/users', methods=['GET'])
def get_all_users():
    """Get all users."""
    return User.query.all()

@bp.route('/users', methods=['PUT'])
def update_user(user_id):
    """Update a user."""
    user = User.query.get(user_id)
    data = request.json
    user.username = data['username']
    user.email = data['email']
    db.session.commit()
    return jsonify({'message': 'User updated successfully!'}), 200