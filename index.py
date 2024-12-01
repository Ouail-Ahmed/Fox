from typing import Dict, List

class Posting:
    def __init__(self, doc_name: str, weight: float, path: str):
        if not isinstance(doc_name, str):
            raise TypeError("doc_name must be a string.")
        if not isinstance(weight, (float, int)):  
            raise TypeError("weight must be a float.")
        if not isinstance(path, str):
            raise TypeError("path must be a string.")
        
        self.doc_name = doc_name
        self.weight = float(weight)  
        self.path = path

    def to_dict(self) -> Dict[str, str | float]:
        return {
            "doc_name": self.doc_name,
            "weight": self.weight,
            "path": self.path
        }


class Index:
    def __init__(self, term: str, doc_num: int, posting: Posting):
        if not isinstance(term, str):
            raise TypeError("term must be a string.")
        if not isinstance(doc_num, int):
            raise TypeError("doc_num must be an integer.")
        if not isinstance(posting, Posting):
            raise TypeError("posting must be a Posting object.")
        
        self.term = term
        self.doc_num = doc_num
        self.postings: Dict[str, Posting] = {posting.doc_name: posting}

    def add_posting(self, doc_name: str, weight: float = None, path: str = None):
        if isinstance(doc_name, Posting):
            self.postings[doc_name.doc_name] = doc_name
            return
        if not isinstance(doc_name, str):
            raise TypeError("doc_name must be a string.")
        if not isinstance(weight, (float, int)):
            raise TypeError("weight must be a float.")
        if not isinstance(path, str):
            raise TypeError("path must be a string.")
        
        self.postings[doc_name] = Posting(doc_name, weight, path)

    def to_dict(self) -> Dict[str, str | int | List[Dict[str, str | float]]]:
        return {
            "term": self.term,
            "doc_num": self.doc_num,
            "postings": [posting.to_dict() for posting in self.postings.values()]
        }
