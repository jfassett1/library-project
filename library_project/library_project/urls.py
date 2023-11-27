"""
URL configuration for library_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth.views import LoginView


urlpatterns = [
    path("", views.homepage, name="home"),
    # path("", views.landing, name = 'landing'),
    path("accounts/", include("django.contrib.auth.urls")),
    path("search/", views.search, name='search-page'),
    path("librarian/",views.lib, name = 'lib-view'),
    path("patron/",views.patron, name = 'patron-view'),
    path('admin/', admin.site.urls),
    path('db_ping/', views.db_ping, name='db_ping'),
    path("details/<int:bookid>/", views.detailed_results, name="book-details"),
    path("update/", views.update, name="update"),
    path('change/', views.change, name='change'),
    path('checkout-book/', views.checkout_book, name='checkout_book'),
    # path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path("accounts/", include("accounts.urls")),  # new
    # path("accounts/", include("django.contrib.auth.urls")),
    # path('signup/')
]
