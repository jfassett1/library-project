from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# from . import initialize_db
import MySQLdb
from .forms import SearchForm
import utils.select_query


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
        # isbn = form.cleaned_data['isbn']
        # decimal_code = form.cleaned_data['decimal_code']
        query = "SELECT BookData. FROM BookData LEFT JOIN Author ON BookData.ISBN = Author.ISBN"
        if 'raw_search' in fields:
            query += "WHERE  IN ()"
        data = str(form.cleaned_data)
        return render(request, "search.html", {"form_data":data, "good":fields})
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
