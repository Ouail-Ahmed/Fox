import re, math, os
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
from sentence_transformers import SentenceTransformer, util

# Load the language model
model = SentenceTransformer('all-MiniLM-L6-v2')

# docs path
docs_path = os.path.join("assets", "collection_time")

longest_colloc_length = 0

# variable that holds the number of docs
num_docs = 0

# for fichier inverse tf normalised by sum
sum_freq_docs = {}

# split on punctuation if it's in the end
split_on_punct_start = re.compile(r'^([^\w\s]+)(.*?)$')

# split on punctuation if it's in the end
split_on_punct_end = re.compile(r'^(.*?)([^\w\s]+)$')
# eliminate punctuation
CLEAN_RE = re.compile(r'[^a-zA-Z0-9\-\s]')


lemmatizer = WordNetLemmatizer()

def start(collocs, stoplist):

    length_of_longest_colloc(collocs)
    tokens = {}

    docs_list = sorted(os.listdir(docs_path))

    global num_docs

    for doc_name in docs_list:
        # don't process files that are not .txt
        if doc_name.endswith(".txt"):
            # don't count docs that are not indexed
            num_docs += 1

            doc_tokens, sum_indexes = indexation(collocs, doc_name, stoplist)

            doc_tokens = lemmatization(doc_tokens)

            doc_tokens, deleted_tokens = remove_stop_words(stoplist, doc_tokens)
            
            # doc_id is the name of the file without .txt
            doc_id = doc_name.split(".txt")[0]

            # sum of indexes in this doc
            sum_freq_docs[doc_id] = sum_indexes - deleted_tokens

            for token in doc_tokens:
                # Add the tokens and there posting if it doesn't exist in tokens
                if token not in tokens.keys():
                    tokens[token] = {doc_id: doc_tokens[token]}
                # Merge the dictionaries if the token exists
                else:
                    tokens[token].update({doc_id: doc_tokens[token]})
            #break
        else:
            print(f"missing .txt extention.\n{doc_name} is not considered as a text file")

    # get the idfs of tokens
    #idfs = get_idfs(tokens)

    # for fichier inverse tf normalised by max
    max_freq_docs = get_docs_max_freq(tokens)

    # Sort tokens alphabetically
    sorted_tokens = sorted(tokens.keys())

    # fichier inverse (weight is tf*idf where tf = freq)
    fi_freq = fichier_inverse_freq(sorted_tokens, tokens)

    # fichier inverse (weight is tf*idf where tf is normalised by the sum)
    fi_sum = fichier_inverse_sum(fi_freq)

    # fichier inverse (weight is tf*idf where tf is normalised by the max)
    fi_max = fichier_inverse_max(fi_freq, max_freq_docs)

    return fi_freq, fi_sum, fi_max

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
    CLEAN_RE = re.compile(r'[^a-zA-Z0-9\'\-\s]')
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

    if len(quotes) == 1:
        no_quotes = list(quotes.keys())[0]
        # when there's no quotes it adds an empty string
        if no_quotes == "" and quotes[no_quotes] == 1.0:
            del quotes['']

    return doc_content, quotes

# construct collocations according to the largest possible one
def construct_collocations(colloc_length, i, target, doc_content, collocs):
        ith_collocs = {}
        have_pass = False

        full_colloc = ""
        full_colloc_length = 0
        full_colloc_embedding = None

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
                # add to ith_collocs
                ith_collocs[target] = 1.0
                # add as potential full colloc
                # at first colloc_length is 0 and have_pass is False
                # but when a colloc is recognized colloc_length is not 0 
                # but it have_pass is True to check if there isn't a longest colloc
                if (colloc_length == 0 or have_pass):
                    full_colloc = target
                    full_colloc_length = len(target.split())
                    full_colloc_embedding = model.encode(target, convert_to_tensor=True)
                    colloc_length = len(target.split())
                    # to allow checking if there's not a longer colloc
                    have_pass = True
            
            # this tries to see if target is a colloc that ends with a punctutation
            # in the case of a query, punctuation is previously eliminated.
            elif(not look_more):
                # handle case of target is a colloc that ends with apostrophe
                # remove the last word of the potential colloc
                target = target.split(f" {doc_content[i+j]}")[0]

                # confirm it's not that the colloc end with additional apostrophe
                # example: de gaulle's
                cleaned_string = (doc_content[i+j].replace("'s", " s").replace("n't", " not").
                replace("'re", " are").replace("'ve", " have")
                .replace("'ll", " will").replace("'d", " would").replace("'m", " am")
                    .replace("'em", " them").replace("'all", " all")).split()[0]
                
                # here it will be de gaulle
                target += f" {str(cleaned_string).strip()}"

                look_more, add_token = colloc_rec(collocs, target)
                # no ith token will produce duplicate collocs in ith_collocs
                # so its normal to have the frequence here as the const 1
                if (add_token):
                    # colloc_length > 0 means this is a sub colloc have_pass means 
                    # it can be a longer colloc, so we insert it when it's not.
                    ith_collocs[target] = 1.0
                    
                    if (colloc_length == 0 or have_pass):
                        full_colloc = target
                        full_colloc_length = len(target.split())
                        full_colloc_embedding = model.encode(target, convert_to_tensor=True)
                        colloc_length = len(target.split())
                
                elif(not look_more):
                    # if target is one word then no collocs expected
                    if (len(target.split()) == 1):
                        break

                    # handle case of target is a colloc that ends with punctuation
                    # remove the last word of the potential colloc
                    target = target.split(f" {doc_content[i+j]}")[0]

                    # remove punctutation that last word
                    cleaned_string = CLEAN_RE.sub('', doc_content[i+j])
                    
                    # if cleaned_string is not an empty string
                    if cleaned_string.strip() != '':
                        target += f" {str(cleaned_string).strip()}"

                        look_more, add_token = colloc_rec(collocs, target)
                        # no ith token will produce duplicate collocs in ith_collocs
                        # so its normal to have the frequence here as the const 1
                        if (add_token):
                            # colloc_length > 0 means this is a sub colloc have_pass means 
                            # it can be a longer colloc, so we insert it when it's not.
                            ith_collocs[target] = 1.0
                            if (colloc_length == 0 or have_pass):
                                full_colloc = target
                                full_colloc_length = len(target.split())
                                full_colloc_embedding = model.encode(target, convert_to_tensor=True)
                                colloc_length = len(target.split())
                # no longer colloc possible here, because of punctuation or apostrophe
                break

        return full_colloc, full_colloc_length, full_colloc_embedding, ith_collocs

# indexation conceputal
def indexation(collocs, doc_name, stoplist):
    # a variable that holds the length of the longest collocation
    global longest_colloc_length
    global CLEAN_RE

    doc_tokens = {}
    sum_freq_quotes = 0
    
    # if doc_name endswith .txt then it's a doc, else it has the content of a query
    if doc_name.endswith(".txt"):
        # id of docs is the number of the doc
        # doc_id = doc_name.split(".txt")[0]
        
        # get the document's content
        doc_path = os.path.join(docs_path, doc_name)
        doc_content = read_doc(doc_path).lower().split()

    # query indexing requires redeclaring the global variables
    else:
        CLEAN_RE = re.compile(r'[^a-zA-Z0-9\-\s]')

        length_of_longest_colloc(collocs)
        
        # doc_name is the content of the query
        doc_content = doc_name.lower()

        # recognize the quotes inside a query as a collocation
        doc_content, quotes = quotes_rec(doc_content)

        # ignore punctutation in queries
        doc_content = doc_content.split()

        # count the queries words number for tf normalised to the sum
        sum_freq_quotes = len(quotes)

        # add the quotes to the tokens list
        merge_dicts(quotes, doc_tokens)

    # variable to count the frequency of tokens in each doc
    global sum_freq_docs
    sum_indexes = 0

    # important variables
    colloc_length = 0

    # to know the colloc that produces sub collocs
    full_colloc = ""
    full_colloc_length = 0
    
    for i in range(len(doc_content)):
        # construct potential collocations
        fc_tmp, fcl_tmp, fce_tmp, ith_collocs = \
                construct_collocations(colloc_length, i, doc_content[i], doc_content, collocs)
        
        # if a colloc is recognized and it's not a sub colloc
        if (fcl_tmp != 0 and colloc_length == 0):
            full_colloc = fc_tmp
            full_colloc_length = fcl_tmp
            colloc_length = fcl_tmp
            full_colloc_embedding = fce_tmp
            
        # skip sub collocs
        if (colloc_length == 0):
            # if ith token is not a part of a colloc
            # if ith word is 2 words combind with apostrophe split them to 2 words
            target = doc_content[i]

            # to add a token that is in the stop list before modifying it
            # "can't" becaumes ca not with the transformation. "won't" too
            if target in stoplist:
                ith_collocs[target] = 1.0
            
            else:
                target = (doc_content[i].replace("'s", " s").replace("n't", " not").
                        replace("'re", " are").replace("'ve", " have")
                        .replace("'ll", " will").replace("'d", " would").replace("'m", " am")
                            .replace("'em", " them").replace("'all", " all").replace("\"", "``"))
                
                # $800 -> $, 800, (time) -> ( time)
                result = re.match(split_on_punct_start, target)
                if result:
                    punct, target = result.group(1), result.group(2)
                    # this is how pos_tag recognize the quotes
                    if punct == "``":
                        ith_collocs[punct] = 1.0
                    # pos_tag doesn't recognize multuple punctuations at once
                    # so if the punctuation is !!? it's enough to take only the 1st one
                    else:
                        ith_collocs[punct[0]] = 1.0

                # time) -> time )
                end_punct = False
                result = re.match(split_on_punct_end, target)
                if result:
                    target, punct = result.group(1), result.group(2)
                    end_punct = True

                targets = target.split()
                # if the target was really 2 words, else the loop will have only 1 iteration
                for target in targets:
                    # skip the target[i] when it's an empty string or a mono mot but starts with -
                    # seems duplicate but the second one is the more important one and without
                    # this one an error happens in the next split if target[i] is empty string
                    
                    # if the '-' is note between two words then remove it as well
                    if target.split('-')[0] == '':
                        target = target.split('-')[1]
                    
                    # skip the target when it's an empty string or a mono mot but starts with -
                    if target == '':
                        continue

                    ith_collocs[target] = 1.0
                # (time) -> ['(', 'time'] added previously, and now time for ')'
                if end_punct:
                    if punct == "``":
                        ith_collocs[punct] = 1.0
                    else:
                        ith_collocs[punct[0]] = 1.0
        
        # if the collocations in ith_colloc could be sub collocs
        if full_colloc != "":
            if (colloc_length == full_colloc_length and len(ith_collocs) > 1):
                for colloc in ith_collocs:
                    if colloc != full_colloc:
                        sub_colloc_embedding = model.encode(colloc, convert_to_tensor=True)
                        similarity = util.pytorch_cos_sim(full_colloc_embedding, sub_colloc_embedding).item()
                        ith_collocs[colloc] = similarity

            if (0 < colloc_length < full_colloc_length and len(ith_collocs) > 0):
                for colloc in ith_collocs:
                    sub_colloc_embedding = model.encode(colloc, convert_to_tensor=True)
                    similarity = util.pytorch_cos_sim(full_colloc_embedding, sub_colloc_embedding).item()
                    ith_collocs[colloc] = similarity

        # Merge ith_collocs into tokens
        merge_dicts(ith_collocs, doc_tokens)

        # sum of tokens of a document is the sum of recognised tokens
        sum_indexes += len(ith_collocs)

        # when colloc_length > 0 then this token is inside a recognized collocation
        # when it's back to 0 then we're out of it
        if (colloc_length > 0):
            colloc_length -= 1

    # in case we're indexing the query, reutrn freq and normalise tf by the sum
    if not doc_name.endswith('.txt'):
        # add to the sum the recognized quotes which were extracted from the start of this func
        sum_indexes += sum_freq_quotes

        # remove stop words from query
        doc_tokens, deleted_indexes = remove_stop_words(stoplist, doc_tokens)

        # remove the number of stop words from the sum words of the query
        sum_indexes -= deleted_indexes

        # dict of query tokens with the weight being tf normalised to the sum
        query_tokens_sum = {}

        for token in doc_tokens:
            query_tokens_sum[token] = round(doc_tokens[token] / sum_indexes,2)
        return doc_tokens, query_tokens_sum
    
    return doc_tokens, sum_indexes
    
def merge_dicts(ith_collocs, doc_tokens):
    # this variable is used to confirm that the token appears for the 1st time for doc[
    # copy the collocs/subcollocs that we get from
    # tokens = [string, int, bool] / ith_collocs = [int, bool]
    for key, value in ith_collocs.items():
        # if the ith_colloc exists in tokens
        if key in doc_tokens:
            # if it appears again in the same document we just update the corresponding token's posting
            # Sum the integers and combine the boolean values (keep True if exists)
            doc_tokens[key] += value
        
        # if it doesn't exist in doc_tokens we just add it
        else:
            # Copy the key-value pair from ith_collocs to doc_tokens
            doc_tokens[key] = value

def remove_stop_words(stoplist, tokens):
    global sum_freq_docs
    stopwords = []
    deleted = 0

    # get the stop words that are in tokens
    for token in tokens.keys():
        if token in stoplist:
            stopwords.append(token)
        if CLEAN_RE.match(token):
            stopwords.append(token)

    # clear_re don't recognize -
    if "-" in tokens.keys():
        stopwords.append("-")

    # remove the stopwords from the tokens
    for stopword in stopwords:
        # count the number of accurent of the stopword in tokens 
        # to remove it from the sum of indexes of the doc
        deleted += tokens[stopword]
        del tokens[stopword]
  
    return tokens, int(deleted)

def lemmatization(doc_tokens):
    global lemmatizer

    # get the tags of each index of the doc
    tags = pos_tag(doc_tokens.keys(), tagset="universal")

    lemm = ""
    lemms = []
    for word, pos in tags:
        # get the lemms of only mono words that doesn't contain -
        if ' ' not in word and '-' not in word:
            if pos == "NOUN":
                lemm = lemmatizer.lemmatize(word, pos="n")
            elif pos == "VERB":
                lemm = lemmatizer.lemmatize(word, pos="v")
            elif pos == "ADJ":
                lemm = lemmatizer.lemmatize(word, pos="a")
            elif pos == "ADV":
                lemm = lemmatizer.lemmatize(word, pos="r")
            else:
                continue
            
            if lemm in lemms:
                doc_tokens[lemm] += doc_tokens.pop(word)
            # replace that word with it's lemm
            else:
                # if the lemm of word is an already existing key in doc_tokens 
                if lemm in doc_tokens.keys() and lemm != word:
                    doc_tokens[lemm] += doc_tokens.pop(word)
                    continue

                lemms.append(lemm)
                doc_tokens[lemm] = doc_tokens.pop(word)
    
    return doc_tokens

# calculate max freq for each doc
def get_docs_max_freq(tokens):
    max_freq_docs = {}
    
    for token, posting in tokens.items():
        for doc_id, freq in posting.items():
            if doc_id in max_freq_docs.keys():
                if freq > max_freq_docs[doc_id]:
                    max_freq_docs[doc_id] = freq
            else:
                max_freq_docs[doc_id] = freq
    
    return max_freq_docs

def fichier_inverse_freq(sorted_tokens, tokens):
    fi_freq = {}
    # add the tokens in alphabetical order
    for token in sorted_tokens:
        # Initialize the posting (dictionary) for each token
        fi_freq[token] = {}

        # Sort posting docs by weight in descending order
        for doc_id, tf in sorted(tokens[token].items(), key=lambda item: item[0]):
            # tf * idf
            fi_freq[token][doc_id] = tf
    
    return fi_freq

def fichier_inverse_sum(fi_freq):
    fi_sum = {}
    
    # copy fichier inverse with the change of dividing the freq
    # on the sum of indexes in the ith doc that it appears in 
    for token, posting in fi_freq.items():

        fi_sum[token] = {}
        for doc_id, freq in posting.items():
            fi_sum[token][doc_id] = round(freq / float(sum_freq_docs[doc_id]), 3)
    
    return fi_sum

def fichier_inverse_max(fi_freq, max_freq_docs):
    fi_max = {}
    
    # copy fichier inverse with the change of dividing the freq
    # on the sum of indexes in the ith doc that it appears in 
    for token, posting in fi_freq.items():
        
        fi_max[token] = {}
        for doc_id, freq in posting.items():
            fi_max[token][doc_id] = round(freq / float(max_freq_docs[doc_id]), 3)
    
    return fi_max

# calculate the idf of each token / unused because it's better to store tf in FI
def get_idfs(tokens):
    
    idfs = {}
    global num_docs
    for token, posting in tokens.items():
        # log of (number of docs devided by number of docs the token appears in)
        idfs[token] = round(math.log10(num_docs/len(posting)), 3)
    
    return idfs
