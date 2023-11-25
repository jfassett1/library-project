import MySQLdb
import populate_books
from faker import Faker
from db_connect import get_cursor
from collections import Counter
# from django.contrib.auth.models import User


#List of tables generated
list_of_tables = [
    "patron",
    "publisher",
    "bookdata",
    "category",
    "book",
    "author",
    "checkout",
    "waitlist",
    "distance",
    "elevator"
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
CREATE TABLE publisher (
    PublisherID INT AUTO_INCREMENT PRIMARY KEY,
    PublisherName VARCHAR(50) UNIQUE
);""")

queries.append("""
CREATE TABLE bookdata (
	BookID INT PRIMARY KEY AUTO_INCREMENT,
	Title VARCHAR(255) NOT NULL,
	PublishDate INT,
	PublisherID INT REFERENCES publisher(PublisherID),
	Description TEXT,
    FULLTEXT idx (Title, Description)
) Engine = InnoDB;""")
queries.append("""
CREATE TABLE category (
    BookID INT REFERENCES bookdata(BookID),
    CategoryName VARCHAR(200) DEFAULT 'UNKNOWN',
    PRIMARY KEY (BookID, CategoryName)
);""")
queries.append("""
CREATE TABLE book (
    DecimalCode VARCHAR(15) PRIMARY KEY,
    BookID INT REFERENCES bookdata(BookID),
    Status TINYINT NOT NULL
);""")
#Had to up Name length because of books written by long names by US agencies
queries.append("""
CREATE TABLE author (
    BookID INT REFERENCES bookdata(BookID),
    Name VARCHAR(200) DEFAULT 'UNKNOWN',
    PRIMARY KEY (BookID, Name)
);""")
queries.append(
"""CREATE TABLE checkout (
    Patron INT REFERENCES patron(AccID),
    DecimalCode VARCHAR(15) REFERENCES book(DecimalCode),
    TimeOut DATETIME NOT NULL,
    Due DATE NOT NULL,
    PRIMARY KEY (Patron, DecimalCode, TimeOut)
);""")
queries.append("""CREATE TABLE waitlist (
    ListID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Patron INT REFERENCES patron(AccID),
    BookID VARCHAR(20) REFERENCES book(BookID)
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


def initialize():
    #Initializing tables
    create_table(queries)
    #Building Patron accounts
    # n_patrons = int(input("How many people do you want?\n"))

    # TODO: #7 recieve error about incorrect django settings if attempt to run
    # create django login data
    # for name, address, email in values:
    #     user, _ = email.split("@")
    #     User.objects.create_user(user, email, user)

    # read and insert book data
    books_data = populate_books.read_books_data(10_000)
    books = populate_books.generate_shelf_decimal(books_data)
    books_data = books.join(books_data, on="BookID", how="inner")
    books_data.sort_values(by='Title',inplace=True)

    insert("publisher", "PublisherName", populate_books.extract_categorical_book_data(books_data, "publisher"))
    insert("bookdata","Title, PublishDate, PublisherID, CategoryID, Description", populate_books.create_book_data(books_data))
    insert("author","BookID, Name",populate_books.format_combined_data(books_data, "authors")," ON DUPLICATE KEY UPDATE BookID = Values(BookID),Name = Values(Name)")
    insert("category","BookID, CategoryName", populate_books.format_combined_data(books_data, "categories"), " ON DUPLICATE KEY UPDATE BookID = Values(BookID),CategoryName = Values(CategoryName)")
    # insert("book","DecimalCode, BookID, Status", populate_books.generate_library(books_data))
    insert("book","DecimalCode, BookID, Status", populate_books.books_to_tuples(books))
    fake = Faker()
    n_patrons = 100
    print(f"Building {n_patrons} patron accounts")
    values = tuple(
        zip([fake.name() for _ in range(n_patrons)],
            [fake.address() for _ in range(n_patrons)],
            [fake.unique.email() for _ in range(n_patrons)]))
    insert("patron","Name, Address, Email",values)
#Main
if __name__ == "__main__":
    initialize()