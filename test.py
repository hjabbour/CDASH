from pymongo import MongoClient

# Set up the MongoDB connection
client = MongoClient('mongodb://root:rootpassword@192.168.2.190:27017')
db = client['CDASH']
collection = db['csvdash']

# Test the connection
try:
    # Attempt to retrieve the first document from the collection
    document = collection.find_one()
    if document:
        print("Connection to MongoDB successful!")
    else:
        print("Connection successful, but the collection is empty.")
except Exception as e:
    print("Error connecting to MongoDB:", str(e))

