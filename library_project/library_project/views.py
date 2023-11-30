import json
import logging

# from . import initialize_db
import MySQLdb
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from utils.general import find_similar_books, process_search_form
from utils.general import (
    get_copy_details, user_waitlist,
    user_checkout, get_book_details,
    make_recommendation, construct_search_query
)


from .forms import SearchForm, addForm, rmForm
from .initialization.db_connect import get_cursor

logger = logging.getLogger('django')


def homepage(request):
    form = SearchForm()
    if not request.user.is_authenticated:
        return render(request,"home.html",{"form":form,"info":""})
    return make_recommendation(request, form)

def search(request):
    if request.method == "GET":
        form = SearchForm(request.GET)

        # check whether it's valid:
        if not form.is_valid():
            return render(request, "search/search.html")


        search_query, advanced_search, page = process_search_form(form)
        RESULTS_PER_PAGE = 50
        results, query, qfields = construct_search_query(search_query, advanced_search, page, RESULTS_PER_PAGE)
        results_numbers = (page-1) * RESULTS_PER_PAGE

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
                "num_res":(results_numbers, results_numbers + len(results))
                }
            )
    return render(request, "search/search.html")


def detailed_results(request, bookid):

    #Code for recommendations
    with MySQLdb.connect('db') as conn:
        cursor = get_cursor(conn)
        query = f"""SELECT Title FROM bookdata WHERE BookID = {bookid}"""
        cursor.execute(query)
        try:
            info = cursor.fetchall()[0][0]
            cursor.close()
        except MySQLdb.Error:
            info = ""
        # return render(request,"home.html",{"form":form,"info":info})
    #Recommendation code
    recommendations = find_similar_books(request, info)


    results = get_book_details(bookid)
    results["books"] = list(zip(results["codes"], results["status"]))
    results["best_status"] = min(results["status"])
    return render(request, "search/details.html", {"results":results,"lastbook":info,"info":recommendations})



@login_required
def checkout_book(request):

    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        print(body)
        book = get_copy_details(**body)

        # Check if the book is available
        if book is True:
            # Perform the checkout
            response = user_checkout(request.user, body["book_id"])
            return JsonResponse({'success': response})
        else:
            # Add the user to the waitlist
            response = user_waitlist(request.user, body["book_id"])
            return JsonResponse({'waitlisted': response})

    # If the request method is not POST, return an error response
    return JsonResponse({'error': 'Invalid request method'})


@staff_member_required
def update(request):
    return render(request,"update/update.html",{"addForm":addForm(),
                                                "rmForm":rmForm()})


def change(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == 'add':
            return add_row(request)
        elif action == 'remove':
            return remove_row(request)
        else:
            return HttpResponse("epic fail")


def remove_row(request):
    if request.method == "POST":
        form = rmForm(request.POST)
        if form.is_valid():
            conn = MySQLdb.connect("db")
            cursor = get_cursor(conn,"library")

            searchby = form.cleaned_data['SEARCHBY']
            decimal = form.cleaned_data['decimal']
            bookID = form.cleaned_data['bookid']
            if not (decimal or bookID):
                return HttpResponse("Input at least one field")

            #Depending on searchby
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
            return render(request,"update/change.html",{'message':message,'query':query})
    return HttpResponse("Invalid request method")


def add_row(request):
    if request.method == "POST":
        form = addForm(request.POST)
        if form.is_valid():

            conn = MySQLdb.connect("db")
            cursor = get_cursor(conn,"library")

            # Form data is valid, so you can process and save it to the database

            title = form.cleaned_data['title']
            author = form.cleaned_data['author']
            publisher = form.cleaned_data['publisher']
            category = form.cleaned_data['category']
            year = form.cleaned_data['year']
            descript = form.cleaned_data['desc'].replace("'","''")

            query_bookdata = f"""INSERT INTO bookdata (Title, PublishDate, Publisher, Description) VALUES ('{title}',{year},'{publisher}','{descript}')"""
            query_author = "INSERT INTO author (BookID, Name) VALUES (%s, %s)"
            query_category = "INSERT INTO category (BookID, CategoryName) VALUES (%s,%s)"
            queries = []

            try:
                #Bookdata Query
                cursor.execute(query_bookdata)
                #Gets bookID
                bookID = cursor.lastrowid
                #Author Query
                cursor.execute(query_author,(bookID,author))
                cursor.execute(query_category,(bookID,category))

                conn.commit()
                message = mark_safe(f'Insert Successful!<br>{bookID}')
            except MySQLdb.Error as e:
                message = e
            return render(request,"update/change.html",{'message':message,'query':query_bookdata})
    return HttpResponse("Invalid request method")



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
        message = f'Database connection failed: {e}'
    return JsonResponse({"message":message})
