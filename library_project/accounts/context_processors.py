def user_context(request):
    return {
        'login': request.user.is_authenticated,
        'Name': request.user.get_full_name() if request.user.is_authenticated else None
    }