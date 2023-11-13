def get_cursor(connection, db_name:str="library"):
    cursor = connection.cursor()
    cursor.execute(f"use {db_name}")
    return cursor
