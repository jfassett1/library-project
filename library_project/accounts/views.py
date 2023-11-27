from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
import MySQLdb
from library_project.initialization.db_connect import get_cursor


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import logout



def login(request):
    return render(request,"registration/login.html")


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
        login = True
        message = user_dict
        with MySQLdb.connect("db") as conn:
            cursor = get_cursor(conn)
            try:
                query = f"SELECT DecimalCode FROM checkout WHERE Patron = '{username}'"
                cursor.execute(query)
                data = cursor.fetchall()
            except MySQLdb.Error as e:
                data = e

    else:
        return redirect('login')
    return render(request, "registration/profile.html", {'identity':identity_dict,'system':system_info_dict,'status':status_dict,'username':username,"data":data})



class SignUpView(generic.CreateView):
    form_class = libraryForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


