

def read_doc (doc):
    index = []
    with open (doc , "r") as file:
        for line in file:
            index.extend(line.split(sep = " "))
            return index


try:
    word_list = read_doc ("C:/Users/ahmed/Documents/Programming/Python/Collection_TIME/017.txt")
    print(word_list)

except FileNotFoundError:
    print("Error : File not found")