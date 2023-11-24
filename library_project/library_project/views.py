from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# from . import initialize_db
import MySQLdb
from .forms import SearchForm
from .initialization.db_connect import get_cursor
from utils.general import keys_values_to_dict
import logging

logger = logging.getLogger('django')
# BOOK_STATUS = { "":2,"In stock":0,
# "Out of stock":1,
# "Reserved":2 }

def construct_query(
    search_term,
    advanced_search_fields,
    page_number:int,
    results_per_page:int
    ):
    query = """
    SELECT
        bookdata.BookID,
        bookdata.Title,
        GROUP_CONCAT(DISTINCT author.Name),
        publisher.PublisherName,
        COUNT(*) AS "num_copies",
        MIN(book.Status)
    FROM
        bookdata
        JOIN publisher ON publisher.PublisherID = bookdata.PublisherID
        JOIN category ON category.CategoryID = bookdata.CategoryID
        RIGHT JOIN author on bookdata.BookID = author.BookID
        RIGHT JOIN book ON bookdata.BookID = book.BookID
    WHERE
        1
    """
    search_params = []
    if search_term:

        query += """    AND MATCH (bookdata.Title, bookdata.Description)
            AGAINST (%s IN NATURAL LANGUAGE MODE WITH QUERY EXPANSION)"""
        search_params.append(search_term)

    # Add advanced search conditions
    for field, value in filter(lambda x: x[1] != '' and x[0] != "book.Status", advanced_search_fields.items()):
        query += f" AND {field} LIKE %s"
        search_params.append(f"%{value}%")
    # query += "\nGROUP BY bookdata.BookID"
    status = advanced_search_fields["book.Status"] if advanced_search_fields["book.Status"] != '' else 2
    # query += f"AND book.Status <= {status}\n"
    query += "\nGROUP BY\n    book.BookID\nHAVING MIN(book.Status) <= %s\n"
    search_params.append(status)

    # Add pagination
    offset = (page_number - 1) * results_per_page
    query += f" LIMIT {results_per_page} OFFSET {offset};"
    logger.info(query)
    # return query, search_params

    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)

        if search_term or advanced_search_fields:
            cursor.execute(query, search_params)
        else:
            cursor.execute(query)

        # Fetch the results
        results = cursor.fetchall()

    print(*results, sep="\n")

    return results, query, search_params


def homepage(request):
    form = SearchForm()
    return render(request, "home.html", {"form":form})

def search(request):
    if request.method == "GET":
        form = SearchForm(request.GET)

        # check whether it's valid:
        if not form.is_valid():
            return render(request, "search/search.html")

        # Construct the query based on form data
        search_query = form.cleaned_data['raw_search']
        advanced_search = {}
        advanced_search["author.Name"] = form.cleaned_data['author']
        advanced_search["category.CategoryName"] = form.cleaned_data['genre']
        advanced_search["book.Status"] = form.cleaned_data['in_stock']
        advanced_search["book.DecimalCode"] = form.cleaned_data['decimal_code']
        advanced_search["bookdata.Title"] = form.cleaned_data['title']
        page = form.cleaned_data["page"]
        results, query, qfields = construct_query(search_query, advanced_search, page, 50)
        results_numbers = (page-1) * 50

        # print(results)
        temp = form.cleaned_data
        temp["page"] = 1
        new_form = SearchForm(temp)
        return render(
            request,
            "search/search.html",
            {
                "form":new_form,
                "SQLquery":query,
                "results":results,
                "num_res":(results_numbers, results_numbers+ len(results))
                }
            )
    return render(request, "search/search.html")


def get_book_details(bookid:int):
    print(bookid, type(bookid))

    query = """
    SELECT
        bd.Title AS 'Book Title',
        GROUP_CONCAT(a.Name) AS 'Authors',
        c.CategoryName AS 'Category Name',
        p.PublisherName AS 'Publisher Name',
        bd.PublishDate AS 'Publish Date',
        MIN(b.Status) AS 'Minimum Status',
        bd.Description AS 'Description',
        COUNT(*) AS 'Number of Copies'
    FROM
        bookdata bd
        JOIN category c ON bd.CategoryID = c.CategoryID
        JOIN publisher p ON bd.PublisherID = p.PublisherID
        RIGHT JOIN author a ON bd.BookID = a.BookID
        RIGHT JOIN book b ON bd.BookID = b.BookID
    WHERE
        bd.BookID = %s
    GROUP BY
        b.BookID;

    """
    query = """
    SELECT
        bd.Title AS 'Book Title',
        GROUP_CONCAT(a.Name) AS 'Author',
        c.CategoryName AS 'Category Name',
        p.PublisherName AS 'Publisher Name',
        bd.PublishDate AS 'Publish Date',
        bd.Description AS 'Description'
    FROM
        bookdata bd
        JOIN publisher p ON p.PublisherID = bd.PublisherID
        JOIN category c ON c.CategoryID = bd.CategoryID
        RIGHT JOIN author a ON bd.BookID = a.BookID
    WHERE
        bd.BookID = %s;
    """
    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)
        cursor.execute(query, (bookid,))

        # Fetch the results
        results = cursor.fetchall()

    return keys_values_to_dict(["title",  "authors", "category", "publisher","publishdate","description"],results[0])


def detailed_results(request, bookid):
    results = get_book_details(bookid)
    return render(request, "search/details.html", {"results":results})

def landing(request):
    return render(request,"landing.html")

def lib(request):
    return render(request,'librarian.html')

def patron(request):
    return render(request,"patron.html")


def db_ping(request):
    # with MySQLdb.connect("db") as conn:

    try:
        conn = MySQLdb.connect("db")

        cursor = conn.cursor()
        query = "select * from library_project_patron"
        cursor.execute("use library")
        cursor.execute(query)
        conn.close()
        message = f"{cursor.fetchall()}"
    except MySQLdb.Error as e:
        message = f'Database connection failed: {e}'
    return JsonResponse({"message":message})
