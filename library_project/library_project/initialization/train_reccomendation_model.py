import joblib
import populate_books
import numpy as np

from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.preprocessing import preprocess_documents
from sklearn.neighbors import NearestNeighbors
from gensim.test.utils import get_tmpfile
import os

# Set working directory to directory of this file
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Read formatted books dataset
books = populate_books.read_books_data()

# Convert all titles to preprocessed tagged documents
titles =[TaggedDocument(doc, [i]) for i, doc in enumerate(preprocess_documents(books["Title"]))]
# Train the model
model = Doc2Vec(titles,
                vector_size=100,
                window=5,
                min_count=1,
                workers=50,
                dm=0,
                epochs=100)
# Save model files for later use
model.save("../recommendation/d2v_titles.model")

# Create book description vectors
description =[TaggedDocument(doc, [i]) for i, doc in enumerate(preprocess_documents(books["description"])) if doc]

# Train and save doc2vec model
model_description = Doc2Vec(description,
                vector_size=100,
                window=5,
                min_count=1,
                workers=50,
                dm=0,
                epochs=100)
model_description.save("../recommendation/d2v_descriptions.model")

# book_vecs = np.array([model_description.dv[i] for i in range(len(books))])

# neigh = NearestNeighbors(n_neighbors=5, metric="cosine")
# neigh.fit(book_vecs)
# joblib.dump(neigh, "../recommendation/description_neighbors.pkl")