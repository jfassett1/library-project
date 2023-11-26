from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User



def login(request):
    return render(request,"registration/login.html")



class libraryForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = list(UserCreationForm.Meta.fields) + ['first_name', 'last_name', 'email']


class SignUpView(generic.CreateView):
    form_class = libraryForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


