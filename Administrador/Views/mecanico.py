from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from ..models import Mecanico, Agendamento, OrdemServico


@login_required
def dashboard_mecanico(request):
    try:
        mecanico = Mecanico.objects.get(usuario=request.user)
    except Mecanico.DoesNotExist:
        messages.error(request, 'Perfil de mecânico não encontrado.')
        return redirect('login')
    
    # Agendamentos pendentes (status 'agendado') disponíveis para pegar
    agendamentos_pendentes = Agendamento.objects.filter(
        status='agendado'
    ).select_related('cliente', 'servico', 'moto').order_by('data_hora')

    # Agendamentos que o mecânico pegou e estão em andamento
    meus_agendamentos = Agendamento.objects.filter(
        mecanico=mecanico,
        status='em_andamento'
    ).select_related('cliente', 'servico', 'moto').order_by('data_hora')

    context = {
        'mecanico': mecanico,
        'agendamentos_pendentes': agendamentos_pendentes,
        'meus_agendamentos': meus_agendamentos
    }

    return render(request, 'Mecanico/dashbord-mecanico.html', context)


@login_required
def pegar_agendamento(request, agendamento_id):
    """
    Permite que o mecânico pegue um agendamento pendente e mude o status para 'em andamento'
    """
    try:
        mecanico = Mecanico.objects.get(usuario=request.user)
    except Mecanico.DoesNotExist:
        messages.error(request, 'Perfil de mecânico não encontrado.')
        return redirect('login')
    
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    
    # Verificar se o agendamento está disponível
    if agendamento.status != 'agendado':
        messages.warning(request, 'Este agendamento não está mais disponível.')
        return redirect('dashboard-mecanico')
    
    # Atribuir o mecânico e mudar o status
    agendamento.mecanico = mecanico
    agendamento.status = 'em_andamento'
    agendamento.save()
    
    messages.success(request, f'Agendamento pegado com sucesso! Cliente: {agendamento.cliente.nome_completo}')
    return redirect('dashboard-mecanico')


@login_required
def ver_servicos_pendentes(request):
    """
    Exibe uma página dedicada apenas aos serviços pendentes
    """
    try:
        mecanico = Mecanico.objects.get(usuario=request.user)
    except Mecanico.DoesNotExist:
        messages.error(request, 'Perfil de mecânico não encontrado.')
        return redirect('login')
    
    agendamentos_pendentes = Agendamento.objects.filter(
        status='agendado'
    ).select_related('cliente', 'servico', 'moto').order_by('data_hora')
    
    context = {
        'mecanico': mecanico,
        'agendamentos_pendentes': agendamentos_pendentes
    }
    
    return render(request, 'Mecanico/ver-servicos.html', context)


@login_required
def concluir_agendamento(request, agendamento_id):
    """
    Marca o agendamento como concluído e envia para o histórico
    """
    try:
        mecanico = Mecanico.objects.get(usuario=request.user)
    except Mecanico.DoesNotExist:
        messages.error(request, 'Perfil de mecânico não encontrado.')
        return redirect('login')
    
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    
    # Verificar se o agendamento pertence ao mecânico e está em andamento
    if agendamento.mecanico != mecanico:
        messages.error(request, 'Este agendamento não pertence a você.')
        return redirect('dashboard-mecanico')
    
    if agendamento.status != 'em_andamento':
        messages.warning(request, 'Este agendamento não está em andamento.')
        return redirect('dashboard-mecanico')
    
    # Se for POST, processar o formulário
    if request.method == 'POST':
        descricao_mecanico = request.POST.get('descricao_mecanico', '').strip()
        valor_servico = request.POST.get('valor_servico', '').strip()
        
        # Validar campos obrigatórios
        if not descricao_mecanico:
            messages.error(request, 'A descrição do serviço é obrigatória!')
            return redirect('dashboard-mecanico')
        
        if not valor_servico:
            messages.error(request, 'O valor do serviço é obrigatório!')
            return redirect('dashboard-mecanico')
        
        try:
            valor_servico = float(valor_servico.replace(',', '.'))
            if valor_servico <= 0:
                messages.error(request, 'O valor do serviço deve ser maior que zero!')
                return redirect('dashboard-mecanico')
        except ValueError:
            messages.error(request, 'Valor inválido! Use apenas números.')
            return redirect('dashboard-mecanico')
        
        # Salvar descrição e valor
        agendamento.descricao_mecanico = descricao_mecanico
        agendamento.valor_servico = valor_servico
        agendamento.status = 'concluido'
        agendamento.save()
        
        messages.success(request, f'Serviço concluído com sucesso! Cliente: {agendamento.cliente.nome_completo} | Valor: R$ {valor_servico:.2f}')
        return redirect('dashboard-mecanico')
    
    # Se for GET, não deveria chegar aqui, redirecionar
    messages.warning(request, 'Preencha a descrição e o valor para concluir o serviço.')
    return redirect('dashboard-mecanico')


@login_required
def cancelar_agendamento_mecanico(request, agendamento_id):
    """
    Cancela o agendamento e devolve para pendente (remove o mecânico)
    """
    try:
        mecanico = Mecanico.objects.get(usuario=request.user)
    except Mecanico.DoesNotExist:
        messages.error(request, 'Perfil de mecânico não encontrado.')
        return redirect('login')
    
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    
    # Verificar se o agendamento pertence ao mecânico e está em andamento
    if agendamento.mecanico != mecanico:
        messages.error(request, 'Este agendamento não pertence a você.')
        return redirect('dashboard-mecanico')
    
    if agendamento.status != 'em_andamento':
        messages.warning(request, 'Este agendamento não está em andamento.')
        return redirect('dashboard-mecanico')
    
    # Devolver para pendente
    agendamento.mecanico = None
    agendamento.status = 'agendado'
    agendamento.save()
    
    messages.info(request, f'Agendamento devolvido para pendente. Cliente: {agendamento.cliente.nome_completo}')
    return redirect('dashboard-mecanico')


@login_required
def historico_mecanico(request):
    """
    Exibe o histórico de serviços concluídos e cancelados pelo mecânico
    """
    try:
        mecanico = Mecanico.objects.get(usuario=request.user)
    except Mecanico.DoesNotExist:
        messages.error(request, 'Perfil de mecânico não encontrado.')
        return redirect('login')
    
    # Buscar agendamentos concluídos e cancelados do mecânico
    agendamentos_concluidos = Agendamento.objects.filter(
        mecanico=mecanico,
        status='concluido'
    ).select_related('cliente', 'servico', 'moto').order_by('-data_hora')
    
    agendamentos_cancelados = Agendamento.objects.filter(
        mecanico=mecanico,
        status='cancelado'
    ).select_related('cliente', 'servico', 'moto').order_by('-data_hora')
    
    # Combinar todos os agendamentos e ordenar por data
    todos_agendamentos = list(agendamentos_concluidos) + list(agendamentos_cancelados)
    todos_agendamentos.sort(key=lambda x: x.data_hora, reverse=True)
    
    context = {
        'mecanico': mecanico,
        'agendamentos_concluidos': agendamentos_concluidos,
        'agendamentos_cancelados': agendamentos_cancelados,
        'todos_agendamentos': todos_agendamentos,
        'total_concluidos': agendamentos_concluidos.count(),
        'total_cancelados': agendamentos_cancelados.count(),
    }
    
    return render(request, 'Mecanico/historico-mecanico.html', context)


def painel_mecanico(request):
    return render(request, 'Mecanico/dashbord-mecanico.html')


def ordens_servico(request):
    return render(request, 'Mecanico/ordens-servico.html')


def logout_mecanico(request):
    django_logout(request)
    return redirect('login')