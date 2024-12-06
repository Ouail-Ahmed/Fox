from pathlib import Path
import os
from nltk import word_tokenize 
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
from colloc_jsonify import CollocationManager 
from index import Index , Posting
import inverse_index_access
import json
import re
import math
folder = Path( os.path.join("time_test") )
lemmatizer = WordNetLemmatizer()

def custom_tokenizer(text):
    # quoted_phrases = re.findall(r'"([^"]+)"', text)
    # for i, phrase in enumerate(quoted_phrases):
    #     placeholder = f"__QUOTE{i}__"
    #     text = text.replace(f'"{phrase}"', placeholder)
    tokens = word_tokenize(text)
    
    # for i, phrase in enumerate(quoted_phrases):
        # cleaned_phrase = phrase.replace('.', '').replace(',', '')  
        # if cleaned_phrase.startswith(" "):
        #     cleaned_phrase = cleaned_phrase[1:]
        # if cleaned_phrase.endswith(" "):
        #     cleaned_phrase = cleaned_phrase[:-1]
        # tokens = [f'{cleaned_phrase}' if token == f"__QUOTE{i}__" else token for token in tokens]
    
    return tokens


def get_files(folder_path: Path) -> list[Path]:
    return [file for file in folder_path.rglob("*.txt") if file.is_file()]

def get_lemmas(pos_tokens: list[tuple[str, str]]) -> list[str]:
    lemms = []
    for token, pos in pos_tokens:
        if pos == "NOUN":
            lemms.append(lemmatizer.lemmatize(token, pos="n"))
        elif pos == "VERB":
            lemms.append(lemmatizer.lemmatize(token, pos="v"))
        elif pos == "ADJ":
            lemms.append(lemmatizer.lemmatize(token, pos="a"))
        elif pos == "NUM":
            lemms.append(lemmatizer.lemmatize(token, pos="n"))
    return lemms

path = folder
files_paths = get_files(folder)

def save_to_json(path, f, lemms, file_name):
    output_folder =Path( path / "output")
    output_folder.mkdir(exist_ok=True)
    filename = output_folder / f"{f.stem}_{file_name}.json"
    index = {f.stem: lemms, "path": str(f)}
    with open(filename, 'w') as json_file:
        json.dump(index, json_file)

def remove_stop_words(lemms: list[str]) -> list[str]:
    with open("StopList.txt", "r") as file:
        stop_words = [line.strip() for line in file if line.strip()]  
    filtered_lemms = []
    for lem in lemms:
        for stop in stop_words:
            if "_" in stop:
                i = stop.count("_")
                word_form = "_".join(lemms[lemms.index(lem):lemms.index(lem) + i + 1])
                if word_form in stop_words:
                    break
            if lem == stop:
                break
        else:
            filtered_lemms.append(lem)
    return filtered_lemms


def all_words_in_string(source: str, target: str) -> bool:
    source_words = source.split() 
    target_words = target.split() 
    
    for word in target_words:
        if word not in source_words:
            return False
    return True




def get_collocations(tokens: list[str]) -> list[str]:
    collocations = []
    collocs = CollocationManager()
    i = 0  

    while i < len(tokens):
        word_has_colloc = False 
        word = tokens[i]
        word = word.replace("'s", " s").replace("n't", " not").replace("'re", " are").replace("'ve", " have").replace("'ll", " will").replace("'d", " would").replace("'m", " am").replace("'em", " them").replace("'all", " all").replace("."," ").replace(","," ").replace("("," ").replace(")"," ").replace("["," ").replace("]"," ").replace("{"," ").replace("}"," ").replace(":"," ").replace(";"," ").replace("!"," ").replace("?"," ").replace("-"," ").replace("  "," ")
        if word == " ":
            i += 1
            continue
        candidates = collocs.get_collocations(word)  
        if candidates:
            longest_colloc = max(candidates, key=len)
            length = len(longest_colloc)

            for candidate in candidates:
                if all_words_in_string (" ".join(tokens[i :i + length]) , candidate):
                    collocations.append( word+" "+candidate) 
                    i += 1  
                    word_has_colloc = True
                    continue  
        if not word_has_colloc:
            collocations.append(word)
            i += 1

    return collocations

def count_tf (tokens: list[str]) -> list[tuple[str, int]]:
    token_counts = {}
    for token in tokens:
        if token in token_counts:
            token_counts[token] += 1
        else:
            token_counts[token] = 1


for f in files_paths:
    index = []
    with open( f, "r") as file:
        text = file.read()
        text = text.lower()
        tokens = word_tokenize(text)
        tokens = get_collocations(tokens)
        pos_tokens = pos_tag(tokens, tagset="universal")
        lemms = get_lemmas(pos_tokens) 
        lemms = remove_stop_words(lemms)
        indexer = []
        token_counts = {}
        for token in lemms:
            if token in token_counts:
                token_counts[token] += 1
            else:
                token_counts[token] = 1

        indexer = [(token, float(count))  for token , count in token_counts.items()]
        save_to_json(path, f, indexer, "tf")
        for keyword, weight in indexer:
            p = Posting(f.stem , weight , str(f))
            ind = Index( keyword,int(f.stem) , p)
            inverse_index_access.insert_index(ind)

# for f in files_paths:
#     indexer = []
#     with open(path/"output" / f"{f.stem}_lemmes.json", "r") as file:
#         tokens = json.load(file)[f.stem]
#         token_counts = {}
#         for token in tokens:
#             if token in token_counts:
#                 token_counts[token] += 1
#             else:
#                 token_counts[token] = 1

#         freq_max = max(token_counts.values())
#         indexer = [(token, round(count / freq_max, 4)) for token, count in token_counts.items()]

# for f in files_paths:
#     indexer = []
#     with open(path /"output" / f"{f.stem}_tf.json", "r") as file:
#         tokens = json.load(file)[f.stem]
#         for token in tokens:
#             count = 0 
#             for f2 in files_paths:
#                 with open(path/"output" / f"{f2.stem}_tf.json", "r") as file2:
#                     tokens2 = json.load(file2)[f2.stem]
#                     if token[0] in [t[0] for t in tokens2]:
#                         count += 1
#             tok, c = token
#             tf_idf_value = round(c * math.log10(len(files_paths) / count), 4)
#             # if tf_idf_value != 0:
#                 # indexer.append((tok, tf_idf_value))
#             indexer.append((tok, tf_idf_value))
#         save_to_json(path, f, indexer, "tf_idf1")

# for f in files_paths:
#     with open(path / "output" / f"{f.stem}_tf_idf1.json", "r") as file:
#         data = json.load(file)
#         index = data[f.stem]
#         keywords_and_weights = index  # List of keywords and weights
#         file_path = Path(data["path"])  # Path
#         for keyword, weight in keywords_and_weights:
#             p = Posting(file_path.stem , weight , str(file_path))
#             ind = Index( keyword,int(file_path.stem) , p)
#             inverse_index_access.insert_index(ind)
#can't cannot ca not
                