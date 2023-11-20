from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# from . import initialize_db
import MySQLdb
from .forms import SearchForm
from .initialization.db_connect import get_cursor
import logging
logger = logging.getLogger('django')
# BOOK_STATUS = { "":2,"In stock":0,
# "Out of stock":1,
# "Reserved":2 }
GARBAGE_TERMS = set()

def construct_query(
    search_term,
    advanced_search_fields,
    page_number:int,
    results_per_page:int
    ):
    query = """SELECT bookdata.Title
    FROM bookdata
    WHERE  MATCH (bookdata.Title, bookdata.Description)
    AGAINST (%s IN NATURAL LANGUAGE MODE WITH QUERY EXPANSION)
    """
    search_params = [search_term]
    # NATURAL JOIN author, category, publisher

    # Add advanced search conditions
    for field, value in filter(lambda x: x[1] != '' and x[0] != "book.Status", advanced_search_fields.items()):
        query += f" AND {field} LIKE %s"
        search_params.append(f"%{value}%")

    # status = advanced_search_fields["book.Status"] if advanced_search_fields["book.Status"] != '' else 2
    # query += f"AND book.Status <= {status}\n"
    # query += "GROUP BY book.BookID\nHAVING MIN(book.Status) <= %s"
    # search_params.append(status)

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
    return results, query, search_params

def homepage(request):
    form = SearchForm()
    return render(request, "home.html", {"form":form})

def search(request):
    if request.method == "POST":
        form = SearchForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            fields = {k:v for k,v in filter(lambda x: x[1] != '', form.cleaned_data.items())}
        else:
            fields = {}

        # Construct the query based on form data
        search_query = form.cleaned_data['raw_search']
        advanced_search = {}
        advanced_search["author.Name"] = form.cleaned_data['author']
        advanced_search["category.CategoryName"] = form.cleaned_data['genre']
        advanced_search["book.Status"] = form.cleaned_data['in_stock']
        advanced_search["book.DecimalCode"] = form.cleaned_data['decimal_code']
        advanced_search["bookdata.Title"] = form.cleaned_data['title']
        results, query, qfields = construct_query(search_query, advanced_search, 1, 50)

        data = query, qfields
        # print(results)
        return render(request, "search.html", {"form_data":data, "good":fields, "results":results})
    return render(request, "search.html")


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
