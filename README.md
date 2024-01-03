# GPU Cloud Service

## Overview
This project is a GPU Cloud Service, designed to allow users to book and manage GPU instances for various computational needs. It is built using Flask, a Python web framework, and utilizes SQLAlchemy for Object-Relational Mapping (ORM) and Flask-Migrate for database migrations.

### Key Features
- **User Management**: Register, update, and delete user information.
- **GPU Instance Management**: Book, view, and delete GPU instances.
- **Usage Tracking**: Keep track of GPU usage statistics.

## Technical Overview

### ORM and Database Synchronization
- **SQLAlchemy**: Used as an ORM library to map Python classes to database tables.
- **Flask-Migrate**: Manages database migrations, detecting changes in SQLAlchemy models and updating the database schema accordingly.

#### Object-Relational Mapping (ORM)
- **ORM Concept**: SQLAlchemy is an ORM library. ORM allows you to work with databases using high-level entities such as classes and objects rather than low-level database commands. It maps (or connects) these classes to database tables.
- **Class-to-Table Mapping**: In SQLAlchemy, each class that inherits from `db.Model` is automatically mapped to a table in the database. The class name typically corresponds to the table name (in a lowercase format), and the class attributes correspond to the columns in the table.

#### Flask-Migrate and Database Synchronization
- **Role of Flask-Migrate**: Flask-Migrate, which is an extension that handles SQLAlchemy database migrations for Flask applications, works by detecting changes in your SQLAlchemy models (the classes in `models.py`).
- **Creating Migrations**: When you run `flask db migrate`, Flask-Migrate, through Alembic (a database migration tool), generates migration scripts. These scripts include commands to adjust your database schema so that it matches the structure defined by your SQLAlchemy models.
- **Applying Migrations**: Running `flask db upgrade` executes these migration scripts, creating new tables and modifying existing ones as needed based on your model definitions.

#### Why Does Flask-Migrate Create a Table for Each Class?
- **Data Persistence**: Each class in `models.py` extending `db.Model` represents an entity that you want to store in the database. Flask-Migrate creates a table for each class because it assumes you'll want to store and retrieve instances of these classes as records in your database.
- **Convenience and Abstraction**: This approach abstracts away much of the complexity of database interactions. You can focus on defining your data structures in Python and let Flask-Migrate and SQLAlchemy handle the translation into SQL.

#### Example: User Class
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # ... other fields ...
```
- Flask-Migrate will create a table named user (or users, depending on naming conventions) with columns id and username.

### Flask-Migrate Commands
The following are some basic commands used in Flask-Migrate:
```bash
flask db init
flask db migrate -m "users table"
flask db upgrade
```



