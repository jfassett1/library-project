import pandas as pd
import random as rand
import os


current_path = os.path.dirname(__file__)
parent_folder = os.path.abspath(os.path.join(current_path, os.pardir))
data_folder = os.path.join(os.pardir, "../data/")

#Books data cleaning
books = pd.read_csv(f"{data_folder}books.csv")
books = books.dropna()
books.drop_duplicates(subset=["isbn13"],keep="first",inplace=True)
mask = books.map(lambda x: '?' in str(x)).any(axis=1)
books = books[~mask]

#Tags
tags = pd.read_csv(f"{data_folder}tags.csv")


book_cols = ["isbn13","original_title","original_publication_year"]

def create_bookdata(df=books):
    book_tuples = []
    for i in range(len(books)):
        isbn13 = int(books.iloc[i]["isbn13"])
        original_title = books.iloc[i]["original_title"]
        original_publication_year = int(books.iloc[i]["original_publication_year"])
        desc = "filler"
        book_tuples.append((isbn13, original_title, original_publication_year,desc))
    return tuple(book_tuples)

def create_data_set(df, column_names):
    data_tuples = []

    for i in range(len(df)):
        row_data = tuple(df.iloc[i][col] for col in column_names)
        data_tuples.append(row_data)

    return tuple(data_tuples)


