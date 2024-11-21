from nltk.corpus import wordnet as wn 
from nltk import word_tokenize 
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer


lemmatizer = WordNetLemmatizer()
with open ("C:/Users/ahmed/Documents/Programming/Python/test.txt","r",-1 ,"utf-8")as file:
    text = file.read()
text = text.lower()
tokens = word_tokenize(text)
print(tokens)
pos_tokens = pos_tag(tokens, tagset="universal")
print(pos_tokens)


lemms = []
for pos_token in pos_tokens:
    token , pos = pos_token
    if pos == "NOUN":
        lemms.append(lemmatizer.lemmatize(token ,pos="n"))
    elif pos == "VERB":
        lemms.append(lemmatizer.lemmatize(token ,pos="v"))
    elif pos == "ADJ":
        lemms.append(lemmatizer.lemmatize(token ,pos="a"))

print(lemms)




