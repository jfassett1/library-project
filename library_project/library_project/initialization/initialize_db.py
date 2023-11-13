import MySQLdb
import populate_books
from faker import Faker
from db_connect import get_cursor


#List of tables generated
list_of_tables = [
    "patron",
    "publisher",
    "bookdata",
    "book",
    "author",
    "categorynames",
    "bookcategory",
    "checkout",
    "distance",
    "elevator"
]

#Creating tables
queries = []
queries.append("CREATE TABLE patron (AccID INT AUTO_INCREMENT PRIMARY KEY, Name VARCHAR(50) NOT NULL, Address VARCHAR(100) NOT NULL, Email VARCHAR(40) NOT NULL);")
queries.append("""
CREATE TABLE publisher (
    PublisherID INT PRIMARY KEY,
    PublisherName VARCHAR(50)
);""")
queries.append("""
CREATE TABLE bookdata (
	BookID INT PRIMARY KEY AUTO_INCREMENT,
	Title VARCHAR(255) NOT NULL,
	PublishDate INT,
	Publisher INT REFERENCES publisher(PublisherID),
	Description TEXT
);""")
queries.append("CREATE TABLE book (DecimalCode CHAR(12) PRIMARY KEY, ISBN CHAR(13) REFERENCES bookdata(ISBN), Status TINYINT NOT NULL);")
queries.append("CREATE TABLE author (ISBN CHAR(13) REFERENCES bookdata(ISBN), DOB DATE, Name VARCHAR(50), PRIMARY KEY (ISBN, DOB));")
queries.append("CREATE TABLE categorynames (CategoryID INT PRIMARY KEY, Name VARCHAR(35) NOT NULL);")
queries.append("CREATE TABLE bookcategory (CategoryID INT REFERENCES categorynames(CategoryID), ISBN CHAR(13) REFERENCES bookdata(ISBN), PRIMARY KEY (CategoryID, ISBN));")
queries.append("CREATE TABLE checkout (Patron INT REFERENCES patron(AccID), Book CHAR(12) REFERENCES book(DecimalCode), Time_Out DATETIME NOT NULL, Due DATE NOT NULL, PRIMARY KEY (Patron, Book));")
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


def insert(table:str,fields:str, values:tuple[tuple, ...]):

    with MySQLdb.connect("db") as conn:

        cursor = get_cursor(conn)
        placeholders = ', '.join(['%s'] * len(fields.split(',')))
        query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
        try:
            cursor.executemany(query, values)
        except MySQLdb.Error as e:
            print(e)
        else:
            conn.commit()
        # Execute the query for each set of values in the list
        print(f"Data for {table} inserted successfully!")


def initialize():
    #Initializing tables
    create_table(queries)
    #Building Patron accounts
    # n_patrons = int(input("How many people do you want?\n"))
    fake = Faker()
    n_patrons = 100
    print(f"Building {n_patrons} patron accounts")
    values = tuple(
        zip([fake.name() for _ in range(n_patrons)],
            [fake.address() for _ in range(n_patrons)],
            [fake.unique.email() for _ in range(n_patrons)]))

    # read and insert book data
    books_data = populate_books.read_books_data()
    insert("patron","Name, Address, Email",values)
    insert("publisher", "PublisherID, PublisherName", populate_books.create_publisher_data(books_data))
    insert("bookdata","Title, PublishDate, Publisher, Description", populate_books.create_book_data(books_data))
    # insert("categorynames","CategoryID, Name", populate_books.tagdata)

#Main
if __name__ == "__main__":
    initialize()