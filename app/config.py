import os

class Config(object):
    # SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/gpu_cloud_service'

    username = os.getenv('RDS_USERNAME', 'default_username')
    password = os.getenv('RDS_PASSWORD', 'default_password')
    endpoint = os.getenv('RDS_ENDPOINT', 'default_endpoint')
    port = os.getenv('RDS_PORT', '5432')  # Default PostgreSQL port is 5432
    dbname = os.getenv('RDS_DB_NAME', 'flask-database-1')

    SQLALCHEMY_DATABASE_URI = f'postgresql://{username}:{password}@{endpoint}:{port}/{dbname}'


# kan sette opp passord ved å kjøre følgende i terminalen:
# $ psql
    # \password your_username
    # \q

# Remember, if you're using a username and password for your database, 
#you'll need to include them in your SQLALCHEMY_DATABASE_URI in 
# the config.py file. For now, as you're in the development phase, 
# it's fine to have them there, but consider moving to environment 
# variables for production.