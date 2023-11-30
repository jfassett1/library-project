from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import datetime


class SearchForm(forms.Form):
    OPTIONS = (
        (0, "In stock"),
        (1,"Out of stock"),
        (2, "Reserved"),
    )
    raw_search = forms.CharField(label="Search", max_length=100, required=False)
    title = forms.CharField(label="Title", max_length=100, required=False)
    lower_publish_year = forms.IntegerField(
        label="Minimum Year", initial=-9999, min_value=-9999, required=False
    )
    upper_publish_year = forms.IntegerField(
        label="Maximum Year",
        initial=datetime.date.today().year,
        min_value=-9999,
        required=False,
    )
    author = forms.CharField(label="Author", max_length=60, required=False)
    publisher = forms.CharField(label="Publisher", max_length=60, required=False)
    ## change later to show most popular genres or supergenres
    ## with checkboxes to select the one you want
    genre = forms.CharField(label="Genre", max_length=100, required=False)
    in_stock = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=OPTIONS,
        initial=2,
        required=False,  # Set the default choice here
    )
    # isbn = forms.CharField(label="ISBN", max_length=13, required=False)
    decimal_code = forms.CharField(label="Decimal Code", max_length=12, required=False)
    page = forms.IntegerField(min_value=1, widget=forms.HiddenInput(), initial=1)


class addForm(forms.Form):
    title = forms.CharField(label="Title", max_length=100, required=True)
    author = forms.CharField(label="Author", max_length=60, required=False)
    category = forms.CharField(label="Category", max_length=200, required=False)
    year = forms.IntegerField(
        label="Year of Publication", min_value=-9999, max_value=2100, required=False
    )
    publisher = forms.CharField(label="Publisher", max_length=200, required=False)
    desc = forms.CharField(label="Description", widget=forms.Textarea(), required=False)


class rmForm(forms.Form):
    searchoptions = ((0, "BookID"), (1, "Decimal"))
    SEARCHBY = forms.ChoiceField(
        widget=forms.RadioSelect, choices=searchoptions, initial="BookID", required=True
    )
    decimal = forms.CharField(label="Decimal Code", max_length=12, required=False)
    bookid = forms.CharField(label="BookID", max_length=12, required=False)

    # title = forms.CharField(label="Title", max_length=100, required=True)
    # author = forms.CharField(label="Author", max_length=60, required=True)
    # genre = forms.CharField(label="Genre", max_length=50, required=True)
    # categoryID = forms.IntegerField(label="CategoryID",min_value=0,max_value=10000)
    # year = forms.IntegerField(label="Year of Publication",min_value=0,max_value=2100)
    # publisher = forms.CharField(label="Publisher",max_length = 50,required=True)
    # desc = forms.CharField(label="Description",max_length = 300,required=True)


class ReturnForm(forms.Form):
    decimal = forms.CharField(label="Decimal Code", max_length=20, required=True)
