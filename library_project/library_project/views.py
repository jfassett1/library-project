from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
# from . import initialize_db
import MySQLdb



def landing(request):
    return render(request,"landing.html")

def lib(request):
    
    return render(request,'librarian.html')
def patron(request):
    return render(request,"patron.html")

def test(request):
    message = "test succesful"
    return render(request,"test.html")

from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt
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
