from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
import MySQLdb
from library_project.initialization.db_connect import get_cursor
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.utils.safestring import mark_safe
import datetime

def login(request):
    return render(request,"registration/login.html")


def make_staff(request):
    user = User.objects.get(username=request.user.username)
    user.is_staff = True
    user.save()
    return redirect('profile')


def logout_user(request):
    logout(request)
    return redirect('home')
class libraryForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = list(UserCreationForm.Meta.fields) + ['first_name', 'last_name', 'email']


def profile_view(request):

    if request.user.is_authenticated:
        #Gets info using session username
        user = User.objects.get(username=request.user.username)
        #Setting flags
        staff = False
        overdue = False
        login = True
        overdue_books = []

        if user.is_staff == True:
            staff = True

        user_attributes = [(field.verbose_name, getattr(user, field.name)) for field in User._meta.fields]
        user_dict = {key: value for key, value in user_attributes}
        user_dict.pop('password',None)

        #Manually groups into new dicts based on category. I ommitted status_keys because it didn't seem very relevant
        identity_keys = ['username', 'first name', 'last name', 'email address']
        status_keys = ['superuser status', 'staff status', 'active']
        system_info_keys = ['ID', 'last login', 'date joined']

        # Group the dictionary
        identity_dict = {k:user_dict[k] for k in identity_keys}
        status_dict = {k: user_dict[k] for k in status_keys}
        system_info_dict = {k: user_dict[k] for k in system_info_keys}
        username = identity_dict['username']
        book_checkout = {"Message":"No data"}


        with MySQLdb.connect("db") as conn:
            cursor = get_cursor(conn)
            try:
                query = f"""SELECT bd.title, c.DecimalCode,c.Due
                FROM checkout as c 
                INNER JOIN book as b
                ON c.DecimalCode = b.DecimalCode
                INNER JOIN bookdata as bd
                ON b.BookID = bd.BookID
                WHERE Patron = '{username}'"""
                cursor.execute(query)
                data = cursor.fetchall()
                data = list(data)

                book_checkout = {}

                for idx,entry in enumerate(data):
                    title = entry[0]
                    decimal = entry[1]
                    due = entry[2]
                    #Marked safe for convenience
                    book_checkout[idx+1] = mark_safe(f"<br>{title}<br>{decimal} <br> Due on: {due}")
                    time_difference = due - datetime.date.today()

                    if time_difference <= datetime.timedelta(days=0):
                        overdue_books.append(title)
                        overdue = True
            except MySQLdb.Error as e:
                data = e

    else:
        return redirect('login')
    return render(request, "registration/profile.html",
                   {'identity':identity_dict,
                    'system':system_info_dict,
                    'status':status_dict,
                    'username':username,
                    "checkoutdata":book_checkout,
                    "staff":staff,
                    "overdue":overdue,
                    "overdue_books":overdue_books})



class SignUpView(generic.CreateView):
    form_class = libraryForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


