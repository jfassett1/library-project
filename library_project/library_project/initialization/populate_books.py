import pandas as pd
import pathlib
import os

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


def read_books_data():
    parent_project_path = pathlib.Path(os.path.dirname(__file__)).parents[1]
    data_folder = parent_project_path/"data"
    books_data = pd.read_csv(
        data_folder/"books_data.csv",
        converters={
            "publisher":lambda x: auto_truncate(x, 50),
            "Title":lambda x: auto_truncate(x, 255),
            "categories": lambda x: x[2:-2],
            }
        )

    books_data = books_data.drop_duplicates(subset = "Title")
    books_data["publishedDate"] = books_data["publishedDate"].fillna("-9999")
    books_data["publishedDate"] = books_data["publishedDate"].str.replace(r'\?', '0', regex=True)
    books_data["publishedDate"] = books_data["publishedDate"].str.extract(r"(^-?\d{,4})")
    books_data["publishedDate"] = books_data["publishedDate"].astype('int')

    books_data["publisher"] = pd.Categorical(books_data["publisher"])
    books_data["categories"] = pd.Categorical(books_data["categories"])
    books_data = books_data.where(pd.notnull(books_data), None)
    # books_data = books_data.dropna(axis=0)

    return books_data

if __name__ == "__main__":

    books_data = read_books_data()
    print(books_data["categories"])
    # print(books_data.isna().sum())
    # print(books_data["publishedDate"].min(),books_data["publishedDate"].max())
    # print(books_data.dtypes)
    # print()
    # print(books_data["Title"].iloc[115:125])
    # print(books_data[books_data["Title"]=="World in Eclipse"])
