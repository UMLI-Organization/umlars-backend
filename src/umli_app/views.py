from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'home.html', {})

def logout_user(request: HttpRequest) -> HttpResponse:
    pass