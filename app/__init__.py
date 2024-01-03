# The __init__.py file in a Flask application is used to initialize 
# your application and bring together different components like 
# database connections, blueprints, configurations, etc. 
# It's essentially where your Flask app is defined and configured.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app.routes import bp
app.register_blueprint(bp)

