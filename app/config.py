class Config(object):    
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/gpu_cloud_service'
# kan sette opp passord ved å kjøre følgende i terminalen:
# $ psql
    # \password your_username
    # \q

# Remember, if you're using a username and password for your database, 
#you'll need to include them in your SQLALCHEMY_DATABASE_URI in 
# the config.py file. For now, as you're in the development phase, 
# it's fine to have them there, but consider moving to environment 
# variables for production.