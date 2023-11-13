from initialize_db import list_of_tables
import MySQLdb
from db_connect import get_cursor

# list_of_tables.reverse()
with MySQLdb.connect("db") as conn:
    cursor = get_cursor(conn)
    for table in list_of_tables:
        print(f"Removing {table}")
        query = f"drop table {table}"
        try:
            cursor.execute(query)
        except MySQLdb.Error as e:
            print(f"Error: {e}")
        else:
            print("Data removed successfully!")
    conn.commit()
