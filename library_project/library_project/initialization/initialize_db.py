import MySQLdb
from patron_generation import mainbuild
from populate_books import bookdata,tagdata
import os
import pandas as pd
current_path = os.path.dirname(__file__)
parent_folder = os.path.abspath(os.path.join(current_path, os.pardir))
data_folder = os.path.join(parent_folder, "data/")

#List of tables generated
list_of_tables = [
    "library_project_patron",
    "library_project_bookdata",
    "library_project_book",
    "library_project_author",
    "library_project_categorynames",
    "library_project_bookcategory",
    "library_project_checkout",
    "library_project_distance",
    "library_project_elevator"
]
#


#Creating tables
queries = []
queries.append("CREATE TABLE library_project_patron (AccID INT AUTO_INCREMENT PRIMARY KEY, Name VARCHAR(50) NOT NULL, Address VARCHAR(100) NOT NULL, Email VARCHAR(40) NOT NULL);")
queries.append("CREATE TABLE library_project_bookdata (ISBN CHAR(13) PRIMARY KEY, Title VARCHAR(200) NOT NULL, PublishDate INT, Description TEXT);")
queries.append("CREATE TABLE library_project_book (DecimalCode CHAR(12) PRIMARY KEY, ISBN CHAR(13) REFERENCES library_project_bookdata(ISBN), Status TINYINT NOT NULL);")
queries.append("CREATE TABLE library_project_author (ISBN CHAR(13) REFERENCES library_project_bookdata(ISBN), DOB DATE, Name VARCHAR(50), PRIMARY KEY (ISBN, DOB));")
queries.append("CREATE TABLE library_project_categorynames (CategoryID INT PRIMARY KEY, Name VARCHAR(35) NOT NULL);")
queries.append("CREATE TABLE library_project_bookcategory (CategoryID INT REFERENCES library_project_categorynames(CategoryID), ISBN CHAR(13) REFERENCES library_project_bookdata(ISBN), PRIMARY KEY (CategoryID, ISBN));")
queries.append("CREATE TABLE library_project_checkout (Patron INT REFERENCES library_project_patron(AccID), Book CHAR(12) REFERENCES library_project_book(DecimalCode), Time_Out DATETIME NOT NULL, Due DATE NOT NULL, PRIMARY KEY (Patron, Book));")
queries.append("CREATE TABLE library_project_distance (Floor INT, Shelf1 INT NOT NULL, Shelf2 INT NOT NULL, Dist FLOAT NOT NULL, PRIMARY KEY (Shelf1, Shelf2));")
queries.append("CREATE TABLE library_project_elevator (ID CHAR(8) NOT NULL, Floor INT NOT NULL, Wait TIME NOT NULL, PRIMARY KEY (ID, Floor));")

def createTable(queries):
    try:
        conn = MySQLdb.connect("db")
        cursor = conn.cursor()
        cursor.execute("use library")
        for table,tablename in zip(queries,list_of_tables):
            print(f"Creating table {tablename}")
            cursor.execute(table)
        
        # Execute the query for each set of values in the list        
        conn.commit()
        print("Created Succesfully!")

    except MySQLdb.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
    return       
        




def insert(table,fields,values,):
    try:
        conn = MySQLdb.connect("db")
        cursor = conn.cursor()
        cursor.execute("use library")
        placeholders = ', '.join(['%s'] * len(fields.split(',')))
        query = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
        
        # Execute the query for each set of values in the list
        cursor.executemany(query, values)
        
        conn.commit()
        print(f"Data for {table} inserted successfully!")

    except MySQLdb.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
    return
def initialize():

    #Initializing tables
    createTable(queries)

    #Building Patron accounts
    # n_patrons = int(input("How many people do you want?\n"))
    n_patrons = 100
    print(f"Building {n_patrons} patron accounts")
    patron_accounts = mainbuild(n_patrons)
    values = tuple(map(lambda x: tuple(x)[1:], patron_accounts.itertuples()))

    #Building bookdata
    # book_data = create_bookdata()

    #Building Tag data
    # tag_data = create_tags()
    #Building tables & inserting 
    insert("library_project_patron","Name, Address, Email",values)
    insert("library_project_bookdata","ISBN, Title, PublishDate, Description",bookdata)
    insert("library_project_categorynames","CategoryID, Name",tagdata)
    return

#Main
if __name__ == "__main__":
    initialize()


