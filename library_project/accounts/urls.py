from django.urls import path

from .views import SignUpView


urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    # path("login/",LoginView.as_view(),template_name='registration/login.html')
]