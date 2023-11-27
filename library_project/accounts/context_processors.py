#Adds context to each page. This is how I track acct information
import time
import datetime
def user_context(request):
    return {
        'login': request.user.is_authenticated,
        'Name': request.user.get_full_name() if request.user.is_authenticated else None,
        'staff': request.user.is_staff,
        'time': datetime.datetime.now()
    }