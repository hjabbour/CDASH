import os, random, string
from pymongo import MongoClient
# 2023 Haytham Jabbour hjabbour
def get_mongodb_connection():
    mongodb_url = os.environ.get('MONGODB_URL')
    if mongodb_url:
        client = MongoClient(mongodb_url)
    else:
        # Fallback to a hardcoded URL
        client = MongoClient('mongodb://root:rootpassword@10.113.108.252:27017')
        #client = MongoClient('mongodb://root:rootpassword@10.113.108.253:27017')
        #client = MongoClient('mongodb://root:password@192.168.0.214:27017')
        #client = MongoClient('mongodb://root:rootpassword@192.168.2.111:27017')

        #client = MongoClient('mongodb://root:rootpassword@10.229.166.67:27017')
        
        #client = MongoClient("mongodb://root:rootpassword@192.168.0.44:27017")
      
    return client