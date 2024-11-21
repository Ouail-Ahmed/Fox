import json
import re
from collections import defaultdict

class CollocationManager:
    def __init__(self, file_path=None, json_file='collocations.json'):
        self.collocations = defaultdict(list)
        self.json_file = json_file
        
        try:
            self.load_collocations()
        except FileNotFoundError:
            if file_path:
                self.load_from_text(file_path)
    
    def clean_word(self, word):
        return re.sub(r'[^\w\-]', '', word).lower()

    def load_from_text(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                words = [self.clean_word(word) for word in line.strip().split() if self.clean_word(word)]
                self.collocations[words[0]].append(words[1:])
        self.save_collocations()
    
    def save_collocations(self):

        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.collocations), f, indent=2, ensure_ascii=False)
        print(f"Collocations saved to {self.json_file}")
    
    def load_collocations(self):

        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.collocations = defaultdict(list, json.load(f))
        print(f"Collocations loaded from {self.json_file}")
    
    def add_collocation(self, index, rest):
        self.collocations[index].append(rest)
        self.save_collocations()

    def remove_collocation(self, index, rest=None):
        if rest is None:
            if index in self.collocations:
             del self.collocations[index]
        else:
            if index in self.collocations:
                for col in self.collocations[index]:
                    print(f"coll {col}")
                self.collocations[index] = [
                col for col in self.collocations[index] if rest not in col
                ]
                if not self.collocations[index]:
                    del self.collocations[index]
        
        self.save_collocations()
    
    def get_collocations(self, word):
        return self.collocations.get(word)
    
    def __len__(self):
        return len(self.collocations)
    
    def all_words(self):
        return list(self.collocations.keys())

def main():
    manager = CollocationManager('Collocs.txt')
    
    
    print(len(manager))
    
if __name__ == '__main__':
    main()