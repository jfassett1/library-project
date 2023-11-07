from django.shortcuts import render
from django.http import HttpResponse


def landing(request):
    return render(request,"landing.html")

def lib(request):
    return render(request,'librarian.html')
def patron(request):
    return render(request,"patron.html")