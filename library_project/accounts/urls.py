from django.urls import path

from .views import SignUpView,logout_user,profile_view,make_staff


urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("exit/",logout_user,name='logout'),
    path("profile/",profile_view,name="profile"),
    path("make_staff/",make_staff,name="make_staff")
    # path("login/",LoginView.as_view(),template_name='registration/login.html')
]