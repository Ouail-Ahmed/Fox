import tkinter as tk
import os
from tkinter import ttk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet as wn
from query import search


# Example documents
documents = [
    "The cat sits on the mat.",
    "The cat sits on the mat too.",
    "Dogs are in the yard.",
    "The bird is flying in the sky.",
    "Fish swim in the sea."
]

# chat gpt generated indexation for tests 

docs_path = os.path.join("assets", "collection_time")


def get_concepts(document):
    words = document.split()
    concepts = []
    for word in words:
        synsets = wn.synsets(word)
        if synsets:
            concept = synsets[0].lemmas()[0].name()
            concepts.append(concept)
    return ' '.join(concepts)

# Indexing documents
indexed_documents = [get_concepts(doc) for doc in documents]

# Creating the TF-IDF vector
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(indexed_documents)

# Search function
# def search(query):
#     query_concepts = get_concepts(query)
#     query_vector = vectorizer.transform([query_concepts])
#     similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
#     ranked_indices = similarities.argsort()[::-1]
#     results = [(i, similarities[i]) for i in ranked_indices if similarities[i] > 0]
#     return results



#interface starts here



# GUI class
class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Recherche de documents par l'indexation conceptuelle")
        self.root.configure(bg='#f4f5f7')

        self.style = ttk.Style()
        self.style.configure('TLabel', background='#f4f5f7', font=('Helvetica World', 12))
        self.style.configure('TEntry', font=('Helvetica World', 12))
        self.style.configure('TButton', font=('Helvetica World', 12))

        self.query_label = ttk.Label(root, text="Indexation Conceptuelle", foreground='#11224e', font=('Helvetica World', 20, 'bold'))
        self.query_label.pack(pady=5)

        self.query_entry = ttk.Entry(root, width=50)
        self.query_entry.pack(pady=5)

        self.style.map("TButton",
                       foreground=[('active', '#11224e'), ('!active', '#11224e')],
                       background=[('active', '#99c8d1'), ('!active', '#b8d8e0')])

        self.search_button = ttk.Button(root, text="Rechercher", command=self.perform_search, style='Rounded.TButton')
        self.search_button.pack(pady=5)

        self.results_text = tk.Text(root, width=80, height=20, font=('Helvetica World', 12))
        self.results_text.pack(pady=5)



        self.results_text.tag_bind("link", "<Button-1>", self._click)

        self.links = {}

        # Correct the style configuration for the rounded button
        self.style.configure('Rounded.TButton', background='#b8d8e0', foreground='#11224e', padding=6)
        self.style.map('Rounded.TButton',
                       background=[('active', '#99c8d1')],
                       foreground=[('active', '#11224e')])

    def perform_search(self):
        query = self.query_entry.get()
        results = search(query)
        print(f"Results: {results}")
        self.results_text.delete(1.0, tk.END)
        self.links.clear()

        if results:
            for idx, doc_index in enumerate(results):
                tag_name = f"link_{idx}"
                print (f"Document {doc_index } ")
                self.results_text.insert(tk.END, f"Document {doc_index }\n", tag_name)
                # self.results_text.tag_add(tag_name, f"{idx+1}.0", f"{idx+1}.end")
                self.results_text.tag_bind(tag_name, "<Button-1>", self._click)
                self.links[tag_name] = f"{docs_path}\\{doc_index}.txt"
                print(f"Linked {tag_name} to document {doc_index}")
        else:
            self.results_text.insert(tk.END, "No results found.")
        self.results_text.config(state=tk.DISABLED) 


    def _click(self, event):
        clicked_index = self.results_text.index(f"@{event.x},{event.y}")
        tag_names = self.results_text.tag_names(clicked_index)
        for tag in tag_names:
            if tag.startswith("link_"):
                doc_index = self.links.get(tag, None)
                if doc_index is not None:
                    self.show_document_content(doc_index)
                else:
                    print(f"No document found for clicked index: {clicked_index}")
                break

    def show_document_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            doc_window = tk.Toplevel(self.root)
            doc_window.title(f"Document: {file_path}")

            text_widget = tk.Text(doc_window, wrap='word', font=('Helvetica World', 12))
            text_widget.pack(expand=1, fill='both', padx=10, pady=10)
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except Exception as e:
            print(f"An error occurred while opening the file: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SearchApp(root)
    root.mainloop()
