import json
import logging

# from . import initialize_db
import MySQLdb
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from utils.general import (
    checkout_book_hold,
    checkout_book_return,
    construct_return_query,
    construct_search_query,
    find_similar_books,
    get_book_best_status,
    get_book_details,
    make_recommendation,
    user_checkout,
    user_waitlist,
)

from .forms import (
    ReturnForm,
    SearchForm,
    addBook,
    addForm,
    alterBook,
    alterPatron,
    rmBook,
    rmPatron,
    addPatron,
)
from .initialization.db_connect import get_cursor

logger = logging.getLogger("django")


def homepage(request):
    form = SearchForm()
    if not request.user.is_authenticated:
        return render(request, "home.html", {"form": form, "info": ""})
    return make_recommendation(request, form)


def search(request):
    if request.method == "GET":
        form = SearchForm(request.GET)

        # check whether it's valid:
        if not form.is_valid():
            return render(request, "search/search.html", {"form": SearchForm()})

        RESULTS_PER_PAGE = 50
        results, query, page = construct_search_query(form, RESULTS_PER_PAGE)
        results_numbers = (page - 1) * RESULTS_PER_PAGE

        temp = form.cleaned_data
        temp["page"] = 1
        new_form = SearchForm(temp)
        return render(
            request,
            "search/search.html",
            {
                "form": new_form,
                "SQLquery": query,
                "results": results,
                "num_res": (results_numbers, results_numbers + len(results)),
            },
        )
    return render(request, "search/search.html", {"form": SearchForm()})


def detailed_results(request, bookid):
    # Code for recommendations
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        query = f"""SELECT Title FROM bookdata WHERE BookID = {bookid}"""
        cursor.execute(query)
        try:
            info = cursor.fetchall()[0][0]
            cursor.close()
        except MySQLdb.Error:
            info = ""
        # return render(request,"home.html",{"form":form,"info":info})
    # Recommendation code
    recommendations = find_similar_books(request, info)

    results = get_book_details(bookid)
    results["books"] = list(zip(results["codes"], results["status"]))
    results["best_status"] = min(results["status"])
    return render(
        request,
        "search/details.html",
        {"results": results, "lastbook": info, "info": recommendations},
    )


@login_required()
def checkout_book(request):
    if request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        print(body)
        book = get_book_best_status(**body)

        # Check if the book is available
        if book is True:
            # Perform the checkout
            response = user_checkout(request.user, body["book_id"])
            return JsonResponse({"success": response})
        else:
            # Add the user to the waitlist
            response = user_waitlist(request.user, body["book_id"])
            return JsonResponse({"waitlisted": response})

    # print(request)
    elif request.method == "GET":
        # return render(request, "/")
        return redirect(homepage)
    # If the request method is not POST, return an error response
    return JsonResponse({"error": "Invalid request method"})


@staff_member_required
def check_status(request):
    if request.method == "POST":
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        print(body)
        book = None
        if body["new_status"] == 2:
            book = checkout_book_return(**body)
        elif body["new_status"] == 0:
            book = checkout_book_hold(**body)

        if book is None:
            return JsonResponse({"failed": "Book not found in checkout"})

        return JsonResponse({"success": (body["book_decimal"], book)})

    # print(request)
    elif request.method == "GET":
        # return render(request, "/")
        return redirect(homepage)
    # If the request method is not POST, return an error response
    return JsonResponse({"error": "Invalid request method"})


@staff_member_required
def return_book(request):
    if request.method == "GET":
        form = ReturnForm(request.GET)
        if not form.is_valid():
            return render(request, "update/returns.html", {"form": ReturnForm()})

        RESULTS_PER_PAGE = 50
        results, query, page = construct_return_query(form, RESULTS_PER_PAGE)
        results_numbers = (page - 1) * RESULTS_PER_PAGE

        temp = form.cleaned_data
        temp["page"] = 1
        new_form = ReturnForm(temp)
        return render(
            request,
            "update/returns.html",
            {
                "form": new_form,
                "SQLquery": query,
                "results": results,
                "num_res": (results_numbers, results_numbers + len(results)),
            },
        )
    return render(request, "update/returns.html", {"form": ReturnForm()})


@staff_member_required
def update(request):
    return render(
        request,
        "update/update.html",
        {
            "addForm": addForm(),
            "addPatron":addPatron(),
            "addBook":addBook(),
            "rmBook": rmBook(),
            "rmPatron": rmPatron(),
            "alterBook": alterBook(),
            "alterPatron": alterPatron(),
        },
    )


def change(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            return add_row(request)
        elif action == "addPatron":
            return add_patron(request)
        elif action == "remove":
            return remove_row(request)
        elif action == "rmPatron":
            return remove_patron(request)
        elif action == "alter":
            return alter_book(request)
        elif action == "alterPatron":
            alter_patron(request)
        elif action == "copy":
            return add_book(request)
        else:
            return HttpResponse("Invalid action submitted", action)
    return HttpResponse(f"Invalid request method:{request.method}")


def alter_patron(request):
    if request.method != "POST":
        # Display an empty form when the page is first loaded
        return render(request, "update/change.html", {"form": alterPatron()})

    form = alterPatron(request.POST)
    if not form.is_valid():
        # Handle invalid form
        return render(
            request,
            "update/change.html",
            {"message": "Invalid form data", "form": form},
        )

    # Extract validated form data
    set_clauses = []
    params = []
    for field, value in form.cleaned_data.items():
        if (
            field != "accid" and value is not None
        ):  # Assuming 'accid' is the account ID, used in WHERE clause
            set_clauses.append(f"`{field}` = %s")
            params.append(value)

    accid = form.cleaned_data.get("accid")
    if not set_clauses:
        # No data to update
        return render(request, "update/change.html", {"message": "No fields to update"})

    query = "UPDATE patron SET " + ", ".join(set_clauses) + " WHERE `accid` = %s"
    params.append(accid)

    try:
        with MySQLdb.connect(
            "db"
        ) as conn:  # Replace 'db' with your actual database connection details
            with get_cursor(conn, "library") as cursor:
                cursor.execute(query, params)
                conn.commit()
    except MySQLdb.Error as e:
        # Handle database errors
        return render(
            request, "update/change.html", {"message": f"Database error: {e}"}
        )

    return render(
        request, "update/change.html", {"message": "Update successful", "query": query}
    )


def alter_book(request):
    if request.method != "POST":
        return render(request, "update/change.html", {"form": alterBook()})

    form = alterBook(request.POST)
    if not form.is_valid():
        return render(
            request,
            "update/change.html",
            {"message": "Invalid form data", "form": form},
        )

    # Extract validated form data
    alter_features = form.cleaned_data.get("alterfields")
    searchby = form.cleaned_data.get("SEARCHBY")
    searchparam = form.cleaned_data.get(searchby)
    author = form.cleaned_data.get("author")
    category = form.cleaned_data.get("category")

    bookid = form.cleaned_data.get(
        "bookid"
    )  # Corrected from form.cleaned_data('bookid')
    if searchby == "decimal":
        with MySQLdb.connect("db") as conn:
            with get_cursor(conn, "library") as cursor:
                idquery = "SELECT b.BookID FROM book AS b WHERE b.DecimalCode = %s"
                cursor.execute(idquery, (searchparam,))
                result = cursor.fetchone()
                if result:
                    bookid = result[0]
                else:
                    return render(
                        request,
                        "update/change.html",
                        {"message": "No book found with the given DecimalCode"},
                    )

    # Special cases for author and category
    try:
        with MySQLdb.connect("db") as conn:
            with get_cursor(conn, "library") as cursor:
                if "author" in alter_features:
                    alter_features.remove("author")
                    cursor.execute(
                        "UPDATE author SET Name = %s WHERE BookID = %s",
                        (author, bookid),
                    )
                    conn.commit()

                if "category" in alter_features:
                    alter_features.remove("category")
                    cursor.execute(
                        "UPDATE category SET CategoryName = %s WHERE BookID = %s",
                        (category, bookid),
                    )
                    conn.commit()

                # Update bookdata
                if alter_features:
                    set_clauses = [f"`{field}` = %s" for field in alter_features]
                    params = [form.cleaned_data.get(field) for field in alter_features]
                    bookdata_query = (
                        "UPDATE bookdata SET "
                        + ", ".join(set_clauses)
                        + " WHERE BookID = %s"
                    )
                    params.append(bookid)
                    cursor.execute(bookdata_query, params)
                    conn.commit()
    except MySQLdb.Error as e:
        return render(
            request, "update/change.html", {"message": f"Database error: {e}"}
        )

    return render(
        request,
        "update/change.html",
        {"message": "Update successful", "query": bookdata_query},
    )


def remove_row(request):
    if request.method == "POST":
        form = rmBook(request.POST)
        if form.is_valid():
            conn = MySQLdb.connect("db")
            cursor = get_cursor(conn, "library")

            searchby = form.cleaned_data["SEARCHBY"]
            decimal = form.cleaned_data["decimal"]
            bookID = form.cleaned_data["bookid"]
            if not (decimal or bookID):
                return HttpResponse("Input at least one field")

            # Depending on searchby
            if searchby == "0":
                query = f"DELETE FROM bookdata WHERE BookID = {bookID}"
            elif searchby == "1":
                query = f"""DELETE FROM bookdata AS bd
                            WHERE bd.BookID IN (
                                SELECT b.BookID
                                FROM book AS b
                                WHERE b.DecimalCode = '{decimal}'
                            );"""
            else:
                query = ""
            try:
                cursor.execute(query)
                conn.commit()

                message = "Succesful?"
            except MySQLdb.Error as e:
                message = e
            return render(
                request, "update/change.html", {"message": message, "query": query}
            )
    return HttpResponse(f"Invalid request method remove_row: {request.method}")

def remove_patron(request):
    if request.method == "POST":
        form = rmPatron(request.POST)
        if form.is_valid():
            conn = MySQLdb.connect("db")
            cursor = get_cursor(conn, "library")


            accID = form.cleaned_data["accid"]
            # Depending on searchby
            query = f"DELETE FROM patron WHERE AccID = {accID}"

            try:
                cursor.execute(query)
                conn.commit()

                message = "Succesful?"
            except MySQLdb.Error as e:
                message = e
            return render(
                request, "update/change.html", {"message": message, "query": query}
            )
    return HttpResponse(f"Invalid request method: {request.post}")




def add_patron(request):
    if request.method == "POST":
        form = addPatron()
        if form.is_valid():
            name = form.cleaned_data.get('name')
            address= form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')

            with MySQLdb.connect('db') as conn:
                with get_cursor(conn,'library') as cursor:
                    query = f"INSERT INTO patron (Name, Address, Email) VALUES({name}, {address}, {email})"

            try:
                cursor.execute(query)
                conn.commit()
                message = "Success"
            except MySQLdb.Error as e:
                message = e
            return render(
                request,
                "update/change.html",
                {"message": message, "query": [query]})
def add_row(request):
    if request.method == "POST":
        form = addForm(request.POST)
        if form.is_valid():
            conn = MySQLdb.connect("db")
            cursor = get_cursor(conn, "library")

            # Form data is valid, so you can process and save it to the database
            title = form.cleaned_data["title"]
            author = form.cleaned_data["author"]
            publisher = form.cleaned_data["publisher"]
            category = form.cleaned_data["category"]
            year = form.cleaned_data["year"]
            descript = form.cleaned_data["desc"].replace("'", "''")

            query_bookdata = f"""INSERT INTO bookdata (Title, PublishDate, Publisher, Description) VALUES ('{title}',{year},'{publisher}','{descript}')"""
            query_author = "INSERT INTO author (BookID, Name) VALUES (%s, %s)"
            query_category = (
                "INSERT INTO category (BookID, CategoryName) VALUES (%s,%s)"
            )
            #Getting decimal

            query_decimal = f"""WITH PotentialShelves AS (
    SELECT
        SUBSTRING_INDEX(cb.DecimalCode, '.', 2) AS Shelf,
        COUNT(*) AS BooksInSubShelf
    FROM
        combined_bookdata cb
        INNER JOIN category cat ON cb.BookID = cat.BookID
    WHERE
        cat.CategoryName = '{category}'
    GROUP BY
        Shelf
)

SELECT
    GROUP_CONCAT(PS.Shelf)
FROM
    PotentialShelves PS
GROUP BY
    PS.BooksInSubShelf
HAVING PS.BooksInSubShelf < 30
LIMIT 10;"""

            #Getting decimal
            try:
                cursor.execute(find_decimal)
                decimal = cursor.fetchone()
            except MySQLdb.Error as e:
                return HttpResponse(f"{e}")
            try:
                # Bookdata Query
                cursor.execute(query_bookdata)
                # Gets bookID
                bookID = cursor.lastrowid
                # Author Query
                decimal = f"{decimal[0]}.{bookID}.0"
                cursor.execute(query_book,(decimal,bookID,0))
                cursor.execute(query_author, (bookID, author))
                cursor.execute(query_category, (bookID, category))
                

                conn.commit()
                message = mark_safe(f"Insert Successful!<br>{bookID}")
            except MySQLdb.Error as e:
                message = e
            return render(
                request,
                "update/change.html",
                {"message": message, "query": [query_bookdata,decimal]},
            )
    return HttpResponse("Invalid request method")

def add_book(request):
    if request.method != "POST":
        return HttpResponse("Invalid request method")
    form = addBook(request.POST)
    if not form.is_valid():
        return HttpResponse("Invalid form here")
    category = "Misc."
    with MySQLdb.connect('db') as conn:
        with get_cursor(conn,'library') as cursor:
            book_id = form.cleaned_data['book_id']
            fetch_category = f"""
            SELECT GROUP_CONCAT(DISTINCT c.CategoryName)
            FROM category c
            WHERE c.BookID = '{book_id}'
            GROUP BY c.CategoryName
            """
            ## get data
            try:
                cursor.execute(fetch_category)
                category = cursor.fetchone()
            except MySQLdb.Error as e:
                print(e)
                return HttpResponse("failed to fetch category")

    shelf_id = "999.0"
    with MySQLdb.connect('db') as conn:
        with get_cursor(conn,'library') as cursor:
            gen_decimal_query = f"""
            SELECT PS.Shelf
            FROM (
            SELECT
                SUBSTRING_INDEX(cb.DecimalCode, '.', 2) AS Shelf,
                COUNT(*) AS BooksInSubShelf,
                GROUP_CONCAT(DISTINCT c.CategoryName) AS Cat

            FROM
                combined_bookdata cb
                LEFT JOIN category c ON c.BookID = cb.BookID
            GROUP BY Shelf, c.CategoryName
            HAVING BooksInSubShelf < 30) AS PS
            WHERE PS.Cat LIKE '%{category}%';"""
            try:
                cursor.execute(gen_decimal_query)
                shelf_id = cursor.fetchone()
                conn.commit()
            except MySQLdb.Error as e:
                print(e)
                return HttpResponse("failed to fetch category")

    with MySQLdb.connect('db') as conn:
        with get_cursor(conn,'library') as cursor:
            gen_decimal_query = """
            SELECT MAX(PS.Shelf)
            FROM (
            SELECT
                SUBSTRING_INDEX(cb.DecimalCode, '.', 1) AS Shelf,
                COUNT(*) AS BooksInSubShelf,
            FROM
                combined_bookdata cb
            GROUP BY Shelf, c.CategoryName;"""
            try:
                cursor.execute(gen_decimal_query)
                shelf_id = cursor.fetchone() + ".0"
                conn.commit()
            except MySQLdb.Error as e:
                print(e)
                return HttpResponse("failed to fetch category")

    with MySQLdb.connect('db') as conn:
        with get_cursor(conn,'library') as cursor:
            shelf_id += f".{book_id}.0"
            q = f"INSERT INTO book SET BookID={book_id}, DecimalCode='{shelf_id}'"
            try:
                cursor.execute(q)
                conn.commit()
            except MySQLdb.Error as e:
                print(e)
                return HttpResponse("failed to fetch category")


def db_ping(request):
    # with MySQLdb.connect("db") as conn:

    try:
        conn = MySQLdb.connect("db")

        cursor = conn.cursor()
        query = "select * from patron"
        cursor.execute("use library")
        cursor.execute(query)
        conn.close()
        message = f"{cursor.fetchall()}"
    except MySQLdb.Error as e:
        message = f"Database connection failed: {e}"
    return JsonResponse({"message": message})
