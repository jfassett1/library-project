import datetime
import MySQLdb
import joblib
from django.contrib.auth.models import User
from django.shortcuts import render
from gensim.models.doc2vec import Doc2Vec
from gensim.parsing.preprocessing import preprocess_documents
from library_project.initialization.db_connect import get_cursor


def keys_values_to_dict(keys: list | tuple, values: list | tuple) -> dict:
    if len(keys) != len(values):
        raise ValueError("Length of keys must be the same as values")
    ret = {}
    for k, v in zip(keys, values):
        ret[k] = v

    return ret


def construct_search_query(
    search_term, advanced_search_fields, page_number: int, results_per_page: int
):
    query = """
    SELECT
        cb.BookID,
        cb.Title,
        cb.Publisher,
        GROUP_CONCAT(DISTINCT a.Name),
        COUNT(DISTINCT cb.DecimalCode) AS "num_copies",
        MIN(cb.Status)
    FROM
        combined_bookdata cb
        RIGHT JOIN category c ON cb.BookID = c.BookID
        RIGHT JOIN author a ON cb.BookID = a.BookID
    WHERE
        1
    """
    search_params = []
    if search_term:
        query += """
        AND MATCH (cb.Title, cb.Description)
            AGAINST (%s IN NATURAL LANGUAGE MODE)"""
        search_params.append(search_term)

    # Add advanced search conditions
    exclude = ("cb.Status", "minYear", "maxYear")
    for field, value in filter(
        lambda x: x[1] != "" and x[0] not in exclude, advanced_search_fields.items()
    ):
        query += f" AND {field} LIKE %s"
        search_params.append(f"%{value}%")

    min_yr_field = isinstance(advanced_search_fields["minYear"], int)
    max_yr_field = isinstance(advanced_search_fields["maxYear"], int)

    if min_yr_field and max_yr_field:
        min_yr = max(advanced_search_fields["minYear"], -9999)
        max_yr = min(advanced_search_fields["maxYear"], datetime.date.today().year)
        if min_yr > max_yr:
            min_yr, max_yr = max_yr, min_yr

        query += """
        AND cb.PublishDate BETWEEN %s AND %s
        """
        search_params.extend([min_yr, max_yr])
    elif min_yr_field:
        min_yr = max(advanced_search_fields["minYear"], -9999)
        query += """
        AND cb.PublishDate >= %s
        """
        search_params.append(min_yr)
    elif max_yr_field:
        max_yr = min(advanced_search_fields["maxYear"], datetime.date.today().year)

        query += """
        AND cb.PublishDate <= %s
        """
        search_params.append(max_yr)

    status = (
        advanced_search_fields["cb.Status"]
        if advanced_search_fields["cb.Status"] != ""
        else 2
    )
    query += "\nGROUP BY\n    cb.BookID\nHAVING MIN(cb.Status) <= %s\n"
    search_params.append(status)

    # Add pagination
    offset = (page_number - 1) * results_per_page
    query += f" LIMIT {results_per_page} OFFSET {offset};"
    # logger.info(query)

    # return query, search_params
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)

        if search_term or advanced_search_fields:
            cursor.execute(query, search_params)
        else:
            cursor.execute(query)

        # Fetch the results
        results = cursor.fetchall()

    # print(*results, sep="\n")

    return results, query, search_params

def process_return_form(form):
    # Construct the query based on form data
    search_query = form.cleaned_data["raw_search"]
    advanced_search = {}
    advanced_search["a.Name"] = form.cleaned_data["author"]
    advanced_search["c.CategoryName"] = form.cleaned_data["genre"]

    advanced_search["ch.Status"] = form.cleaned_data["in_stock"]
    advanced_search["ch.DecimalCode"] = form.cleaned_data["decimal_code"]
    advanced_search["ch.Patron"] = form.cleaned_data["user_name"]

    advanced_search["ud.first_name"] = form.cleaned_data["first_name"]
    advanced_search["ud.last_name"] = form.cleaned_data["last_name"]
    advanced_search["ud.email"] = form.cleaned_data["email"]

    advanced_search["cb.Title"] = form.cleaned_data["title"]
    advanced_search["cb.Publisher"] = form.cleaned_data["publisher"]

    advanced_search["minYear"] = form.cleaned_data["lower_publish_year"]
    advanced_search["maxYear"] = form.cleaned_data["upper_publish_year"]

    page = form.cleaned_data["page"]

    return search_query, advanced_search, page

def construct_return_query(
    search_term, advanced_search_fields, page_number: int, results_per_page: int
):
    query = """
    SELECT
        ch.BookID,
        cb.Title,
        ch.Patron,
        ch.DecimalCode,
        ch.TimeOut,
        ch.Due,
        ch.Status
    FROM
        checkout ch
        LEFT JOIN combined_bookdata cb ON cb.DecimalCode = ch.DecimalCode
        LEFT JOIN (
            SELECT GROUP_CONCAT(CategoryName), BookID
            FROM category
            GROUP BY BookID
            ) c ON ch.BookID = c.BookID
        LEFT JOIN (
                SELECT GROUP_CONCAT(Name), BookID
                FROM author
                GROUP BY BookID
            ) a ON ch.BookID = a.BookID
        LEFT JOIN auth_user ud ON ud.username = ch.Patron
    WHERE
        1
    """
    search_params = []
    if search_term:
        query += """
        AND MATCH (cb.Title, cb.Description)
            AGAINST (%s IN NATURAL LANGUAGE MODE)"""
        search_params.append(search_term)

    # Add advanced search conditions
    exclude = ("ch.Status", "minYear", "maxYear")
    for field, value in filter(
        lambda x: x[1] != "" and x[0] not in exclude, advanced_search_fields.items()
    ):
        query += f" AND {field} LIKE %s"
        search_params.append(f"%{value}%")

    min_yr_field = isinstance(advanced_search_fields["minYear"], int)
    max_yr_field = isinstance(advanced_search_fields["maxYear"], int)

    if min_yr_field and max_yr_field:
        min_yr = max(advanced_search_fields["minYear"], -9999)
        max_yr = min(advanced_search_fields["maxYear"], datetime.date.today().year)
        if min_yr > max_yr:
            min_yr, max_yr = max_yr, min_yr

        query += """
        AND cb.PublishDate BETWEEN %s AND %s
        """
        search_params.extend([min_yr, max_yr])
    elif min_yr_field:
        min_yr = max(advanced_search_fields["minYear"], -9999)
        query += """
        AND cb.PublishDate >= %s
        """
        search_params.append(min_yr)
    elif max_yr_field:
        max_yr = min(advanced_search_fields["maxYear"], datetime.date.today().year)

        query += """
        AND cb.PublishDate <= %s
        """
        search_params.append(max_yr)

    status = (
        advanced_search_fields["ch.Status"]
        if advanced_search_fields["ch.Status"] != ""
        else 0
    )
    query += "\nAND ch.Status >= %s\n"
    search_params.append(status)

    # Add pagination
    offset = (page_number - 1) * results_per_page
    query += f" LIMIT {results_per_page} OFFSET {offset};"
    # logger.info(query)

    # return query, search_params
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)

        if search_term or advanced_search_fields:
            cursor.execute(query, search_params)
        else:
            cursor.execute(query)

        # Fetch the results
        results = cursor.fetchall()

    # print(*results, sep="\n")

    return results, query, search_params


def find_unread_book_id(
    best_sample_titles: list[str], username: str | None, conn: MySQLdb.Connection
):
    cursor = get_cursor(conn)

    placeholders = "%s, " * (len(best_sample_titles) - 1) + "%s"
    print(placeholders)

    id_query = f"""
    SELECT b.Title, b.BookID
    FROM bookdata b
    WHERE
        b.Title IN ({placeholders})"""
    if username is not None:
        id_query += f"""
        AND b.BookID NOT IN
        (
            SELECT c.BookID
            FROM checkout c
            WHERE c.Patron = '{username}'
        )"""

    id_query += "LIMIT 5;"

    cursor.execute(id_query, best_sample_titles)

    reccomended_titles_bids = cursor.fetchall()
    print(reccomended_titles_bids)
    cursor.close()
    return reccomended_titles_bids


def predict_similar(info: list[str]):
    # Recommendation code
    model = Doc2Vec.load(r"./library_project/recommendation/d2v.model")
    neigh = joblib.load(r"./library_project/recommendation/neighbors.pkl")
    titlemap = joblib.load(r"./library_project/recommendation/titlemap.pkl")

    # process titles into list of strings
    titles = preprocess_documents(info)
    print(info)
    # get neighbors
    predictions = []
    for j, title in enumerate(titles):
        sample = model.infer_vector(title)  # type: ignore
        dist, idxs = neigh.kneighbors([sample], 10)
        print(dist)
        dist /= 1 + (1 / (j + 2) ** j)
        print(dist, idxs, info[j])
        predictions.extend([(d, i) for d, i in zip(dist[0][1:], idxs[0][1:])])

    print(predictions)
    predictions.sort()
    return [titlemap[i] for _, i in predictions]


def find_similar_books(request, book_name):
    with MySQLdb.connect("db") as conn:
        try:
            user = User.objects.get(username=request.user.username)
            username = user.username
        except:
            username = None
        return find_unread_book_id(predict_similar([book_name]), username, conn)


def make_recommendation(request, form):
    info = ""
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        user = User.objects.get(username=request.user.username)

        username = user.username

        query = f"""
        SELECT DISTINCT bc.Title, bc.TimeOut
        FROM (
            SELECT b.Title, c.TimeOut
            FROM checkout as c
            INNER JOIN bookdata as b ON c.BookID = b.BookID
            WHERE c.Patron = '{username}'
            ORDER BY c.TimeOut DESC
        ) AS bc
        ORDER BY bc.TimeOut DESC
        LIMIT 5;"""

        try:
            cursor.execute(query)
            info = [c[0] for c in cursor.fetchall()]
            cursor.close()
        except MySQLdb.Error:
            return render(request, "home.html", {"form": form, "info": info})
        if not info:
            return render(request, "home.html", {"form": form, "info": ""})

        reccomended_titles_bids = find_unread_book_id(
            predict_similar(info), username, conn
        )

        return render(
            request,
            "home.html",
            {"form": form, "info": reccomended_titles_bids, "lastbook": info[0]},
        )


def get_book_details(bookid: int):
    # print(bookid, type(bookid))

    query = """
    SELECT
        cb.Title AS 'Book Title',
        GROUP_CONCAT(a.Name) AS 'Authors',
        GROUP_CONCAT(DISTINCT c.CategoryName) AS 'Categories',
        cb.Publisher AS 'Publisher Name',
        cb.PublishDate AS 'Publish Date',
        cb.Description AS 'Description',
        COUNT(*) AS 'Number of Copies',
        cb.DecimalCode AS 'Book Codes',
        cb.Status AS 'Status',
        MIN(cb.BookID) AS 'ID'
    FROM
        combined_bookdata cb
        RIGHT JOIN category c ON cb.BookID = c.BookID
        RIGHT JOIN author a ON cb.BookID = a.BookID
    WHERE
        cb.BookID = %s
    GROUP BY
        cb.BookID, cb.DecimalCode;
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        cursor.execute(query, (bookid,))

        # Fetch the results
        results = cursor.fetchall()

    names = [
        "title",
        "authors",
        "category",
        "publisher",
        "publishdate",
        "description",
        "copies",
        "codes",
        "status",
        "book_id",
    ]
    try:
        return keys_values_to_dict(names, [tuple(r) for r in zip(*results)])
    except ValueError as e:
        print(e)
        return keys_values_to_dict(names, ["Unknown"] * len(names))


def get_book_best_status(book_id: str):
    query = """
    SELECT
        MIN(b.Status)
    FROM
        book b
    WHERE
        b.BookID = %s
    GROUP BY
        b.BookID
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        cursor.execute(query, (book_id,))

        # Fetch the results
        results = cursor.fetchall()
    print(f"best status for {book_id}:", results)
    # no results means no one in waitlist
    return not results[0][0]

def get_copy_status(book_decimal: str):
    query = """
    SELECT
        c.DecimalCode, c.Status
    FROM
        checkout c
    WHERE
        c.DecimalCode LIKE %s
        AND c.Status IN (0, 1)
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        cursor.execute(query, (f"%{book_decimal}%",))

        # Fetch the results
        results = cursor.fetchall()
    print(f"Status of {book_decimal}:", results)
    if results == ():
        return None
    # no results means no one in waitlist
    return results[0][0]

def checkout_book_return(book_decimal:str, new_status:int=2):
    query = """
    UPDATE
        checkout c
    SET
        c.Status = %s
    WHERE
        c.DecimalCode = %s
        AND c.Status IN (0,1);
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        try:
            cursor.execute(query, (new_status, book_decimal))
            conn.commit()

        except MySQLdb.Error as e:
            print(e)
            return False
        else:
            print(f"Return of {book_decimal} successful")
            return True

def checkout_book_hold(book_decimal:str, new_status:int=0):
    query = """
    UPDATE
        checkout c
    SET
        c.Status = %s,
        c.Due = (CURRENT_DATE + INTERVAL 2 WEEK)
    WHERE
        c.DecimalCode = %s
        AND c.Status = 3;
    """
    procedure_call_query = "CALL MoveToHoldFromWaitlist(%s);"
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        try:
            cursor.execute(query, (new_status, book_decimal))
            cursor.execute(procedure_call_query, (book_decimal))
            conn.commit()

        except MySQLdb.Error as e:
            print(e)
            return False
        else:
            print(f"Return of {book_decimal} successful")
            return True

def user_checkout(user, book_id):
    query = """
    INSERT INTO checkout (Patron, BookID, Status)
    VALUES (%s, %s, %s);
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        try:
            cursor.execute(query, (user, book_id, 0))
            conn.commit()

        except MySQLdb.Error as e:
            print(e)
            return False
        else:
            print(f"Checkout of {book_id} by {user} successful")
            return True


def user_waitlist(user, book_id):
    query = """
    INSERT INTO waitlist (Patron, BookID)
    VALUES (%s,%s);
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        try:
            cursor.execute(query, (user, book_id))
            conn.commit()

        except MySQLdb.Error as e:
            print(e)
            return False
        else:
            print(f"Waitlist of {book_id} by {user} successful")
            return True


def process_search_form(form):
    # Construct the query based on form data
    search_query = form.cleaned_data["raw_search"]
    advanced_search = {}
    advanced_search["a.Name"] = form.cleaned_data["author"]

    advanced_search["c.CategoryName"] = form.cleaned_data["genre"]

    advanced_search["cb.Status"] = form.cleaned_data["in_stock"]
    advanced_search["cb.DecimalCode"] = form.cleaned_data["decimal_code"]
    advanced_search["cb.Title"] = form.cleaned_data["title"]
    advanced_search["cb.Publisher"] = form.cleaned_data["publisher"]
    advanced_search["minYear"] = form.cleaned_data["lower_publish_year"]
    advanced_search["maxYear"] = form.cleaned_data["upper_publish_year"]

    page = form.cleaned_data["page"]

    return search_query, advanced_search, page


