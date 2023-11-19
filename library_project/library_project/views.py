from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# from . import initialize_db
import MySQLdb
from .forms import SearchForm
import utils.select_query
from .initialization.db_connect import get_cursor

def construct_query(
    search_term,
    advanced_search_fields,
    page_number:int,
    results_per_page:int
    ):
    query = """SELECT bookdata.Title, book.Status
    FROM bookdata
    NATURAL JOIN book
    WHERE 1
    """
    # , author.Name
    # LEFT JOIN author ON bookdata.BookID = author.BookID

    search_params = []
    # Add search term condition
    if search_term:
        query += """
            AND (
                bookdata.Title LIKE %s
                OR bookdata.Description LIKE %s
            )
        """
        # OR author.Name LIKE %s
        search_params.extend([f"%{search_term}%"]*2)

    # Add advanced search conditions
    for field, value in filter(lambda x: x[1] != '', advanced_search_fields.items()):
        query += f" AND {field} = %s"
        search_params.append(value)

    # Add pagination
    offset = (page_number - 1) * results_per_page
    query += f" LIMIT {results_per_page} OFFSET {offset}"
    # return query, search_params

    with MySQLdb.connect("db") as conn:
        cursor = get_cursor(conn)

        if search_term or advanced_search_fields:
            cursor.execute(query, search_params)
        else:
            cursor.execute(query)

        # Fetch the results
        results = cursor.fetchall()
    return results, query

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
        # raw_search = form.cleaned_data['raw_search']
        # author = form.cleaned_data['author']
        # genre = form.cleaned_data['genre']
        # in_stock = form.cleaned_data['in_stock']
        # decimal_code = form.cleaned_data['decimal_code']
        search_query = form.cleaned_data['raw_search']
        advanced_search = {}
        advanced_search["author.Name"] = form.cleaned_data['author']
        advanced_search["category.CategoryName"] = form.cleaned_data['genre']
        advanced_search["book.Status"] = form.cleaned_data['in_stock']
        advanced_search["book.DecimalCode"] = form.cleaned_data['decimal_code']
        results, query = construct_query(search_query, advanced_search, 1, 50)
        # query = "SELECT BookData. FROM BookData LEFT JOIN Author ON BookData.BookID = Author.BookID"
        # if 'raw_search' in fields:
        #     query += "WHERE  IN ()"
        # data = str(form.cleaned_data)
        data = query
        print(results)
        return render(request, "search.html", {"form_data":data, "good":fields, "results":results})
    return render(request, "search.html")


def landing(request):
    return render(request,"landing.html")

def lib(request):
    return render(request,'librarian.html')

def patron(request):
    return render(request,"patron.html")

def test(request):
    message = "test succesful"
    return render(request,"test.html")

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
