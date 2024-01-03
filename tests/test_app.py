"""
This is where we will write our tests for our application
"""

import unittest
from app import app, db
from app.models import User
import json

import pytest
from app import app, db

@pytest.fixture
def client():
    """
    A pytest fixture that provides a test client for the Flask application.

    This fixture sets up the Flask application for testing, ensuring that tests
    are run in an environment that mimics the actual application context but
    uses a separate test database. It initializes the database before each test
    and removes all data and drops the tables after each test to ensure a clean state.

    Yields:
        FlaskClient: A test client for your Flask application. This client can be used
        to make requests to the application's routes and check the responses.

    Usage:
        Use the `client` fixture in test functions to make requests to the Flask application.
        Example:
            def test_example(client):
                response = client.get('/some-route')
                assert response.status_code == 200
    """    
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
