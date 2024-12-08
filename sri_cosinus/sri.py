import os, math, fnmatch
from pymongo import MongoClient, errors
from indexation import start as index_docs, read_doc, indexation as index_query

# names of expected_collections
fi = {
    'f': 'fi_freq',
    's': 'fi_sum',
    'm': 'fi_max'
}

query_tokens = {}

def main(fi_version, query, forced_indexing):
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
        collections, ignore_indexing = indexed_document_exists(db, fi_version)

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

        # indexing the query and get each index with tf normalised to the sum
        query_tokens[fi['f']], query_tokens[fi['s']], query_tokens[fi['m']] = \
                                                            index_query(collocs, query, stoplist)

        list_docs = search(db, fi_version, query_tokens[fi_version])

        # Close connection
        client.close()

        return list_docs
        
    except errors.ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except errors.PyMongoError as e:
        print(f"An error occurred: {e}")
    
def indexed_document_exists(db, expected_document):
    # Retrieve the list of collections
    collections = db.list_collection_names()
        
    return collections, (True if expected_document in db.list_collection_names() else False)

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

def search(db, collection_name, query):

    collection = db[collection_name]
    
    list_docs = {}
    doc_w_sum = {}
    query_w_sum = 0

    # get the number of docs in the collection
    docs_path = os.path.join("assets", "collection_time")
    num_docs = len(fnmatch.filter(os.listdir(docs_path), '*.txt'))

    #Vérification de l'existence du token dans la collection
    # nbdocs = collection.count_documents({"_id": key})
    # if nbdocs == 0:
    #     print(f"token: {key} not found")

    # else:
    # get the documents that have at least one token in the query
    # a set is unique
    docs_pert = set()
    for key in query:
        # sum of weights of tokens in query
        query_w_sum += query[key] ** 2

        # get the tokens that are in the query and add the docs that they exist in into the set
        cursor=collection.find({"_id": key})
        for elem in cursor:
            docs_pert.update(elem["post"].keys())

    # get all the tokens
    cursor=collection.find()
    for elem in cursor:
        # if the token exists in one of the pertinent docs
        common = set(docs_pert).intersection(elem["post"].keys())

        if common:
            #calcul de l'idf en se basant sur le nbr docs ou il apparait
            idf= math.log10(num_docs/elem["dt"])
            
            # get only the pertinent docs that token exists in
            for doc in common:
                #calcul du tf-idf
                tf= elem["post"][doc]
                tf_idf= tf*idf

                if doc not in doc_w_sum:
                    doc_w_sum[doc] = tf_idf ** 2
                else:
                    doc_w_sum[doc] += tf_idf ** 2
                
                if elem["_id"] in query:
                    #calcul de la pertinence de chaque doc 
                    vec= tf_idf * query[elem["_id"]]
                    
                    if doc not in list_docs:
                        list_docs[doc]= vec
                    else:
                        list_docs[doc]+= vec


    # produit scalaire
    sorted_docs = sorted(list_docs.keys())
    for doc in sorted_docs:
        print(f"{doc}: {list_docs[doc]}")
    
    # count cosinus
    for doc in sorted_docs:
        w_sum = doc_w_sum[doc]
        divisor_doc = math.sqrt(doc_w_sum[doc])
        divisor_query = math.sqrt(query_w_sum)
        divisor = math.sqrt(doc_w_sum[doc]) * math.sqrt(query_w_sum)
        list_docs[doc] = list_docs[doc] / divisor

    #tri des docs par pertinence
    # for doc in sorted_docs:
    #     print(f"{doc}: {list_docs[doc]}")
    list_docs = sorted(list_docs, key=list_docs.get, reverse=True)
    # print(list_docs)
    return list_docs

# main call
if __name__ == "__main__":
    # example of a query
    query = "de"
    main(fi['s'], query, False)
