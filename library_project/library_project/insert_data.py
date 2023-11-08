import MySQLdb
from patron_generation import mainbuild


data = mainbuild(100)
values = tuple(map(lambda x: tuple(x)[1:], data.itertuples()))

def insert(values):
    conn = MySQLdb.connect("db")
    cursor = conn.cursor()
    cursor.execute("use library")
    query = f"INSERT INTO library_project_patron VALUES {values}"
    cursor.execute(query)
    conn.close()
    return