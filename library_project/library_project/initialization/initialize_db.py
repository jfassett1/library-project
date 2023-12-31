import math
import sys
import MySQLdb
import joblib
import numpy as np
import pandas as pd
import populate_books
from faker import Faker
from db_connect import get_cursor
from collections import Counter
import time
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.preprocessing import preprocess_documents
from sklearn.neighbors import NearestNeighbors
import tomllib

# from django.contrib.auth.models import User
def read_schema(sch_type:str)->dict[str,str]:
    with open(f"./schema/{sch_type}.toml", "rb") as f:
        return tomllib.load(f)

triggers = read_schema("triggers")
procedures  = read_schema("procedures")
tables = read_schema("tables")
views = read_schema("views")
scheduled_events = read_schema("scheduled_events")

#TODO: make accID their username instead of an integer

# queries.append("CREATE TABLE distance (Floor INT, Shelf1 INT NOT NULL, Shelf2 INT NOT NULL, Dist FLOAT NOT NULL, PRIMARY KEY (Shelf1, Shelf2));")
# queries.append("CREATE TABLE elevator (ID CHAR(8) NOT NULL, Floor INT NOT NULL, Wait TIME NOT NULL, PRIMARY KEY (ID, Floor));")
def create_mysql_object(objects:dict, kind:str):
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)

        for name, query in objects.items():
            print(f"Creating {kind} {name}")

            try:
                cursor.execute(query)
                print(f"Created {name} Succesfully!")
            except MySQLdb.Error as e:
                print("Error:", e)
                conn.rollback()
        conn.commit()

def create_table():
    create_mysql_object(tables, "table")

def create_view():
    create_mysql_object(views, "view")

def create_trigger():
    create_mysql_object(triggers, "trigger")

def create_scheduled_event():
    create_mysql_object(scheduled_events, "scheduled event")

def create_procedure():
    create_mysql_object(procedures, "procedure")


def insert(table:str, fields:str, values:tuple[tuple, ...]|tuple[str, ...],additional:str=""):

    with MySQLdb.connect("db") as conn:

        cursor = get_cursor(conn)
        if len(values[0]) > 1:
            placeholders = ', '.join(['%s'] * len(fields.split(',')))
            query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders}){additional}"
            print(query)
            try:
                cursor.executemany(query, values)
            except MySQLdb.Error as e:
                print(e)
                print(f"Data for {table} failed to insert!")
            else:
                # Execute the query for each set of values in the list
                print(f"Data for {table} inserted successfully!")
            conn.commit()


        elif len(values[0]) == 1:
            s = Counter([c[0] for c in values])
            print(s.most_common(5))

            query = f"INSERT INTO {table} ({fields}) VALUE (%s) {additional}"
            print(query)
            for v in values:
                try:
                    cursor.execute(query, v)
                except MySQLdb.Error as e:
                    print(e)
                    print(f"{v} failed to insert into {table}!")
                conn.commit()

def get_book_ids():
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        query = """
        SELECT bd.BookID, bd.Title FROM bookdata bd ORDER BY bd.BookID;
        """
        try:
            cursor.execute(query)
        except MySQLdb.Error as e:
            print(e)

    return pd.DataFrame(cursor.fetchall(), columns=[
            "BookID",
            "Title",
            ]).set_index("Title")

def train_knn(books:pd.DataFrame):
    books = books.reset_index()

    joblib.dump(books["Title"].to_dict(), "../recommendation/titlemap.pkl",)
    title_to_vec = Doc2Vec.load("../recommendation/d2v_titles.model")
    print("creating title vectors")
    book_vecs = []
    for i, book in enumerate(books["Title"]):
        if i+1 % 1000 == 0:
            print(f"Creating title vector {i}")

        book_vecs.append(title_to_vec.infer_vector(preprocess_documents([book])[0])) # type: ignore
    print("training title knn")
    book_vecs = np.array(book_vecs)
    neigh = NearestNeighbors(n_neighbors=5, metric='cosine')
    neigh.fit(book_vecs)
    joblib.dump(neigh, "../recommendation/neighbors.pkl")

    # print("creating description vectors")
    # book_vecs = []
    # for book in books["description"]:
    #     book_vecs.append(descriptions_to_vec.infer_vector(preprocess_documents([book])[0]))
    # book_vecs = np.array(book_vecs)
    # print("training description knn")
    # descriptions_to_vec = Doc2Vec.load("../recommendation/d2v_descriptions.model")
    # neigh = NearestNeighbors(n_neighbors=5, metric='cosine')
    # neigh.fit(book_vecs)
    # joblib.dump(neigh, "../recommendation/desc_neighbors.pkl")

def gen_insert_data():
    samples = 30_000
    books_data = populate_books.read_books_sample_no_replace(50_000, sample_size=samples)
    insert("bookdata",
           "Title, PublishDate, Publisher, Description",
        #    populate_books.books_to_tuples(books_data[["BookID","Title", "publishedDate", "publisher", "description"]].drop_duplicates(subset="BookID")[["Title", "publishedDate", "publisher", "description"]]))
           populate_books.books_to_tuples(books_data[["Title", "publishedDate", "publisher", "description"]]))

    # extract and merge book data with correct book id
    data = books_data[
        [
            "Title",
            "authors",
            "categories",
            "ratingsCount"
        ]
    ].set_index("Title")
    updated_ids = get_book_ids()
    books_data = pd.merge(updated_ids, data, how='inner', right_index=True, left_index=True)



    authors = populate_books.format_combined_data_df(books_data, "authors")
    authors = authors[["BookID", "authors"]]
    authors.set_index("BookID", inplace=True)
    # authors = populate_books.format_combined_data_df(books_without_dupes, "authors")
    insert(
        "author",
        "BookID, Name",
        populate_books.books_to_tuples(pd.DataFrame(authors["authors"]), True),
        " ON DUPLICATE KEY UPDATE BookID = Values(BookID),Name = Values(Name)"
    )
    # insert categories
    categories = populate_books.format_combined_data_df(
        books_data, "categories"
        )
    categories.set_index("BookID", inplace=True)

    categories = pd.DataFrame(categories["categories"].apply(
            lambda x: populate_books.auto_truncate(x, 500)
        ))
    insert(

        "category",
        "BookID, CategoryName",
        populate_books.books_to_tuples(categories, True),
        # " ON DUPLICATE KEY UPDATE BookID = Values(BookID),Name = Values(Name)"
    )
    books = populate_books.add_replacement_sample(books_data, sample_size=2*samples)
    books = populate_books.generate_shelf_decimal(books)
    # insert books
    insert("book","DecimalCode, BookID, Status", populate_books.books_to_tuples(books[["DecimalCode", "BookID", "BookStatus"]]))

    # Create 100 fake patrons
    fake = Faker()
    n_patrons = 1000
    print(f"Building {n_patrons} patron accounts")
    values = tuple(
        zip([fake.name() for _ in range(n_patrons)],
            [fake.address() for _ in range(n_patrons)],
            [fake.unique.email() for _ in range(n_patrons)]))



    insert("patron","Name, Address, Email",values)
    train_knn(books_data)



def initialize():

    create_table()
    create_view()
    create_trigger()
    create_procedure()
    create_scheduled_event()
    gen_insert_data()



#     # TODO: #7 recieve error about incorrect django settings if attempt to run
#     # create django login data
#     # for name, address, email in values:
#     #     user, _ = email.split("@")
#     #     User.objects.create_user(user, email, user)
def refresh(which:str="TABLE"):
    names = []
    db_name="library"
    match which:
        case "TABLE":
            names = list(tables.keys())
        case "VIEW":
            names = list(views.keys())
        case "TRIGGER":
            names = list(triggers.keys())
        case "EVENT":
            names = list(scheduled_events.keys())
        case "PROCEDURE":
            names = list(procedures.keys())

    if not names:
        return

    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn, db_name)
        for name in names:
            print(f"Removing {name}")
            query = f"DROP {which} {name};"
            try:
                cursor.execute(query)
            except MySQLdb.Error as e:
                print(f"Error: {e}")
            else:
                print(f"{which} removed successfully!")

def refresh_all():
    for kind in ("VIEW", "TRIGGER", "EVENT", "TABLE","PROCEDURE"):
        refresh(kind)


# #Main
if __name__ == "__main__":
    start_time = time.time()
    if len(sys.argv) == 1:
        refresh_all()
        initialize()

    if "table" in sys.argv:
        refresh("TABLE")
        create_table()
        gen_insert_data()

    if "trigger" in sys.argv:
        refresh("TRIGGER")
        create_trigger()

    if "view" in sys.argv:
        refresh("VIEW")
        create_view()

    if "event" in sys.argv:
        refresh("EVENT")
        create_scheduled_event()

    if "procedure" in sys.argv:
        refresh("PROCEDURE")
        create_procedure()

    end_time = time.time()-start_time
    print(f"It took {end_time:.2f} seconds to initialize")