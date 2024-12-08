from pymongo import MongoClient, errors
import math

# names of expected_collections
fi = {
    'f': 'fi_freq',
    's': 'fi_sum',
    'm': 'fi_max'
}

def main():
    MONGO_URI = 'mongodb://localhost:27017/'
    DATABASE_NAME = 'inverted_files'

    try:
        # connect to database in mongodb
        client = MongoClient(MONGO_URI)
        # connect / create the database
        db = client[DATABASE_NAME]

        collection = db[fi['s']]

        cursor=collection.find()

        doc_w_sum = 0


        for elem in cursor:
            idf= math.log10(423/elem["dt"])
            if "017" in elem["post"].keys():
              doc_w_sum += (idf*elem['post']['017']) ** 2

        print("doc 017 fi_sum:")
        print(f"doc_w_sum = {doc_w_sum}")

        # Close connection
        client.close()
        
    except errors.ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except errors.PyMongoError as e:
        print(f"An error occurred: {e}")

# main call
if __name__ == "__main__":
    main()
