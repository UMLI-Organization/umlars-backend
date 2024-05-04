from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def home(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        return login_user(request)
    else:
        return render(request, 'home.html', {})

def login_user(request: HttpRequest) -> HttpResponse:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome {username}')
            return redirect('home')
        else:
            messages.warning(request, 'Invalid credentials')
            return redirect('home')

def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')