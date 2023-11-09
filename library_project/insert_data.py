import MySQLdb
from patron_generation import mainbuild
import os
import pandas as pd

current_path = os.path.dirname(__file__)
parent_folder = os.path.abspath(os.path.join(current_path, os.pardir))
data_folder = os.path.join(parent_folder, "data/")


data = mainbuild(100)
values = tuple(map(lambda x: tuple(x)[1:], data.itertuples()))


def insert(table,values):
    try:
        conn = MySQLdb.connect("db")
        cursor = conn.cursor()
        cursor.execute("use library")
        query = f"INSERT INTO {table} (Name, Address, Email) VALUES (%s, %s, %s)"

        # Execute the query for each set of values in the list
        cursor.executemany(query, values)

        conn.commit()
        print("Data inserted successfully!")

    except MySQLdb.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
    return
insert("library_project_patron",values)