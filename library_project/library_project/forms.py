from django import forms
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

class addBook(forms.Form):
    book_id = forms.IntegerField(label="BookID", min_value=0, required=True)

class addPatron(forms.Form):
    name = forms.CharField(label="Name", max_length=50, required=True)
    address = forms.CharField(label = "Address",max_length=100)
    email = forms.EmailField(label="Email Address",max_length=40)

class addForm(forms.Form):
    title = forms.CharField(label="Title", max_length=100, required=True)
    author = forms.CharField(label="Author", max_length=60, required=False)
    category = forms.CharField(label="Category", max_length=200, required=False)
    year = forms.IntegerField(
        label="Year of Publication", min_value=-9999, max_value=2100, required=False
    )
    publisher = forms.CharField(label="Publisher", max_length=200, required=False)
    desc = forms.CharField(label="Description", widget=forms.Textarea(), required=False)


class alterBook(forms.Form):

    searchoptions = (("bookid", "BookID"), ("decimal", "Decimal"))
    SEARCHBY = forms.ChoiceField(
        widget=forms.RadioSelect, choices=searchoptions, initial="bookid", required=True
    )
    decimal = forms.CharField(label="Decimal Code", max_length=12, required=False)
    bookid = forms.CharField(label="BookID", max_length=12, required=False)

    fields = (
        ('title', 'Title'),
        ('author', 'Author'),
        ('category', 'Category'),
        ('publishdate', 'Year of Publication'),
        ('publisher', 'Publisher'),
        ('description', 'Description'),
    ) # type: ignore
    alterfields = forms.MultipleChoiceField(
        label="Which fields do you want to edit?",
        widget=forms.CheckboxSelectMultiple,
        choices=fields, # type: ignore
        # initial=[0],  # Assuming you want "BookID" as the initial choice
        required=True
    )

    title = forms.CharField(label="Title", max_length=100, required=False)
    author = forms.CharField(label="Author", max_length=60, required=False)
    category = forms.CharField(label="Category", max_length=200, required=False)
    publishdate = forms.IntegerField(
        label="Year of Publication", min_value=-9999, max_value=2100, required=False
    )
    publisher = forms.CharField(label="Publisher", max_length=200, required=False)
    description = forms.CharField(label="Description", widget=forms.Textarea(), required=False)

class alterPatron(forms.Form):
    accid = forms.IntegerField(label="Account ID",required=True)
    name = forms.CharField(label="Name", max_length=50, required=True)
    address = forms.CharField(label = "Address",max_length=100)
    email = forms.EmailField(label="Email Address",max_length=40)



class rmBook(forms.Form):
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

class rmPatron(forms.Form):
    searchoptions = ((0, "Name"), (1, "PatronID"))
    SEARCHBY = forms.ChoiceField(
        widget=forms.RadioSelect, choices=searchoptions, initial="Name", required=True
    )
    patron_name = forms.CharField(label="Name",max_length=100)
    patron_id = forms.IntegerField(label="Patron ID")


class ReturnForm(forms.Form):
    OPTIONS = (
        (0, "Checked Out"),
        (1,"Over Due"),
        (2, "Returned"),
        (3, "On Hold"),
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
    genre = forms.CharField(label="Genre", max_length=100, required=False)
    in_stock = forms.ChoiceField(
        label = "Status",
        widget=forms.RadioSelect,
        choices=OPTIONS,
        initial=0,
        required=False,  # Set the default choice here
    )
    decimal_code = forms.CharField(label="Decimal Code", max_length=12, required=False)
    user_name = forms.CharField(label="Patron Username", max_length=50, required=False)
    first_name = forms.CharField(label="First Name", max_length=120, required=False)
    last_name = forms.CharField(label="Last Name", max_length=120, required=False)
    email = forms.CharField(label="Email", max_length=120, required=False)
    page = forms.IntegerField(min_value=1, widget=forms.HiddenInput(), initial=1)

