from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout


def painel_mecanico(request):
    return render(request, 'Mecanico/painel-mecanico.html')

def ordens_servico(request):
    return render(request, 'Mecanico/ordens-servico.html')

def logout_mecanico(request):
    django_logout(request)
    return redirect('login')