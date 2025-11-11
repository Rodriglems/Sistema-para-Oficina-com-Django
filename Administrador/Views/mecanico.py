from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Mecanico, Agendamento, OrdemServico


@login_required
def dashboard_mecanico(request):
    """Dashboard principal do mecânico"""
    ordens_servico = OrdemServico.objects.all()
    context = {
        'ordens_servico': ordens_servico,
        'descricao_clinte':
    }
    return render(request, 'Mecanico/dashbord-mecanico.html', context)

def painel_mecanico(request):
    return render(request, 'Mecanico/dashboard-mecanico.html')

def ordens_servico(request):
    return render(request, 'Mecanico/ordens-servico.html')

def logout_mecanico(request):
    django_logout(request)
    return redirect('login')