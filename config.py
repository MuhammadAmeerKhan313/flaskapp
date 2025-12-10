from pymongo import MongoClient

def get_db():
    uri = "mongodb+srv://Muhammad_Ameer_Khan:Ameer123%40456@edupredictcluster.txdhy5t.mongodb.net/EduPredictDB?retryWrites=true&w=majority"
    client = MongoClient(uri)
    db = client.get_database("EduPredictCluster")
    return db
