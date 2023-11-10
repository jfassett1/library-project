from itertools import repeat
import pandas as pd
# TODO: Update paths to use pathlib instead of strings
import pathlib
import os

def create_bookdata(books:pd.DataFrame):
    return tuple(
        zip(
            books["isbn13"].astype(int),
            books["original_title"],
            books["original_publication_year"].astype(int),
            repeat("Filler")
        )
    )


def create_data_set(df, column_names):
    data_tuples = []

    for i in range(len(df)):
        row_data = tuple(df.iloc[i][col] for col in column_names)
        data_tuples.append(row_data)

    return tuple(data_tuples)

current_path = os.path.dirname(__file__)
os.path.abspath(os.path.join(current_path, os.pardir))
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
bookdata = create_bookdata(books)
tagdata = create_data_set(tags,tags.columns)
