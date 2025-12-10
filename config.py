# config.py
from pymongo import MongoClient

def get_db():
    """
    Connects to MongoDB Atlas and returns the database object.
    """
    uri = "mongodb+srv://Muhammad_Ameer_Khan:Ameer123%40456@edupredictcluster.txdhy5t.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client.get_database("EduPredictDB")  # Replace with your DB name
    return db
