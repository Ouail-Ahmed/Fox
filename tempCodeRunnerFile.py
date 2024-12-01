def get_lemmas(pos_tokens: list[tuple[str, str]]) -> list[str]:
    lemms = []
    for token, pos in pos_tokens:
        if pos == "NOUN":
            lemms.append(lemmatizer.lemmatize(token, pos="n"))
        elif pos == "VERB":
            lemms.append(lemmatizer.lemmatize(token, pos="v"))
        elif pos == "ADJ":
            lemms.append(lemmatizer.lemmatize(token, pos="a"))
    return lemms