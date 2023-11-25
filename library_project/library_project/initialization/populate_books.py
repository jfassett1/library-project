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
def extract_categorical_book_data(book_data:pd.DataFrame, column_name:str):
    """Get codes for a categorical feature

    Args:
        book_data (pd.DataFrame): Book data frame
        column_name (str): name of column to extract

    Returns:
        tuple: tuple of tuples of category code and category name
    """
    data = book_data[column_name].unique()
    print("total len",len(data), "unique len",len(set(data)))
    return tuple([(d,) for d in data])



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
    books_data["categories"].replace("",'["Misc"]',inplace=True)
    books_data["authors"].fillna('["UNKNOWN"]',inplace=True)



    books_data["publisher"] = pd.Categorical(books_data["publisher"])
    # books_data["categories"] = pd.Categorical(books_data["categories"])
    books_data = books_data.where(pd.notnull(books_data), None)
    books_data["ratingsCount"] = books_data["ratingsCount"].fillna(0)
    # books_data = books_data.dropna(axis=0)
    #drops first row

    books_data.sort_values(by='Title',inplace=True)
    # books_data = books_data.iloc[1:, :]

    # books_data = books_data.dropna(axis=0)

    return books_data


#Start of decimal generation

class Bookshelf:
    def __init__(self,ind:int=0,category:str = 'Misc'):
        self.category = category
        self.bookshelfID = ind
        self.full = False
        self.subshelves = {
            '01': [],
            '02': [],
            '03': [],
            '04': [],
            '05': [],
            '06': [],
            '07': [],
        }
    def append(self, bookID):
        for _, books in filter(lambda x: len(x[1])<30, self.subshelves.items()):
            books.append(bookID)
            break
        else:
            self.full = True
            return "Full"

    def read(self):
        print(f"Bookshelf: {self.bookshelfID}\nCategory: {self.category}")
        for shelf in self.subshelves.values():
            print(shelf)

    def index(self):
        finallist = []
        b_id = f"{self.bookshelfID:03d}"
        for subshelf,books in self.subshelves.items():
            for book_id in books:
                finallist.append((f"{b_id}.{subshelf}.{book_id}",book_id,0))
        return finallist


def populate_bookshelves(books, startint=1,category:str='Misc'):
    """Builds bookshelf data
    Args: iterable of bookIDs

    Returns: List of bookshelf objects
    """
    bookshelves = [Bookshelf(startint,category)]
    next_bookshelf_id = startint + 1
    for id in books:
        book_added = False
        for bookshelf in bookshelves:
            result = bookshelf.append(id)
            if result is None:
                book_added = True
                break

        if not book_added:
            # If all bookshelves are full, create a new bookshelf
            new_bookshelf = Bookshelf(next_bookshelf_id)
            new_bookshelf.category = category
            bookshelves.append(new_bookshelf)
            new_bookshelf.append(id)  # Add the book to the new bookshelf
            # print(f"Created Bookshelf{len(bookshelves)} for book {i}")
            next_bookshelf_id += 1

    return bookshelves

def generate_shelf_decimal(books_data:pd.DataFrame) -> pd.DataFrame:
    def append_period_and_copy_number(group):
        group["newDecimalCode"] =  group["DecimalCode"] + "." + group.groupby("BookID").cumcount().astype(str)
        return group
    sample = books_data.groupby("categories", observed=False).sample(frac=0.2, replace=True, weights=np.log10(books_data["ratingsCount"]+2))["categories"]

    # print(sample.head())
    sample.sort_index(inplace=True)
    grouped = sample.groupby(sample, observed=False)
    library = []
    misc_cats = []

    for cat, group in grouped:
        if len(group) <= 200:
            misc_cats.append(cat)
        else:
            library.extend(populate_bookshelves(group.index,startint=len(library)+1,category=cat))

    last_int = library[-1].bookshelfID

    misc = sample.isin(misc_cats)
    library.extend(populate_bookshelves(misc.index,startint=last_int,category="Misc",))


    indices = []
    for bookshelf in library:
        indices.extend(bookshelf.index())
    print(f"Generating {len(library)} bookshelves containing {len(indices)} books")

    data = pd.DataFrame(indices, columns=["DecimalCode","BookID", "BookStatus"])
    data =  data.groupby("BookID").apply(append_period_and_copy_number).loc[:,["newDecimalCode", "BookID", "BookStatus"]]
    data.drop(columns=["BookID"],inplace=True)
    data = data.rename({"newDecimalCode":"DecimalCode"}, axis=1)
    data = data.reset_index()
    data.drop(columns=["level_1"],inplace=True)

    return data[["DecimalCode", "BookID", "BookStatus"]]

def books_to_tuples(books):
    return tuple(books.itertuples(False, None))

if __name__ == "__main__":

    books_data = read_books_data(10_000)
    books = generate_shelf_decimal(books_data)
    print(books[:30])
    # print(books_data.head())
    # print(generate_library(books_data))
    # print(books_data["categories"])
    # print(books_data.isna().sum())
    # print(books_data["publishedDate"].min(),books_data["publishedDate"].max())
    # print(books_data.dtypes)
    # print(create_book_data(books_data)[:30])

    # print(books_data["Title"].iloc[115:125])
    # print(books_data[books_data["Title"]=="World in Eclipse"])
