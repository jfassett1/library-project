from django.urls import path

from .views import SignUpView
from .views import logout_user


urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("exit/",logout_user,name='logout')
    # path("login/",LoginView.as_view(),template_name='registration/login.html')
]