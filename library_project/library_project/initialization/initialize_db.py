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

# from django.contrib.auth.models import User


triggers = {
    # change book status to out of stock if checked out by someone
    "update_book_status_checkout": """
    CREATE TRIGGER update_book_status_checkout
    BEFORE INSERT ON checkout
    FOR EACH ROW
    BEGIN
        DECLARE new_status INT;
        DECLARE decimal_code_to_update VARCHAR(25);

        SET new_status = NEW.Status;

        SET decimal_code_to_update = (
            SELECT MIN(b.DecimalCode) FROM book b WHERE b.BookID = NEW.BookID AND b.Status = 0
        );

        IF new_status = 0 THEN
            SET NEW.DecimalCode = decimal_code_to_update;
            UPDATE book SET Status = 1 WHERE DecimalCode = decimal_code_to_update;
        END IF;
    END
    """,
    # update book status when book is returned in checkout
    "update_book_status_return": """
    CREATE TRIGGER update_book_status_return
    AFTER UPDATE ON checkout
    FOR EACH ROW
    BEGIN
        IF NEW.Status = 2 THEN
            UPDATE book SET Status = 0 WHERE DecimalCode = NEW.DecimalCode;
        END IF;
    END;
    """,
    # change all book copy status to reserved if
    # someone is added to waitlist for the book
    "update_book_status_waitlist": """
    CREATE TRIGGER update_book_status_waitlist
    AFTER INSERT ON waitlist
    FOR EACH ROW
    BEGIN
        UPDATE book SET book.Status = 2 WHERE book.BookID = NEW.BookID;
    END;
    """
}
procedures = {
    # call when a book is returned (checkout.status = 2)
    # move first person from waitlist to checkout
    # set checkout status to on hold (3)
    # put book on hold for 3 days
    # delete person from waitlist
    'move_to_hold_from_waitlist':"""
CREATE PROCEDURE move_to_hold_from_waitlist(IN decimal_code_value INT)
BEGIN
    DECLARE patron_id_var INT;
    DECLARE waitlist_id_var INT;
    DECLARE due_date_var DATE;
    DECLARE book_id_var INT;

    SET book_id_var = (SELECT BookID FROM checkout WHERE DecimalCode = decimal_code_value);

    SELECT Patron, ListID INTO patron_id_var, waitlist_id_var
    FROM waitlist
    WHERE BookID = book_id_var
    ORDER BY ListID
    LIMIT 1;

    IF patron_id_var IS NOT NULL THEN
        SET due_date_var = DATE_ADD(CURDATE(), INTERVAL 3 DAY);


        INSERT INTO checkout (Patron, BookID, DecimalCode, Due, Status)
        VALUES (patron_id_var, book_id_var, decimal_code_value, due_date_var, 3);

        UPDATE book SET Status = 2 WHERE BookID = book_id_var;

        DELETE FROM waitlist WHERE ListID = waitlist_id_var;
    END IF;
END
"""
}
#Creating tables
tables = {
'patron': """
CREATE TABLE patron (
    AccID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Address VARCHAR(100) NOT NULL,
    Email VARCHAR(40) NOT NULL
);""",
'bookdata': """
CREATE TABLE bookdata (
	BookID INT PRIMARY KEY AUTO_INCREMENT,
	Title VARCHAR(255) NOT NULL,
	PublishDate INT,
	Publisher VARCHAR(50),
	Description TEXT,
    FULLTEXT idx (Title, Description)
) Engine = InnoDB;""",
'author': """
CREATE TABLE author (
    BookID INT REFERENCES bookdata(BookID),
    Name VARCHAR(200) DEFAULT 'UNKNOWN',
    PRIMARY KEY (BookID, Name)
);""",
'category': """
CREATE TABLE category (
    BookID INT REFERENCES bookdata(BookID),
    CategoryName VARCHAR(500) DEFAULT 'UNKNOWN',
    PRIMARY KEY (BookID, CategoryName)
);""",
'book': """
CREATE TABLE book (
    DecimalCode VARCHAR(25) PRIMARY KEY,
    BookID INT REFERENCES bookdata(BookID),
    Status TINYINT NOT NULL
);""",
'checkout': """
CREATE TABLE checkout (
    Patron VARCHAR(150) REFERENCES auth_user(username),
    DecimalCode VARCHAR(25) REFERENCES book(DecimalCode),
    BookID VARCHAR(25) REFERENCES bookdata(BookID),
    TimeOut DATETIME DEFAULT CURRENT_TIMESTAMP,
    Due DATE DEFAULT (CURRENT_DATE + INTERVAL 2 WEEK),
    Status TINYINT NOT NULL,
    PRIMARY KEY (DecimalCode, TimeOut)
);""",
'waitlist': """
CREATE TABLE waitlist (
    ListID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Patron VARCHAR(150) REFERENCES auth_user(username),
    BookID INT REFERENCES bookdata(BookID)
);"""
}

views = {
'combined_bookdata':"""
CREATE VIEW combined_bookdata AS
SELECT
    bd.BookID,
    bd.Title,
    bd.PublishDate,
    bd.Publisher,
    bd.Description,
    b.DecimalCode,
    b.Status
FROM
    book b
    INNER JOIN bookdata bd ON bd.BookID = b.BookID;
"""
}

scheduled_events = {
'mark_overdue_books':"""
CREATE EVENT mark_overdue_books
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
    UPDATE checkout c
    SET c.Status = 1
    WHERE c.Due < CURRENT_DATE;
END;

"""
}
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
    title_to_vec = Doc2Vec.load("../recommendation/d2v.model")
    print("creating title vectors")
    book_vecs = []
    for book in books["Title"]:
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
    books_data = populate_books.read_books_data(50_000)
    insert("bookdata",
           "Title, PublishDate, Publisher, Description",
           populate_books.books_to_tuples(books_data[["BookID","Title", "publishedDate", "publisher", "description"]].drop_duplicates(subset="BookID")[["Title", "publishedDate", "publisher", "description"]]))

    # extract and merge book data with correct book id
    data = books_data[
        [
            "Title",
            "publishedDate",
            "publisher",
            "description",
            "DecimalCode",
            "BookStatus",
            "authors",
            "categories"
        ]
    ].set_index("Title")

    # books = pd.merge(get_book_ids(), data, "inner", left_on="Title", right_index=True)
    updated_ids = get_book_ids()

    books = populate_books.merge(
        updated_ids, data, False, "Title"
    ).drop_duplicates(subset="DecimalCode") # idk why this is required but it breaks without it
    books = books[books["BookID"]!=1]

    # insert books
    insert("book","DecimalCode, BookID, Status", populate_books.books_to_tuples(books[["DecimalCode", "BookID", "BookStatus"]]))
    # insert authors
    books.reset_index()
    books = books.set_index("BookID")
    authors = populate_books.format_combined_data_df(books, "authors")
    insert("author","BookID, Name",populate_books.books_to_tuples(authors, True)," ON DUPLICATE KEY UPDATE BookID = Values(BookID),Name = Values(Name)")
    # insert categories
    categories = populate_books.format_combined_data_df(books, "categories")
    insert("category","BookID, CategoryName", populate_books.books_to_tuples(categories, True), " ON DUPLICATE KEY UPDATE BookID = Values(BookID),CategoryName = Values(CategoryName)")

    # Create 100 fake patrons
    fake = Faker()
    n_patrons = 1000
    print(f"Building {n_patrons} patron accounts")
    values = tuple(
        zip([fake.name() for _ in range(n_patrons)],
            [fake.address() for _ in range(n_patrons)],
            [fake.unique.email() for _ in range(n_patrons)]))



    insert("patron","Name, Address, Email",values)
    train_knn(updated_ids)



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
                print("Data removed successfully!")

def refresh_all():
    for kind in ("VIEW", "TRIGGER", "EVENT", "TABLE",):
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