import joblib
import populate_books
import numpy as np

from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.preprocessing import preprocess_documents
from sklearn.neighbors import NearestNeighbors
from gensim.test.utils import get_tmpfile




books = populate_books.read_books_data().drop_duplicates("Title")

titles =[TaggedDocument(doc, [i]) for i, doc in enumerate(preprocess_documents(books["Title"]))]

model = Doc2Vec(titles,
                vector_size=1000,
                window=5,
                min_count=1,
                workers=50,
                dm=0,
                epochs=100)
model.save("d2v_titles.model")
description =[TaggedDocument(doc, [i]) for i, doc in enumerate(preprocess_documents(books["description"])) if doc]
model_description = Doc2Vec(description,
                vector_size=100,
                window=5,
                min_count=1,
                workers=50,
                dm=0,
                epochs=100)
model_description.save("../recommendation/d2v_descriptions.model")

book_vecs = np.array([model_description.dv[i] for i in range(len(books))])

neigh = NearestNeighbors(n_neighbors=5, metric="cosine")
neigh.fit(book_vecs)
joblib.dump(neigh, "../recommendation/description_neighbors.pkl")