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
        book_data (pd.Dataframe): Book info dataframe with column column

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
    col_data = book_data[[column]].copy()

    #Turns string representations of list into actual list
    col_data[column] = col_data[column].apply(lambda x: eval(x))
    #Creates duplicate rows for each author of a book, keeps proper index
    # exploded_col =
    return col_data.explode(column)


# #Start of decimal generation

# class Bookshelf:
#     def __init__(self,ind:int=0,category:str = 'Misc'):
#         self.category = category
#         self.bookshelfID = ind
#         self.full = False
#         self.subshelves = {
#             '01': [],
#             '02': [],
#             '03': [],
#             '04': [],
#             '05': [],
#             '06': [],
#             '07': [],
#         }
#     def append(self, bookID):
#         for _, books in filter(lambda x: len(x[1])<30, self.subshelves.items()):
#             books.append(bookID)
#             break
#         else:
#             self.full = True
#             return "Full"

#     def read(self):
#         print(f"Bookshelf: {self.bookshelfID}\nCategory: {self.category}")
#         for shelf in self.subshelves.values():
#             print(shelf)

#     def index(self):
#         finallist = []
#         b_id = f"{self.bookshelfID:03d}"
#         for subshelf,books in self.subshelves.items():
#             for book_id in books:
#                 finallist.append((f"{b_id}.{subshelf}.{book_id}",book_id,0))
#         return finallist


# def populate_bookshelves(books, startint=1,category:str='Misc'):
#     """Builds bookshelf data
#     Args: iterable of bookIDs

#     Returns: List of bookshelf objects
#     """
#     bookshelves = [Bookshelf(startint,category)]
#     next_bookshelf_id = startint + 1
#     for id in books:
#         book_added = False
#         for bookshelf in bookshelves:
#             result = bookshelf.append(id)
#             if result is None:
#                 book_added = True
#                 break

#         if not book_added:
#             # If all bookshelves are full, create a new bookshelf
#             new_bookshelf = Bookshelf(next_bookshelf_id)
#             new_bookshelf.category = category
#             bookshelves.append(new_bookshelf)
#             new_bookshelf.append(id)  # Add the book to the new bookshelf
#             # print(f"Created Bookshelf{len(bookshelves)} for book {i}")
#             next_bookshelf_id += 1

#     return bookshelves


def generate_shelf_decimal(books_data: pd.DataFrame) -> pd.DataFrame:

    def split_into_chunks(group, chunk_size: int, shelf_num: int):
        chunks = [group.iloc[i:i+chunk_size] for i in range(0, len(group), chunk_size)]
        for idx, c in enumerate(chunks):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                c.loc[:, "DecimalCode"] = f"{shelf_num+idx//7+1:3d}.{idx%7}."+c["BookID"].astype(str)
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
    library["BookStatus"] = np.zeros(library.shape[0])
    print(f"Generated {shelf_num} bookshelves containing {len(books_data)} books")
    return library[["DecimalCode", "BookID", "BookStatus"]]
    # for cat, group in grouped:
    #     if len(group) <= 200:
    #         misc_cats.append(cat)
    #     else:
    #         library.extend(populate_bookshelves(group.index,startint=len(library)+1,category=cat))

    # last_int = library[-1].bookshelfID if library else 0

    # misc = books_data["categories"].isin(misc_cats)
    # library.extend(populate_bookshelves(misc.index,startint=last_int,category="Misc",))




    # data = pd.DataFrame(indices, columns=["DecimalCode","BookID", "BookStatus"])
    # data =  data.groupby("BookID").apply(append_period_and_copy_number).loc[:,["newDecimalCode", "BookID", "BookStatus"]]
    # data.drop(columns=["BookID"],inplace=True)
    # data = data.rename({"newDecimalCode":"DecimalCode"}, axis=1)
    # data = data.reset_index()
    # data.drop(columns=["level_1"],inplace=True)

    # return data[["DecimalCode", "BookID", "BookStatus"]]

def books_to_tuples(books):
    return tuple(books.itertuples(False, None))


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

    books_data = books_data.drop_duplicates(subset = "Title")
    books_data["publishedDate"] = books_data["publishedDate"].fillna("-9999")
    books_data["publishedDate"] = books_data["publishedDate"].str.replace(r'\?', '0', regex=True)
    books_data["publishedDate"] = books_data["publishedDate"].str.extract(r"(^-?\d{,4})")
    books_data["publishedDate"] = books_data["publishedDate"].astype('int')
    books_data["publisher"].replace("","UNKNOWN",inplace=True)
    books_data["categories"].fillna('["Misc"]',inplace=True)
    books_data["authors"].fillna('["UNKNOWN"]',inplace=True)
    books_data["description"].fillna('None given.',inplace=True)


    books_data["publisher"] = pd.Categorical(books_data["publisher"])
    # books_data["categories"] = pd.Categorical(books_data["categories"])
    books_data = books_data.where(pd.notnull(books_data), None)
    books_data["ratingsCount"] = np.log10(books_data["ratingsCount"].fillna(2))
    print(books_data.index)
    books_data["BookID"] = books_data.index
    sample_data = books_data.sample(frac=0.80, replace=True, weights=books_data["ratingsCount"])

    # print(sample_data.iloc[0])
    # idx = sample_data.iloc[0].name
    # print(books_data.loc[idx])

    sample_data = pd.merge(generate_shelf_decimal(sample_data), sample_data, how="inner", left_on="BookID", right_on="BookID")

    # print(sample_data.iloc[0])
    # books_data = merge(books_data, format_combined_data_df(books_data, "authors"), both_index=True)
    # books_data = merge(books_data,format_combined_data_df(books_data.drop_duplicates("BookID",keep='first'), "categories"), both_index=True)
    print(sample_data.isna().sum())
    return sample_data[["BookID","Title", "publishedDate", "publisher", "description", "authors", "categories", "DecimalCode", "BookStatus"]]


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
