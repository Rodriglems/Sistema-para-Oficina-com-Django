from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django import forms
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .forms import ClienteRegistrationForm
from .models import Cliente



@ensure_csrf_cookie
@csrf_protect
@require_http_methods(["GET", "POST"])
def registrar_cliente(request):
    if request.method == "POST":
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # O método save() já cria o Cliente automaticamente
            return redirect('login')
    else:
        form = ClienteRegistrationForm()
    return render(request, 'Cliente/registro.html', {'form': form})