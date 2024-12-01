from pymongo import MongoClient
def get_database():
 
   CONNECTION_STRING = "mongodb://localhost:27017/fox_db"
   
 
   client = MongoClient(CONNECTION_STRING)
 
   return client['fox_db']
  
if __name__ == "__main__":   
  
   dbname = get_database()