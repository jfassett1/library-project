from initialize_db import list_of_tables
import MySQLdb


try:
    conn = MySQLdb.connect("db")
    cursor = conn.cursor()
    cursor.execute("use library")
    for table in list_of_tables:   
        print(f"Removing {table}")
        query = f"drop table {table}"
        cursor.execute(query)
        # Execute the query for each set of values in the list
    # cursor.executemany(query, values)
        
    conn.commit()
    print("Data removed successfully!")

except MySQLdb.Error as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
