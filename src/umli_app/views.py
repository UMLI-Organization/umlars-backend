from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .models import UMLModel
from .forms import SignUpForm, AddUMLModel


def home(request: HttpRequest) -> HttpResponse:

    if request.method == 'POST':
        return login_user(request)
    else:
        uml_models = UMLModel.objects.prefetch_related('metadata').all()
        return render(request, 'home.html', {'uml_models': uml_models})


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


def register_user(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=password)
            login(request, user)

            messages.success(request, 'You have successfully registered')
            return redirect('home')
    else:
        form = SignUpForm()
    
    return render(request, 'register.html', {'form': form})


def uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model = UMLModel.objects.prefetch_related('metadata').get(id=pk)
        
        # Read and decode the file content
        # TODO: redo after final file format decision
        try:
            xml_content = uml_model.source_file.read().decode('utf-8')

            import xml.dom.minidom as minidom
            # Pretty-print the XML content
            pretty_xml = minidom.parseString(xml_content).toprettyxml(indent="  ")
        except ValueError:
            pretty_xml = uml_model.formatted_data
        
        return render(request, 'uml-model.html', {'uml_model': uml_model, 'pretty_xml': pretty_xml})
    else:
        messages.warning(request, 'You need to be logged in to view this page')
        return redirect('home')
    

def delete_uml_model(request: HttpRequest, pk: int) -> HttpResponse:
    if request.user.is_authenticated:
        uml_model_to_delete = UMLModel.objects.get(id=pk)
        uml_model_to_delete.delete()
        messages.success(request, 'UML model has been deleted.')
        return redirect('home')
    else:
        messages.warning(request, 'You need to be logged in to delete this UML model')
        return redirect('home')
    
    
def add_uml_model(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = AddUMLModel(request.POST, request.FILES)
            if request.method == 'POST':
                if form.is_valid():
                    added_uml_model = form.save()
                    messages.success(request, 'UML model has been added.')
                    return redirect('home')
        else:
            form = AddUMLModel()
    
        return render(request, 'add-uml-model.html', {'form': form})
    else:
        messages.warning(request, 'You need to be logged in to add a UML model')
        return redirect('home')
    
    