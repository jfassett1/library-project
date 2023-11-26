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


triggers = triggers = {
    "update_book_status_checkout": """
    CREATE TRIGGER update_book_status_checkout
    AFTER INSERT ON checkout
    FOR EACH ROW
    BEGIN
        IF NEW.Status = 0 THEN
            UPDATE book SET Status = 1 WHERE DecimalCode = NEW.DecimalCode;
        ELSIF NEW.Status = 2 THEN
            UPDATE book SET Status = 0 WHERE DecimalCode = NEW.DecimalCode;
        END IF;
    END;
    """,

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

    "update_book_status_waitlist": """
    CREATE TRIGGER update_book_status_waitlist
    AFTER INSERT ON waitlist
    FOR EACH ROW
    BEGIN
        UPDATE book SET book.Status = 2 WHERE DecimalCode IN (
            SELECT book.DecimalCode FROM book
            WHERE book.BookID = NEW.BookID
            AND book.Status = 1
            ORDER BY book.DecimalCode
            LIMIT 1
        );
    END;
    """,

    "update_book_availability": """
    CREATE TRIGGER update_book_availability
    AFTER UPDATE ON book
    FOR EACH ROW
    BEGIN
        IF NEW.Status = 0 THEN
            DECLARE patron_id INT;
            DECLARE checkout_time DATETIME;
            DECLARE due_date DATE;

            SELECT Patron, TimeOut INTO patron_id, checkout_time
            FROM checkout
            WHERE DecimalCode = NEW.DecimalCode AND Status = 3
            LIMIT 1;

            IF patron_id IS NOT NULL THEN
                SET due_date = DATE_ADD(CURDATE(), INTERVAL 3 DAY);

                INSERT INTO checkout (Patron, DecimalCode, TimeOut, Due, Status)
                VALUES (patron_id, NEW.DecimalCode, checkout_time, due_date, 3);

                -- Remove user from waitlist
                DELETE FROM waitlist WHERE BookID = NEW.BookID LIMIT 1;
            END IF;
        END IF;
    END;
    """
}
list_of_triggers = list(triggers.keys())
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
    CategoryName VARCHAR(500) DEFAULT 'UNKNOWN',
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
    Patron VARCHAR(150) REFERENCES auth_user(username),
    DecimalCode VARCHAR(25) REFERENCES book(DecimalCode),
    TimeOut DATETIME DEFAULT CURRENT_TIMESTAMP,
    Due DATE DEFAULT (CURRENT_DATE + INTERVAL 2 WEEK),
    Status TINYINT NOT NULL,
    PRIMARY KEY (DecimalCode, TimeOut)
);""")
queries.append("""CREATE TABLE waitlist (
    ListID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Patron INT REFERENCES patron(AccID),
    BookID INT REFERENCES bookdata(BookID)
);""")
queries.append("CREATE TABLE distance (Floor INT, Shelf1 INT NOT NULL, Shelf2 INT NOT NULL, Dist FLOAT NOT NULL, PRIMARY KEY (Shelf1, Shelf2));")
queries.append("CREATE TABLE elevator (ID CHAR(8) NOT NULL, Floor INT NOT NULL, Wait TIME NOT NULL, PRIMARY KEY (ID, Floor));")

queries.append("""CREATE TABLE bookshelf (
    BookshelfID INT PRIMARY KEY,
    Category VARCHAR(200),
    Slots INT,
);""")


def create_table(queries):

    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)

        try:
            cursor.execute("DELIMITER //")
        except MySQLdb.Error as e:
            print(e)
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
            print("Creating view")
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            print("Error:", e)
            conn.rollback()




def create_trigger():

    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        for trigger_name, trigger, in triggers.items():
            print(f"Creating trigger {trigger_name}")
            try:
                cursor.execute(trigger)
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
        SELECT bd.BookID, bd.Title FROM bookdata bd ORDER BY bd.BookID;
        """
        try:
            cursor.execute(query)
        except MySQLdb.Error as e:
            print(e)

    return pd.DataFrame(cursor.fetchall(), columns=[
            "BookID",
            "Title"
            ]).set_index("Title")



def initialize():

    create_table(queries)
    create_view()
    create_trigger()

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

    books = populate_books.merge(
        get_book_ids(), data, False, "Title"
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


#     # TODO: #7 recieve error about incorrect django settings if attempt to run
#     # create django login data
#     # for name, address, email in values:
#     #     user, _ = email.split("@")
#     #     User.objects.create_user(user, email, user)

# #Main
if __name__ == "__main__":
    initialize()