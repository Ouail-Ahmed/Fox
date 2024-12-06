import os
from pymongo import MongoClient, errors
from indexation import start as index_docs, read_doc, indexation as index_query

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

        # assets paths
        collocs_path = os.path.join("assets", "collocations.txt")
        stoplist_path = os.path.join("assets", "stoplist.txt")

        # get the stop list content
        stoplist = sorted(read_doc(stoplist_path).lower().split('\n'))

        # each collocation is an element in the list collocs
        collocs = sorted(read_doc(collocs_path).lower().split('\n'))

        # if the collections does exist ignore_indexing = True
        collections, ignore_indexing = indexed_documents_exists(db)

        # if you want to force indexing again make it True
        forced_indexing = True 

        if not ignore_indexing or forced_indexing:
            # Drop each collection individually
            for collection in collections:
                db[collection].drop()
                print(f"old collection {collection} was deleted")

            # indexation conceptual - return value fichier inverse
            fi_freq, fi_sum, fi_max = index_docs(collocs, stoplist)

            add_fi_to_database(db, fi['f'], fi_freq)

            add_fi_to_database(db, fi['s'], fi_sum)

            add_fi_to_database(db, fi['m'], fi_max) 

        # example of a query
        query = '''"hey"american federation of labor, american federation 
        of labor and congress of industrial organizations. a  man'''

        # indexing the query and get each index with tf normalised to the sum
        query_tokens_freq, query_tokens_sum = index_query(collocs, query, stoplist)

        print(f"\tfreq:\n{query_tokens_freq}\n\tsum:\n{query_tokens_sum}")

        # Close connection
        client.close()   
        
    except errors.ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except errors.PyMongoError as e:
        print(f"An error occurred: {e}")
    
def indexed_documents_exists(db):
    # Retrieve the list of collections
    collections = db.list_collection_names()

    # Expected collection names
    expected_collections = set()

    for _, name in fi.items():
        expected_collections.add(name)
        
    return collections, (True if len(collections) == len(fi) and expected_collections.issubset(collections) else False)

def add_fi_to_database(db, collection_name, fi):
    collection = db[collection_name]

    # Insert the tokens into the collection
    # Loop through each token and insert it into the collection
    for token, posting in fi.items():
        document = {
            '_id': token,
            'dt': len(posting),
            'post': posting
        }
        collection.insert_one(document)

    print(f"Data inserted into database under '{collection_name}' collection.")

# main call
if __name__ == "__main__":
    main()
