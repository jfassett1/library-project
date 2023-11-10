from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# from . import initialize_db
import MySQLdb
from .forms import SearchForm
from utils.select_query import make_select_query


def homepage(request):
    form = SearchForm()
    return render(request, "home.html", {"form":form})

def search(request):
    if request.method == "POST":
        form = SearchForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            good = "yes"
        else:
            good = "no"
        data = str(form.cleaned_data)
        return render(request, "search.html", {"form_data":data, "good":good})
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
