from app import app  # Import the existing 'app' object
from flasgger import Swagger

swagger = Swagger(app) # For API documentation

if __name__ == "__main__":
    app.run(debug=True)  # 'debug=True' is useful for development, not production
