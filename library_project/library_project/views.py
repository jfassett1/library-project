from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import MySQLdb
from forms import SearchForm

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def homepage(request):
    form = SearchForm()
    return render(request, "home.html", {"form":form})

@csrf_exempt
def search(request):

    if request.method == "GET":
        # data = request.GET
        form = SearchForm(request.GET)

        # check whether it's valid:
        if form.is_valid():
            good = "yes"
        else:
            good = "no"
        data= str(form.cleaned_data)
    return render(request, "search.html", {"form_data":data, "good":good})

def landing(request):
    return render(request,"landing.html")

def lib(request):

    return render(request,'librarian.html')
def patron(request):
    return render(request,"patron.html")

def test(request):
    message = "test succesful"
    return JsonResponse({"message":message})


def db_ping(request):
    try:
        # Attempt to establish a database connection
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
