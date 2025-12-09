from pymongo import MongoClient
from pymongo.errors import ConfigurationError

MONGO_URI = 'mongodb://localhost:27017'

def get_db():
    try:
        client = MongoClient(MONGO_URI)
        return client['edupredict']
    except ConfigurationError as e:
        print(f"Error connecting to MongoDB: {e}")
        return None