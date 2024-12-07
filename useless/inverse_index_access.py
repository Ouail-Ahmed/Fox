from py_mongo import get_database
from index import Index , Posting
dbname = get_database()
inverse_index= dbname["fichier inverse"]

def insert_index(index: Index):
    index_dict = index.to_dict()  

    existing_entry = inverse_index.find_one({"term": index_dict["term"]})

    if existing_entry:
        for index_post in index_dict["postings"]:
            for post in existing_entry["postings"]:
                if post["doc_name"] == index_post["doc_name"]:
                    post.update(index_post)
                    break
            else:
                existing_entry["postings"].append(index_post)
        doc_names = {post["doc_name"] for post in existing_entry["postings"]}
        doc_num = len(doc_names)
        inverse_index.update_one(
            {"term": index_dict["term"]},
            {"$set": {"doc_num": doc_num, "postings": existing_entry["postings"]}}
        )
    else:

        doc_names = {post["doc_name"] for post in index_dict["postings"]}
        index_dict["doc_num"] = len(doc_names)
        inverse_index.insert_one(index_dict)

def load_index_from_db(term: str) -> Index:
    entry = inverse_index.find_one({"term": term})
    if entry:
        postings = {
            p["doc_name"]: Posting(p["doc_name"], p["weight"], p["path"])
            for p in entry["postings"]
        }
        return Index(entry["term"], entry["doc_num"], list(postings.values())[0])
    return None

