# This is where we will write our tests for our application

import unittest
from app import app, db
from app.models import User
import json

import pytest
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/gpu_cloud_service_test'
    # If you have set a username and password for your PostgreSQL, include them in the URI

    with app.test_client() as client:
        with app.app_context():
            # Initialize the test database
            db.create_all()
        yield client  # This is where the testing happens
        db.session.remove()
        db.drop_all()  # Clean up the database after tests

# Your test functions go here

def test_user_registration(client):
    response = client.post('/register', json={'username': 'testuser', 'email': 'test@email.com'})
    assert response.status_code == 201
    assert b'User registered successfully!' in response.data
