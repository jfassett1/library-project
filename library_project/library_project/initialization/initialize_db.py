import MySQLdb
import pandas as pd
import populate_books
from faker import Faker
from db_connect import get_cursor
from collections import Counter
# from django.contrib.auth.models import User


#List of tables generated
list_of_tables = [
    "patron",
    "bookdata",
    "author",
    "category",
    "book",
    "checkout",
    "waitlist",
    "distance",
    "elevator",
]
list_of_views = [
    "combined_bookdata"
]

#Creating tables
queries = []
#TODO: make accID their username instead of an integer
queries.append("""
CREATE TABLE patron (
    AccID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Address VARCHAR(100) NOT NULL,
    Email VARCHAR(40) NOT NULL
);""")
queries.append("""
CREATE TABLE bookdata (
	BookID INT PRIMARY KEY AUTO_INCREMENT,
	Title VARCHAR(255) NOT NULL,
	PublishDate INT,
	Publisher VARCHAR(50),
	Description TEXT,
    FULLTEXT idx (Title, Description)
) Engine = InnoDB;""")
queries.append("""
CREATE TABLE author (
    BookID INT REFERENCES bookdata(BookID),
    Name VARCHAR(200) DEFAULT 'UNKNOWN',
    PRIMARY KEY (BookID, Name)
);""")
queries.append("""
CREATE TABLE category (
    BookID INT REFERENCES bookdata(BookID),
    CategoryName VARCHAR(200) DEFAULT 'UNKNOWN',
    PRIMARY KEY (BookID, CategoryName)
);""")
queries.append("""
CREATE TABLE book (
    DecimalCode VARCHAR(25) PRIMARY KEY,
    BookID INT REFERENCES bookdata(BookID),
    Status TINYINT NOT NULL
);""")
#Had to up Name length because of books written by long names by US agencies

queries.append(
"""CREATE TABLE checkout (
    Patron INT REFERENCES patron(AccID),
    DecimalCode VARCHAR(25) REFERENCES book(DecimalCode),
    TimeOut DATETIME NOT NULL,
    Due DATE NOT NULL,
    PRIMARY KEY (Patron, DecimalCode, TimeOut)
);""")
queries.append("""CREATE TABLE waitlist (
    ListID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Patron INT REFERENCES patron(AccID),
    BookID INT REFERENCES bookdata(BookID)
);""")
queries.append("CREATE TABLE distance (Floor INT, Shelf1 INT NOT NULL, Shelf2 INT NOT NULL, Dist FLOAT NOT NULL, PRIMARY KEY (Shelf1, Shelf2));")
queries.append("CREATE TABLE elevator (ID CHAR(8) NOT NULL, Floor INT NOT NULL, Wait TIME NOT NULL, PRIMARY KEY (ID, Floor));")


def create_table(queries):

    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        for table,tablename in zip(queries,list_of_tables):
            print(f"Creating table {tablename}")
            try:
                cursor.execute(table)
            except MySQLdb.Error as e:
                print(e)
            else:
                print("Created Succesfully!")
        # Execute the query for each set of values in the list
        conn.commit()


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
        SELECT * FROM bookdata;
        """
        try:
            cursor.execute(query)
        except MySQLdb.Error as e:
            print(e)

    return pd.DataFrame(cursor.fetchall(), columns=[
            "BookID",
            "Title",
            "PublishDate",
            "Publisher",
            "Description",
            ]).set_index("Title")


def create_view():

    query = """
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
    with MySQLdb.connect("db") as conn:

        cursor = get_cursor(conn)

        try:
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            print("Error:", e)
            conn.rollback()

def initialize():

    create_table(queries)
    create_view()

    books_data = populate_books.read_books_data()
    insert("bookdata",
           "Title, PublishDate, Publisher, Description",
           populate_books.books_to_tuples(books_data[["BookID","Title", "publishedDate", "publisher", "description"]].drop_duplicates(subset="BookID")[["Title", "publishedDate", "publisher", "description"]]))

    # extract and merge book data with correct book id
    data = books_data[["Title", "publishedDate", "publisher", "description", "DecimalCode", "BookStatus", "authors", "categories"]]
    books = populate_books.merge(get_book_ids(), data, False, "Title").drop_duplicates(subset="DecimalCode")

    # insert books
    insert("book","DecimalCode, BookID, Status", populate_books.books_to_tuples(books[["DecimalCode", "BookID", "BookStatus"]]))
    # insert authors
    insert("author","BookID, Name",populate_books.format_combined_data(books, "authors")," ON DUPLICATE KEY UPDATE BookID = Values(BookID),Name = Values(Name)")
    # insert categories
    insert("category","BookID, CategoryName", populate_books.format_combined_data(books, "categories"), " ON DUPLICATE KEY UPDATE BookID = Values(BookID),CategoryName = Values(CategoryName)")

    # Create 100 fake patrons
    fake = Faker()
    n_patrons = 100
    print(f"Building {n_patrons} patron accounts")
    values = tuple(
        zip([fake.name() for _ in range(n_patrons)],
            [fake.address() for _ in range(n_patrons)],
            [fake.unique.email() for _ in range(n_patrons)]))
    insert("patron","Name, Address, Email",values)


#     # TODO: #7 recieve error about incorrect django settings if attempt to run
#     # create django login data
#     # for name, address, email in values:
#     #     user, _ = email.split("@")
#     #     User.objects.create_user(user, email, user)

# #Main
if __name__ == "__main__":
    initialize()