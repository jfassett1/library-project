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


urlpatterns = [
    path("", views.homepage, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("search/", views.search, name='search-page'),
    path('admin/', admin.site.urls),
    path('db_ping/', views.db_ping, name='db_ping'),
    path("details/<int:bookid>/", views.detailed_results, name="book-details"),
    path("update/", views.update, name="update"),
    path('change/', views.change, name='change'),
    path('checkout-book/', views.checkout_book, name='checkout_book'),
    path('return-book/', views.return_book, name='return_book'),
    path('check-status/', views.check_status, name='check_status'),
    path("accounts/", include("accounts.urls")),  # new
]
