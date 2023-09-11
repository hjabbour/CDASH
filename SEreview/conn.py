import os, random, string
from pymongo import MongoClient
# 2023 Haytham Jabbour hjabbour
def get_mongodb_connection():
    mongodb_url = os.environ.get('MONGODB_URL')
    if mongodb_url:
        client = MongoClient(mongodb_url)
    else:
        # Fallback to a hardcoded URL
        #client = MongoClient('mongodb://root:password@10.229.166.36:27017')
        #client = MongoClient('mongodb://root:password@192.168.2.114:27017')
        client = MongoClient('mongodb://root:password@10.229.166.167:27017')
        
        #client = MongoClient('mongodb://root:password@127.0.0.1:27017')
        
    return client