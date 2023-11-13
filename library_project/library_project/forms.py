from django import forms

class SearchForm(forms.Form):
    OPTIONS = ((0,"In stock"), (1,"Out of stock",), (2,"Reserved"))
    raw_search = forms.CharField(label="Search", max_length=100, required=True)
    # date_filter_lower = forms.DateField(label="Start Date", widget=forms.DateInput(attrs={'type': 'date'}))
    # date_filter_upper = forms.DateField(label="End Date", widget=forms.DateInput(attrs={'type': 'date'}))
    author = forms.CharField(label="Author", max_length=60, required=False)
    ## change later to show most popular genres or supergenres
    ## with checkboxes to select the one you want
    genre = forms.CharField(label="Genre", max_length="20", required=False)
    in_stock = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=OPTIONS,
        initial='Reserved',
        required=False # Set the default choice here
    )
    isbn = forms.CharField(label="ISBN", max_length=13, required=False)
    decimal_code = forms.CharField(label="Decimal Code", max_length=12, required=False)