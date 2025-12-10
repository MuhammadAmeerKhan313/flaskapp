# config.py
from pymongo import MongoClient

def get_db():
    # Directly using your MongoDB Atlas connection URI
    uri = "mongodb+srv://Muhammad_Ameer_Khan:Ameer123%40456@edupredictcluster.txdhy5t.mongodb.net/EduPredictDB?retryWrites=true&w=majority"
    
    # Connect to MongoDB
    client = MongoClient(uri)
    
    # Select your database
    db = client.get_database("EduPredictDB")
    return db
