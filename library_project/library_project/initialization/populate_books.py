import warnings
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
            book_data["publisher"],
            book_data["description"]
        )
    )

def format_author_data(book_data:pd.DataFrame):
    """formats author data

    Args:
        book_data (pd.Dataframe): Book info dataframe with 'authors' column

    Returns:
        tuple: Authors & BookIDs


    """
    authors = book_data[["authors"]].copy()
    #Changes index to default incremental
    authors.reset_index(inplace=True)
    authors.index +=1

    #Turns string representations of list into actual list
    authors['authors'] = authors['authors'].apply(lambda x: eval(x))
    #Creates duplicate rows for each author of a book, keeps proper index
    exploded_authors = authors.explode("authors")
    return tuple(zip(
        exploded_authors.index,
        exploded_authors['authors']
    ))

def format_combined_data(book_data:pd.DataFrame, column):
    """formats author data

    Args:
        book_data (pd.Dataframe): Book info dataframe with column 'column'

    Returns:
        tuple: Authors & BookIDs


    """
    col_data = book_data[[column]].copy()
    #Changes index to default incremental
    col_data.reset_index(inplace=True)
    col_data.index +=1

    #Turns string representations of list into actual list
    col_data[column] = col_data[column].apply(lambda x: eval(x))
    #Creates duplicate rows for each author of a book, keeps proper index
    exploded_col = col_data.explode(column)
    return tuple(zip(
        exploded_col.index,
        exploded_col[column]
    ))

def format_combined_data_df(book_data:pd.DataFrame, column)->pd.DataFrame:
    """formats author data

    Args:
        book_data (pd.Dataframe): Book info dataframe with column column

    Returns:
        tuple: Authors & BookIDs


    """
    col_data = book_data.copy()

    #Turns string representations of list into actual list
    col_data[column] = col_data[column].apply(lambda x: eval(x))
    #Creates duplicate rows for each author of a book, keeps proper index
    # exploded_col =
    return col_data.explode(column)


def generate_shelf_decimal(books_data: pd.DataFrame) -> pd.DataFrame:

    def split_into_chunks(group, chunk_size: int, shelf_num: int):
        chunks = [group.iloc[i:i+chunk_size] for i in range(0, len(group), chunk_size)]
        for idx, c in enumerate(chunks):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                c.loc[:, "DecimalCode"] = f"{shelf_num+idx//7+1}.{idx%7}."+c["BookID"].astype(str)
        return shelf_num+len(chunks)//7+1, chunks

    def aggregate_groups(groups, chunk_size: int):
        result = []
        current_chunk = pd.DataFrame()

        for _, group in groups:
            if len(current_chunk) + len(group) <= chunk_size:
                current_chunk = pd.concat([current_chunk, group])
            else:
                result.append(current_chunk)
                current_chunk = group

        if not current_chunk.empty:
            result.append(current_chunk)

        return result

    print("Generating bookshelves...")

    library = pd.DataFrame()
    misc_cats = []
    shelf_num = 0
    for cat in books_data["categories"].unique():
        group = books_data.loc[books_data["categories"] == cat]
        if len(group) <= 200:
            misc_cats.append(cat)
        else:
            shelf_num, chunks = split_into_chunks(group, 30, shelf_num)
            library = pd.concat([library, *chunks])

    aggregated = aggregate_groups(books_data.isin(misc_cats).groupby("categories"), 200)

    for chunk in aggregated:
        shelf_num, chunks = split_into_chunks(chunk, 30, shelf_num)
        library = pd.concat([library, *chunks])

    library["DecimalCode"] = library["DecimalCode"] + "." + library.groupby("BookID").cumcount().astype(str)
    library["BookStatus"] = np.zeros(library.shape[0], dtype=np.int16)
    print(f"Generated {shelf_num} bookshelves containing {len(books_data)} books")
    return library[["DecimalCode","BookID", "BookStatus"]]


def books_to_tuples(books, index:bool=False):
    return tuple(books.itertuples(index, None))


def merge(df, df2, both_index = False, right_on="BookID"):
    cols_to_use = df2.columns.difference(df.columns)
    if both_index:
        return pd.merge(df, df2[cols_to_use], right_index=True, left_index=True, how='outer')
    else:
        return pd.merge(df, df2[cols_to_use], right_on=right_on, left_index=True, how='outer')

def read_books_data(nrows=None):
    parent_project_path = pathlib.Path(os.path.dirname(__file__)).parents[1]
    data_folder = parent_project_path/"data"
    books_data = pd.read_csv(
        data_folder/"books_data.csv",
        converters={
            "publisher":lambda x: auto_truncate(x, 50),
            "Title":lambda x: auto_truncate(x, 255),
            # "categories": lambda x: auto_truncate(x[2:-2], 255),
            },
        nrows=nrows
        )
    # remove duplicated titles
    books_data = books_data.drop_duplicates(subset = "Title")


    # fill missing values
    books_data["publisher"].replace("","UNKNOWN",inplace=True)
    books_data["categories"].fillna('["Misc"]',inplace=True)
    books_data["authors"].fillna('["UNKNOWN"]',inplace=True)
    books_data["description"].fillna('',inplace=True)
    books_data["publishedDate"] = books_data["publishedDate"].fillna("-9999")

    # parse publisher data
    books_data["publishedDate"] = books_data["publishedDate"].str.replace(r'\?', '0', regex=True)
    books_data["publishedDate"] = books_data["publishedDate"].str.extract(r"(^-?\d{,4})")
    books_data["publishedDate"] = books_data["publishedDate"].astype('int')

    # fill in remaining nulls with none
    books_data = books_data.where(pd.notnull(books_data), None)



    # create a sample of books weighted by number of reviews
    books_data["ratingsCount"] = np.log10(books_data["ratingsCount"].fillna(2))
    sample_data = books_data.sample(40_000, replace=True, weights=books_data["ratingsCount"])

    # add decimal numbers to sample data
    # sample_data = pd.merge(generate_shelf_decimal(sample_data[["BookID", "categories"]]), sample_data, how="inner", left_on="BookID", right_on="BookID")
    # this breaks stuff but in theory should work
    # sample_data = generate_shelf_decimal(sample_data)

    return sample_data[["Title", "publishedDate", "publisher", "description", "authors", "categories"]]


if __name__ == "__main__":

    books_data = read_books_data(10_000)
    # print(books_data.columns)
    # books = books_data[["BookID","Title", "publishedDate", "publisher", "description"]].drop_duplicates(subset="BookID")
    # print(len(books), len(books_data["BookID"].unique()))
    # print(books_data.head())
    # books = generate_shelf_decimal(books_data)
    # print(books[:30])
    # print(books_data.head())
    # print(generate_library(books_data))
    # print(books_data["categories"])
    # print(books_data.isna().sum())
    # print(books_data["publishedDate"].min(),books_data["publishedDate"].max())
    # print(books_data.dtypes)
    # print(create_book_data(books_data)[:30])

    # print(books_data["Title"].iloc[115:125])
    # print(books_data[books_data["Title"]=="World in Eclipse"])
