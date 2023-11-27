from initialize_db import list_of_tables, list_of_views, list_of_triggers
import MySQLdb
from db_connect import get_cursor

# list_of_tables.reverse()
with MySQLdb.connect("db") as conn:
    cursor = get_cursor(conn)
    for table in list_of_tables:
        print(f"Removing {table}")
        query = f"DROP TABLE {table};"
        try:
            cursor.execute(query)
        except MySQLdb.Error as e:
            print(f"Error: {e}")
        else:
            print("Data removed successfully!")
    for view in list_of_views:
        print(f"Removing {view}")
        query = f"DROP VIEW {view};"
        try:
            cursor.execute(query)
        except MySQLdb.Error as e:
            print(f"Error: {e}")
        else:
            print("View removed successfully!")
    # for trigger in list_of_triggers:
    #     print(f"Removing {trigger}")
    #     query = f"DROP TRIGGER {trigger};"
    #     try:
    #         cursor.execute(query)
    #     except MySQLdb.Error as e:
    #         print(f"Error: {e}")
    #     else:
    #         print("Trigger removed successfully!")
    conn.commit()
