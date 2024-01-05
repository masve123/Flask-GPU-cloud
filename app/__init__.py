"""
The __init__.py file in a Flask application is used to initialize 
your application and bring together different components like 
database connections, blueprints, configurations, etc. 
It's essentially where your Flask app is defined and configured.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Importing blueprints
from .api.users.routes import users_blueprint
from .api.gpu_instances.routes import gpu_instances_blueprint
from .api.gpu_bookings.routes import gpu_bookings_blueprint
from .api.gpu_usage.routes import gpu_usage_blueprint
from .api.queue.routes import queue_blueprint

# Registering blueprints
app.register_blueprint(users_blueprint, url_prefix='/users')
app.register_blueprint(gpu_instances_blueprint, url_prefix='/gpu_instances')
app.register_blueprint(gpu_bookings_blueprint, url_prefix='/gpu_bookings')
app.register_blueprint(gpu_usage_blueprint, url_prefix='/gpu_usage')
app.register_blueprint(queue_blueprint, url_prefix='/queue')
