import pandas as pd
import pathlib
import os

# def create_bookdata(books:pd.DataFrame):

#     return tuple(
#         zip(
#             books["isbn13"].astype(int),
#             books["original_title"],
#             books["original_publication_year"].astype(int),
#             repeat("Filler")
#         )
#     )

def create_publisher_data(book_data:pd.DataFrame):
    publishers = book_data["publisher"].unique()
    return tuple(zip( pd.Categorical(publishers).codes, publishers))

def create_book_data(book_data:pd.DataFrame):
    return tuple(
        zip(
            book_data["Title"],
            book_data["publishedDate"],
            pd.Categorical(book_data["publisher"]).codes,
            book_data["description"]
        )
    )

def create_author_data(book_data:pd.DataFrame):
    # TODO: #6 Insert author data into a table
    return books_data

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
            "Title":lambda x: auto_truncate(x, 255)
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
    print(books_data.isna().sum())
    print(books_data["publishedDate"].min(),books_data["publishedDate"].max())
    print(books_data.dtypes)
    print()
    # print(books_data["Title"].iloc[115:125])
    # print(books_data[books_data["Title"]=="World in Eclipse"])
