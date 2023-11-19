import pandas as pd
import numpy as np
import pathlib
import os

def auto_truncate(val, length:int):
    """
    Truncate subscriptable input

    Args:
        val (Subscriptable): Object to be truncated
        length (int): Max Object Length

    Returns:
        Subscriptable: Truncated object
    """
    return val[:length]

def create_book_data(book_data:pd.DataFrame):
    """prepare book data for insertion

    Args:
        book_data (pd.DataFrame): book data

    Returns:
        tuple: tuples to be inserted into book_data table
    """
    return tuple(
        zip(
            book_data["Title"],
            book_data["publishedDate"],
            pd.Categorical(book_data["publisher"]).codes,
            pd.Categorical(book_data["categories"]).codes,
            book_data["description"]
        )
    )

def create_author_data(book_data:pd.DataFrame):
    # TODO: #6 Insert author data into a table
    return books_data


def generate_library(book_data:pd.DataFrame)->tuple[tuple,...]:
    def append_period_and_copy_number(group):
        group["newDecimalCode"] =  group["DecimalCode"] + "." + group.groupby("DecimalCode").cumcount().astype(str)
        return group
    sample = book_data.groupby("categories").sample(frac=0.10, replace=True, weights=book_data["ratingsCount"]+1)["categories"]
    status = np.random.randint(0, 3, len(sample))
    category_codes = pd.Categorical(sample).codes
    codes = category_codes.astype(str)
    books = pd.DataFrame({ "DecimalCode":codes,"BookID":sample.index,"BookStatus":status})
    books["DecimalCode"] += "."
    books["DecimalCode"] += books["BookID"].astype(str).apply(lambda x: auto_truncate(x, 5))
    books =  books.groupby("DecimalCode").apply(append_period_and_copy_number).loc[:,["newDecimalCode","BookID", "BookStatus"]]
    books = books.reset_index().drop(["DecimalCode", "level_1"], axis=1).rename({"newDecimalCode":"DecimalCode"}, axis=1)
    return tuple(books.itertuples(index=False, name=None))

def extract_categorical_book_data(book_data:pd.DataFrame, column_name:str):
    """Get codes for a categorical feature

    Args:
        book_data (pd.DataFrame): Book data frame
        column_name (str): name of column to extract

    Returns:
        tuple: tuple of tuples of category code and category name
    """
    data = book_data[column_name].unique()
    return tuple(zip( pd.Categorical(data).codes, data))



def read_books_data():
    parent_project_path = pathlib.Path(os.path.dirname(__file__)).parents[1]
    data_folder = parent_project_path/"data"
    books_data = pd.read_csv(
        data_folder/"books_data.csv",
        converters={
            "publisher":lambda x: auto_truncate(x, 50),
            "Title":lambda x: auto_truncate(x, 255),
            "categories": lambda x: x[2:-2],
            },
        nrows=100_000
        )

    books_data = books_data.drop_duplicates(subset = "Title")
    books_data["publishedDate"] = books_data["publishedDate"].fillna("-9999")
    books_data["publishedDate"] = books_data["publishedDate"].str.replace(r'\?', '0', regex=True)
    books_data["publishedDate"] = books_data["publishedDate"].str.extract(r"(^-?\d{,4})")
    books_data["publishedDate"] = books_data["publishedDate"].astype('int')

    books_data["publisher"] = pd.Categorical(books_data["publisher"])
    books_data["categories"] = pd.Categorical(books_data["categories"])
    books_data = books_data.where(pd.notnull(books_data), None)
    books_data["ratingsCount"] = books_data["ratingsCount"].fillna(0)
    # books_data = books_data.dropna(axis=0)

    return books_data

if __name__ == "__main__":

    books_data = read_books_data()
    print(books_data.head())
    # print(generate_library(books_data))
    # print(books_data["categories"])
    # print(books_data.isna().sum())
    # print(books_data["publishedDate"].min(),books_data["publishedDate"].max())
    # print(books_data.dtypes)
    # print()
    # print(books_data["Title"].iloc[115:125])
    # print(books_data[books_data["Title"]=="World in Eclipse"])
