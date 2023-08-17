from pymongo import MongoClient

def get_mongodb_connection():
    #client = MongoClient('mongodb://root:password@10.229.166.36:27017')
    client = MongoClient('mongodb://root:password@192.168.2.158:27017')
    #client = MongoClient('mongodb://root:password@127.0.0.1:27017')

    return client

