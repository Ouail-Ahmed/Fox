import re
import math
import os

# docs path
docs_path = os.path.join("assets", "collection_time")

longest_colloc_length = 0

num_docs = 0

# for fichier inverse tf normalised by sum
sum_freq_docs = {}

# elimate punctuation
CLEAN_RE = re.compile(r'[^a-zA-Z0-9\-\s]')

def main(collocs, stoplist):

    length_of_longest_colloc(collocs)
    tokens = {}

    docs_list = sorted(os.listdir(docs_path))

    global num_docs
    num_docs = len(docs_list)

    for doc_name in docs_list:
        tokens = indexation(collocs, doc_name , stoplist, tokens)

    # get the idfs of tokens
    idfs = get_idfs(tokens)

    # for fichier inverse tf normalised by max
    max_freq_docs = get_docs_max_freq(tokens)

    # Sort tokens alphabetically
    sorted_tokens = sorted(tokens.keys())

    # fichier inverse (weight is tf*idf where tf = freq)
    fi_freq = fichier_inverse_freq(sorted_tokens, tokens, idfs)

    # fichier inverse (weight is tf*idf where tf is normalised by the sum)
    fi_sum = fichier_inverse_sum(sorted_tokens, tokens, idfs)

    # fichier inverse (weight is tf*idf where tf is normalised by the max)
    fi_max = fichier_inverse_max(sorted_tokens, tokens, idfs, max_freq_docs)

    ##### prints ######
    verbose = False
    if verbose:
        #print the max of frequencies of each doc
        print(" docs max freq:")
        for doc_id, freq in max_freq_docs.items():
            print(f"{doc_id}.txt -> {freq}")

        # print the sum of frequencies of each doc
        print(" docs freq:")
        for doc_id, freq in sum_freq_docs.items():
            print(f"{doc_id} -> {freq}")

        print("\n idfs:")
        for token, idf in idfs.items():
            print(f"{token} -> {idf}")

        print("\n fi weight = freq")
        print("\n\n")
        for key in tokens.keys():
            print(f"{key}:\t\t\t\t\t{tokens[key]}\n")

        print("\n fi weight = freq*idf")
        print("\n\n")
        for key in fi_freq.keys():
            print(f"{key}:\t\t\t\t\t{fi_freq[key]}\n")

        print("\n fi weight = tf*idf where tf normalised by the sum")
        print("\n\n")
        for key in fi_sum.keys():
            print(f"{key}:\t\t\t\t\t{fi_sum[key]}\n")

        print("\n fi weight = tf*idf where tf normalised by the max")
        print("\n\n")
        for key in fi_max.keys():
            print(f"{key}:\t\t\t\t\t{fi_max[key]}\n")

    return idfs, fi_freq, fi_sum, fi_max


# return the content of a file
def read_doc(doc_path):
    try:
        with open(doc_path, 'r') as file:
            content = file.read()
        return content
    
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error: {e}"
    
# get the length of the longest colloc
def length_of_longest_colloc(collocs):

    global longest_colloc_length

    for line in collocs:
        words = line.strip().split()
        word_count = len(words)

        if longest_colloc_length < word_count:
            longest_colloc_length = word_count

# recognize all collocations of a document
def colloc_rec(collocs, target):
    low, high = 0, len(collocs) - 1
    ret = False
    
    while low <= high:
        mid = (low + high) // 2
        if collocs[mid].startswith(target):
            # full colloc recognized
            if len(target) == len(collocs[mid]):
                return True, True
            '''zher te7t fhad lcas:
            target = american federation of labor
            collocs[mid] = american federation of labor and congress of industrial organizations
            which means the condition collocs[mid].startswith(target) is met
            but len is not the same, so I was returning True, False 
            without searching more if the sub colloc li hia target really doesn't exist fla list'''
            ret = True
        
        # target after the current colloc
        if collocs[mid] < target:
            low = mid + 1
        # target before current colloc
        else:
            high = mid - 1

    if (ret):
        return True, False
    # target not found
    return False, False

# recognize all quotes as a collocation
def quotes_rec(doc_content):
    # eliminate ponctuation
    CLEAN_RE = re.compile(r'[^a-zA-Z0-9\-\s]')
    divide = doc_content.split('"')
    
    # dict represents recognized quotes
    quotes = {}
    doc_content = ""
    # the quotes will always be in impair position
    for i in range(len(divide)):
        # add the quotes to the dict with value 0.0 to handle duplicates
        if(i % 2 != 0):
            quote = CLEAN_RE.sub('', divide[i]).strip()
            quotes[quote] = 0.0

    for i in range(len(divide)):
        # if quote increase the frequence
        if(i % 2 != 0):
            quote = CLEAN_RE.sub('', divide[i]).strip()
            quotes[quote] += 1.0
        # restructure the document without the recognized quotes
        else:
            doc_content += divide[i]
    
    return doc_content, quotes

# indexation conceputal
def indexation(collocs, doc_name, stoplist, tokens):
    # a variable that holds the length of the longest collocation
    global longest_colloc_length
    global CLEAN_RE
    
    # if doc_name endswith .txt the it's a doc, else it has the content of a query
    if doc_name.endswith(".txt"):
        # id of docs is the number of the doc
        doc_id = doc_name.split(".txt")[0]
        
        # get the document's content
        doc_path = os.path.join(docs_path, doc_name)
        doc_content = read_doc(doc_path).lower().split()

    # query indexing requires redeclaring the global variables
    else:
        CLEAN_RE = re.compile(r'[^a-zA-Z0-9\-\s]')
        length_of_longest_colloc(collocs)
        doc_id = "query"
        doc_content = doc_name.lower()

        # recognize the quotes inside a query as a collocation
        doc_content, quotes = quotes_rec(doc_content)

        # ignore punctutation in queries
        doc_content = CLEAN_RE.sub('', doc_content).split()

        # add the quotes to the tokens list
        merge_dicts(quotes, tokens, doc_id)

    # variable to count the frequency of tokens in each doc
    global sum_freq_docs
    sum_freq_docs[doc_id] = 0

    # important variables
    colloc_length = 0
    have_pass = False
    
    for i in range(len(doc_content)):
        ith_collocs = {}
        
        target = doc_content[i]
        have_pass = False
        
        # construct collocations according to the largest possible one
        for j in range(longest_colloc_length):
            # constructing potenial collocation
            if (j != 0):
                # if we can't add words because it's the end of the file
                if (i+j >= len(doc_content)):
                    break
                target += f" {doc_content[i+j]}"
                
            # add_token means a colloc or a sub colloc is recognized
            # look_more = false means no potenial colloc
            look_more, add_token = colloc_rec(collocs, target)
            if (add_token):
                # previous ith collocs are not the full collocation
                for key in ith_collocs.keys():
                    ith_collocs[key] = 1/5
                # case of sub colloc when not skipping. ('rdms' -> 'dm', 'dms')
                if (colloc_length > 0 and not have_pass):
                    ith_collocs[target] = 1/5
                # add as potential full colloc
                else:
                    ith_collocs[target] = 1.0
                    colloc_length = len(target.split())
                    have_pass = True
            
            # this tries to see if target is a colloc that ends with a punctutation
            # in the case of a query, punctuation is previously eliminated.
            elif(not look_more):
                # if target is one word then no collocs expected
                if (len(target.split()) == 1):
                    break
                # handle case of target is a colloc that ends with punctuation
                target = target.split(f" {doc_content[i+j]}")[0]
                cleaned_string = CLEAN_RE.sub('', doc_content[i+j])
                
                # if cleaned_string is not an empty string
                if cleaned_string.strip() != '':
                    target += f" {str(cleaned_string).strip()}"

                    look_more, add_token = colloc_rec(collocs, target)
                    # no ith token will produce duplicate collocs in ith_collocs
                    # so its normal to have the frequence here as the const 1
                    if (add_token):
                        for key in ith_collocs.keys():
                            ith_collocs[key] = 1/5
                        if (colloc_length > 0 and not have_pass):
                            ith_collocs[target] = 1/5

                        else:
                            ith_collocs[target] = 1.0
                            colloc_length = len(target.split())
                            have_pass = True
                break
        # hundle score of sub collocs / skip sub collocs
        if (colloc_length > 0):
            colloc_length -= 1
            # continue
        else:
            # if ith token is not a part of a colloc
            # remove punctuation if exists except '-' and add it
            target = CLEAN_RE.sub('', doc_content[i]).strip()
            
            # skip the target when it's an empty string
            if target == '':
                continue
            
            # if the '-' is note between two words then remove it as well
            if target.split('-')[0] == '':
                target = target.split('-')[1]
            
            # skip the target when it's an empty string or a mono mot but starts with a digit
            if target == '':
                continue

            # is_stoplist True means target is recognized in the stop list
            _, is_stoplist = colloc_rec(stoplist, target)

            # if target is not in the stop list then add it to tokens
            if (not is_stoplist):
                ith_collocs[target] = 1.0

        # Merge ith_collocs into tokens
        merge_dicts(ith_collocs, tokens, doc_id)

        # sum of tokens of a document is the sum of recognised tokens
        sum_freq_docs[doc_id] += len(ith_collocs)

    # in case we're indexing the query, reutrn freq and normalise tf by the sum
    if not doc_name.endswith('.txt'):
        query_tokens_sum = {}
        for token, posting in tokens.items():
            for query_index, freq in posting.items():
                query_tokens_sum[token] = {query_index: freq / sum_freq_docs[doc_id]}
        return tokens, query_tokens_sum
    
    return tokens
    
def merge_dicts(ith_collocs, tokens, doc_id):
    # this variable is used to confirm that the token appears for the 1st time for doc[i]
    add_token = False
    # copy the collocs/subcollocs that we get from ith token
    # tokens = [string, int, bool] / ith_collocs = [int, bool]
    for key, value in ith_collocs.items():
        # if the ith_colloc exists in tokens
        if key in tokens:
            # loop on the ids of that token
            for id in tokens[key].keys():
                # if it appears again wait if it doesn't exist in all docs
                if id != doc_id:
                    add_token = True
                # if it appears again in the same document we just update the corresponding token's posting
                else:
                    # Sum the integers and combine the boolean values (keep True if exists)
                    tokens[key][id] += value
                    add_token = False
                    break
                
            # if it appears again in a different document for the 1st time append to the token's posting
            if(add_token):
                tokens[key][doc_id] = value
        # if it doesn't exist in tokens we just add it
        else:
            # Copy the key-value pair from ith_collocs to tokens
            tokens[key] = {doc_id: value}

# calculate the idf of each token
def get_idfs(tokens):
    
    idfs = {}
    global num_docs
    for token, posting in tokens.items():
        # log of (number of docs devided by number of docs the token appears in)
        idfs[token] = round(math.log10(num_docs/len(posting)), 3)
    
    return idfs

# calculate max freq for each doc
def get_docs_max_freq(tokens):
    max_freq_docs = {}
    
    for token, posting in tokens.items():
        for doc_id, freq in posting.items():
            if doc_id in max_freq_docs.keys():
                if posting[doc_id] > max_freq_docs[doc_id]:
                    max_freq_docs[doc_id] = posting[doc_id]
            else:
                max_freq_docs[doc_id] = posting[doc_id]
    
    return max_freq_docs

def fichier_inverse_freq(sorted_tokens, tokens, idfs):
    fi_freq = {}
    # add the tokens in alphabetical order
    for key in sorted_tokens:
        # Initialize the posting (dictionary) for each key
        fi_freq[key] = {}

        # Sort posting docs by weight in descending order
        for doc_id, tf in sorted(tokens[key].items(), key=lambda item: item[1], reverse=True):

            # tf * idf
            fi_freq[key][doc_id] = round(tf * idfs[key], 3)
    
    return fi_freq

def fichier_inverse_sum(sorted_tokens, tokens, idfs):
    fi_sum = {}
    # add the tokens in alphabetical order
    for key in sorted_tokens:
        # Initialize the posting (dictionary) for each key
        fi_sum[key] = {}

        # Sort posting docs by weight in descending order
        for doc_id, freq in sorted(tokens[key].items(), key=lambda item: item[1], reverse=True):
            # tf normalise paraport a la somme
            tf = freq / sum_freq_docs[doc_id]
            
            # tf * idf
            fi_sum[key][doc_id] = round(tf * idfs[key], 3)
    
    return fi_sum

def fichier_inverse_max(sorted_tokens, tokens, idfs, max_freq_docs):
    fi_max = {}
    # add the tokens in alphabetical order
    for key in sorted_tokens:
        # Initialize the posting (dictionary) for each key
        fi_max[key] = {}

        # Sort posting docs by weight in descending order
        for doc_id, freq in sorted(tokens[key].items(), key=lambda item: item[1], reverse=True):
            # tf normalise paraport a la somme
            tf = freq / max_freq_docs[doc_id]
            
            # tf * idf
            fi_max[key][doc_id] = round(tf * idfs[key], 3)
    
    return fi_max


# main call
if __name__ == "__main__":
    main()
