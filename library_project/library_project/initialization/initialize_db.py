import MySQLdb
#Because import statements break
try:
    from . import populate_books
except:
    import populate_books

try:
    from .db_connect import get_cursor
except:
    from db_connect import get_cursor

from faker import Faker


#List of tables generated
list_of_tables = [
    "patron",
    "publisher",
    "bookdata",
    "category",
    "book",
    "author",
    "checkout",
    "distance",
    "elevator"
]

#Creating tables
queries = []
queries.append("""
CREATE TABLE patron (
    AccID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Address VARCHAR(100) NOT NULL,
    Email VARCHAR(40) NOT NULL
);""")
queries.append("""
CREATE TABLE publisher (
    PublisherID INT PRIMARY KEY,
    PublisherName VARCHAR(50)
);""")
queries.append("""
CREATE TABLE category (
    CategoryID INT PRIMARY KEY,
    CategoryName TEXT NOT NULL
);""")
queries.append("""
CREATE TABLE bookdata (
	BookID INT PRIMARY KEY AUTO_INCREMENT,
	Title VARCHAR(255) NOT NULL,
	PublishDate INT,
	PublisherID INT REFERENCES publisher(PublisherID),
    CategoryID INT REFERENCES category(CategoryID),
	Description TEXT,
    FULLTEXT idx (Title, Description)
) Engine = InnoDB;""")
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
    Book CHAR(12) REFERENCES book(DecimalCode),
    Time_Out DATETIME NOT NULL,
    Due DATE NOT NULL,
    PRIMARY KEY (Patron, Book)
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
                return False
            else:
                print("Created Succesfully!")
        # Execute the query for each set of values in the list
        conn.commit()
        return True


def insert(table:str, fields:str, values:tuple[tuple, ...],additional:str=""):

    with MySQLdb.connect("db") as conn:

        cursor = get_cursor(conn)
        placeholders = ', '.join(['%s'] * len(fields.split(',')))
        query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders}){additional}"
        print(query)
        try:
            cursor.executemany(query, values)
        except MySQLdb.Error as e:
            print(e)
            return False
        else:
            conn.commit()
        # Execute the query for each set of values in the list
        print(f"Data for {table} inserted successfully!")


def initialize():
    #Initializing tables
    if not create_table(queries):
        print("Initialization Failed, consider refreshing database?")
        return
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
    # sample = books_data.groupby("categories").sample(frac=0.10, replace=True, weights=book_data["ratingsCount"]+1)["categories"]

    insert("patron","Name, Address, Email",values)
    insert("category","CategoryID, CategoryName", populate_books.extract_categorical_book_data(books_data, "categories"))
    insert("publisher", "PublisherID, PublisherName", populate_books.extract_categorical_book_data(books_data, "publisher"))
    insert("bookdata","Title, PublishDate, PublisherID, CategoryID, Description", populate_books.create_book_data(books_data))
    insert("author","BookID, Name",populate_books.format_author_data(books_data)," ON DUPLICATE KEY UPDATE BookID = Values(BookID),Name = Values(Name)")
    # insert("book","DecimalCode, BookID, Status", populate_books.generate_library(books_data))
    insert("book","DecimalCode, BookID, Status", populate_books.generate_shelf_decimal(books_data))
    print("Initialization Complete!")
#Main
if __name__ == "__main__":
    initialize()