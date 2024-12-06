import os
import fnmatch
import math
from pymongo import MongoClient, errors
from indexation import start as index_docs, read_doc, indexation as index_query



def main():
    MONGO_URI = 'mongodb://localhost:27017/'
    DATABASE_NAME = 'inverted_files'

    try:
        client= MongoClient(MONGO_URI)
        db= client[DATABASE_NAME]

        #Collection a utiliser, a changer dépendant de l'interface (somme,max ou freq)
        collection=db['fi_sum']

        # get the number of docs in the collection
        docs_path = os.path.join("assets", "collection_time")
        num_docs = len(fnmatch.filter(os.listdir(docs_path), '*.txt'))

        collocs_path = os.path.join("assets", "collocations.txt")
        stoplist_path = os.path.join("assets", "stoplist.txt")

        # get the stop list content
        stoplist = sorted(read_doc(stoplist_path).lower().split('\n'))

        # each collocation is an element in the list collocs
        collocs = sorted(read_doc(collocs_path).lower().split('\n'))

        #Query to search for, a changer dépendant de l'interface
        query= '''hey 00 cape canaveral'''

        query_tokens_freq, query_tokens_sum = index_query(collocs, query, stoplist)

        list_docs= {}

        #Parcours de chaque token de la requête
        for key in query_tokens_sum:

            #Vérification de l'existence du token dans la collection
            nbdocs= collection.count_documents({"_id": key})
            if nbdocs == 0:
                print(f"token: {key} not found")

            else:
                cursor=collection.find({"_id": key})
                for doc in cursor:
                    for field in doc:
                        #calcul de l'idf en se basant sur le nbr docs ou il apparait
                        if field == "dt":
                            print(f"key: {key} nbdocs: {doc[field]}")
                            idf= math.log10(num_docs/doc[field])
                            print(f"idf: {idf}")
                            
                        if field== "post":
                            print(f"token: {key}")
                            for key3 in doc[field]:
                                #calcul du tf-idf
                                tf= doc[field][key3]
                                tf_idf= tf*idf

                                #calcul de la pertinence de chaque doc
                                vec= tf_idf*query_tokens_sum[key]
                                print(f"doc: {key3} tf-idf: {tf_idf} vector: {vec}")
                                if key3 not in list_docs:
                                    list_docs[key3]= vec
                                else:
                                    list_docs[key3]+= vec
                                #print(f"list_docs avec pertinence: {list_docs}\n")
                        print("\n")
        client.close()

        #tri des docs par pertinence
        list_docs= sorted(list_docs, key=list_docs.get, reverse=True)
        print(list_docs)

    except errors.ConnectionFailure as e:
        print(f"Error: {e}")
        print("Connection to database failed")
        return
    except errors.PyMongoError as e:
        print(f"Error: {e}")
        print("Connection to database failed")
        return
    
if __name__ == "__main__":
    main()