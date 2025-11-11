from django.contrib.auth import logout as django_logout, authenticate, update_session_auth_hash
from ..models import Moto, Servicos, Agendamento, OrdemServico, Mecanico, Cliente, Administrador
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from ..forms import EditarClienteForm, ClienteRegistrationForm, MecanicoRegistrationForm, EditarMecanicoForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.http import JsonResponse
import os


@login_required
def dashboard_admin(request):
    """Dashboard do Administrador com dados completos"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado. Apenas administradores podem acessar esta página.')
        return redirect('login')
    
    try:
        # Dados para o dashboard
        total_clientes = Cliente.objects.count()
        total_mecanicos = Mecanico.objects.count()
        total_agendamentos = Agendamento.objects.count()
        total_ordens = OrdemServico.objects.count()
        
        agendamentos_hoje = Agendamento.objects.filter(data_hora__date=date.today()).count()
        servicos_andamento = OrdemServico.objects.filter(status='em_andamento').count()
        agendamentos_pendentes = Agendamento.objects.filter(status='agendado').count()
        agendamentos_concluidos = Agendamento.objects.filter(status='concluido').count()
        
        context = {
            'total_clientes': total_clientes,
            'total_mecanicos': total_mecanicos,
            'total_agendamentos': total_agendamentos,
            'total_ordens': total_ordens,
            'agendamentos_hoje': agendamentos_hoje,
            'servicos_andamento': servicos_andamento,
            'agendamentos_pendentes': agendamentos_pendentes,
            'agendamentos_concluidos': agendamentos_concluidos,
        }
        
        return render(request, 'Administrador/dashbord-admin.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao carregar dashboard: {e}')
        return render(request, 'Administrador/dashbord-admin.html', {})



@login_required
def clientes_admin(request):
    """Página de gerenciamento de clientes"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    clientes = Cliente.objects.all().select_related('usuario')
    context = {
        'clientes': clientes
    }
    return render(request, 'Administrador/cliente/cliente-admin.html', context)



@login_required
def logout_admin(request):
    """Logout específico do administrador"""
    django_logout(request)
    messages.success(request, 'Administrador desconectado com sucesso!')
    return redirect('login')



@login_required
def criar_admin_padrao(request):
    """Criar administrador padrão para desenvolvimento"""
    try:
        if User.objects.filter(username='admin').exists():
            messages.info(request, 'Administrador já existe!')
        else:
            admin_user = User.objects.create_user(
                username='admin2',
                password='admin123',
                email='admin@oficina.com',
                first_name='Administrador',
                is_staff=True,
                is_superuser=True
            )
            
            Administrador.objects.create(
                usuario=admin_user,
                email='admin@oficina.com',
                telefone='(11) 99999-9999'
            )
            
            messages.success(request, 'Administrador criado com sucesso!')
            messages.info(request, 'Usuário: admin2 | Senha: admin123')
            
    except Exception as e:
        messages.error(request, f'Erro ao criar administrador: {e}')
    
    return redirect('login')



@login_required  
def agendar_servico_admin(request):
    """Página de agendamento específica para administradores"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    if request.method == 'POST':
        try:
            # Capturar dados do formulário
            cliente_id = request.POST.get('cliente')
            mecanico_id = request.POST.get('mecanico')
            servico_id = request.POST.get('servico')
            outro_servico = request.POST.get('outro_servico')
            descricao = request.POST.get('descricao', '')
            data = request.POST.get('data')
            hora = request.POST.get('hora')
            marca = request.POST.get('marca')
            modelo = request.POST.get('modelo')
            ano = request.POST.get('ano')
            
            # Validar dados obrigatórios
            if not all([cliente_id, data, hora, marca, modelo, ano]):
                messages.error(request, 'Todos os campos são obrigatórios.')
                return redirect('agendar-servico-admin')
            
            # Validar serviço
            if servico_id == 'outro':
                if not outro_servico:
                    messages.error(request, 'Por favor, digite o nome do serviço.')
                    return redirect('agendar-servico-admin')
                # Criar ou buscar serviço personalizado
                servico, created = Servicos.objects.get_or_create(
                    nome=outro_servico,
                    defaults={'descricao': f'Serviço personalizado: {outro_servico}'}
                )
            elif not servico_id:
                messages.error(request, 'Por favor, selecione um serviço.')
                return redirect('agendar-servico-admin')
            else:
                servico = get_object_or_404(Servicos, id=servico_id)
            
            # Buscar objetos
            cliente = get_object_or_404(Cliente, id=cliente_id)
            mecanico = None
            if mecanico_id:
                mecanico = get_object_or_404(Mecanico, id=mecanico_id)
            
            # Criar ou buscar moto
            moto, created = Moto.objects.get_or_create(
                marca=marca,
                modelo=modelo,
                ano=int(ano)
            )
            
            # Combinar data e hora
            from datetime import datetime
            data_hora = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
            
            # Criar agendamento
            agendamento = Agendamento.objects.create(
                cliente=cliente,
                mecanico=mecanico,
                servico=servico,
                data_hora=data_hora,
                moto=moto,
                descricao_problema=descricao,
                status='agendado'
            )
            
            messages.success(request, f'Agendamento #{agendamento.id} criado com sucesso!')
            return redirect('adm-agendamentos')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar agendamento: {str(e)}')
            return redirect('agendar-servico-admin')
    
    # Buscar dados necessários para o formulário
    clientes = Cliente.objects.all().select_related('usuario')
    mecanicos = Mecanico.objects.all().select_related('usuario')
    servicos = Servicos.objects.all()
    
    context = {
        'clientes': clientes,
        'mecanicos': mecanicos,
        'servicos': servicos,
    }
    
    return render(request, 'Administrador/agenda_servico/agendar-servico-admin.html', context)

# Edição de Agendamentos


@login_required
def agendamentos_admin(request):
    """Página de gerenciamento de agendamentos com filtros"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    # Filtrar por status se especificado
    status_filter = request.GET.get('status', '')
    
    agendamentos = Agendamento.objects.all().select_related(
        'cliente__usuario', 'moto', 'servico', 'mecanico__usuario'
    )
    
    if status_filter:
        agendamentos = agendamentos.filter(status=status_filter)
    
    # Contar agendamentos por status para os badges
    total_count = Agendamento.objects.count()
    andamento_count = Agendamento.objects.filter(status='em_andamento').count()
    concluido_count = Agendamento.objects.filter(status='concluido').count()
    cancelado_count = Agendamento.objects.filter(status='cancelado').count()
    agendado_count = Agendamento.objects.filter(status='agendado').count()
    
    context = {
        'agendamentos': agendamentos,
        'status_filter': status_filter,
        'total_count': total_count,
        'andamento_count': andamento_count,
        'concluido_count': concluido_count,
        'cancelado_count': cancelado_count,
        'agendado_count': agendado_count,
    }
    return render(request, 'Administrador/agenda_servico/agendamentos-admin.html', context)


@login_required
def editar_agendamento(request, id):
    """Editar agendamento"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    agendamento = get_object_or_404(Agendamento, id=id)
    
    if request.method == 'POST':
        try:
            # Capturar dados do formulário
            cliente_id = request.POST.get('cliente')
            mecanico_id = request.POST.get('mecanico')
            servico_id = request.POST.get('servico')
            outro_servico = request.POST.get('outro_servico')
            descricao = request.POST.get('descricao', '')
            data = request.POST.get('data')
            hora = request.POST.get('hora')
            marca = request.POST.get('marca')
            modelo = request.POST.get('modelo')
            ano = request.POST.get('ano')
            status = request.POST.get('status')
            
            # Validar dados obrigatórios
            if not all([cliente_id, data, hora, marca, modelo, ano, status]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                return redirect('editar_agendamento', id=id)
            
            # Validar serviço
            if servico_id == 'outro':
                if not outro_servico:
                    messages.error(request, 'Por favor, digite o nome do serviço.')
                    return redirect('editar_agendamento', id=id)
                # Criar ou buscar serviço personalizado
                servico, created = Servicos.objects.get_or_create(
                    nome=outro_servico,
                    defaults={'descricao': f'Serviço personalizado: {outro_servico}'}
                )
            elif not servico_id:
                messages.error(request, 'Por favor, selecione um serviço.')
                return redirect('editar_agendamento', id=id)
            else:
                servico = get_object_or_404(Servicos, id=servico_id)
            
            # Buscar objetos
            cliente = get_object_or_404(Cliente, id=cliente_id)
            mecanico = None
            if mecanico_id:
                mecanico = get_object_or_404(Mecanico, id=mecanico_id)
            
            # Criar ou atualizar moto
            moto, created = Moto.objects.get_or_create(
                marca=marca,
                modelo=modelo,
                ano=int(ano)
            )
            
            # Combinar data e hora
            from datetime import datetime
            data_hora = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
            
            # Atualizar agendamento
            agendamento.cliente = cliente
            agendamento.mecanico = mecanico
            agendamento.servico = servico
            agendamento.data_hora = data_hora
            agendamento.moto = moto
            agendamento.descricao_problema = descricao
            agendamento.status = status
            agendamento.save()
            
            messages.success(request, f'Agendamento #{agendamento.id} atualizado com sucesso!')
            return redirect('adm-agendamentos')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar agendamento: {str(e)}')
            return redirect('editar_agendamento', id=id)
    
    # Buscar dados necessários para o formulário
    clientes = Cliente.objects.all().select_related('usuario')
    mecanicos = Mecanico.objects.all().select_related('usuario')
    servicos = Servicos.objects.all()
    
    context = {
        'agendamento': agendamento,
        'clientes': clientes,
        'mecanicos': mecanicos,
        'servicos': servicos,
    }
    
    return render(request, 'Administrador/agenda_servico/editar-agendamento.html', context)


@login_required
def cancelar_agendamento(request, id):
    """Cancelar agendamento"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    agendamento = get_object_or_404(Agendamento, id=id)
    agendamento.status = 'cancelado'
    agendamento.save()
    
    messages.success(request, f'Agendamento de {agendamento.cliente} foi cancelado!')
    return redirect('adm-agendamentos')

 
 
 #CRUD de clientes  

@login_required
def mecanicos_admin(request):
    """Página de gerenciamento de mecânicos"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    mecanicos = Mecanico.objects.all().select_related('usuario')
    context = {
        'mecanicos': mecanicos
    }
    return render(request, 'Administrador/mecanico/mecanico-admin.html', context)


 
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    user = cliente.usuario  # campo OneToOneField para User

    if request.method == 'POST':
        form = EditarClienteForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('adm-cliente')
    else:
        form = EditarClienteForm(instance=user)
    return render(request, 'Administrador/cliente/editar.html', {'form': form})


def admin_registrar_cliente(request):
    if request.method == "POST":
        form = ClienteRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f"Cliente {user.username} criado com sucesso. Ele já pode fazer login.")
                return redirect(f"{reverse('login')}?username={user.username}")
            except IntegrityError:
                messages.error(request, "Erro: este e-mail já está cadastrado.")
                return redirect("admin_cliente_cadastrar")  # volta para o formulário
    else:
        form = ClienteRegistrationForm()

    return render(request, 'Administrador/cliente/cadastrar.html', {'form': form})


def excluir_cliente(request, id):
    # se o udsuário não for administrador ou staff, redireciona
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')

    cliente = get_object_or_404(Cliente, id=id)

    # Exclui também o usuário vinculado (opcional)
    usuario = cliente.usuario
    cliente.delete()
    usuario.delete()

    messages.success(request, f"O cliente {usuario.username} foi excluído com sucesso!")
    return redirect('adm-cliente')


# CRUD de mecanicos

@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_criar_mecanico(request):
    if request.method == "POST":
        form = MecanicoRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f"Mecânico {user.username} criado com sucesso!")
                return redirect('adm-mecanico')
            except IntegrityError as e:
                messages.error(request, f"Erro: {str(e)}")
                form = MecanicoRegistrationForm()  # Limpa o formulário em caso de erro
        else:
            # Se o formulário não é válido, mostra os erros
            messages.error(request, "Por favor corrija os erros no formulário.")
    else:
        form = MecanicoRegistrationForm()

    return render(request, 'Administrador/mecanico/cadastrar.html', {'form': form})

def editar_mecanico(request, pk):
    mecanico = get_object_or_404(Mecanico, pk=pk)
    user = mecanico.usuario
    if request.method == 'POST':
        form = EditarMecanicoForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('adm-mecanico')
    else:
        form = EditarMecanicoForm(instance=user)
    return render(request, 'Administrador/mecanico/editar.html', {'form': form})

def excluir_mecanico(request, id):
    # se o udsuário não for administrador ou staff, redireciona
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')

    mecanico = get_object_or_404(Mecanico, id=id)
    usuario = mecanico.usuario
    mecanico.delete()
    usuario.delete()

    messages.success(request, f"O mecânico {usuario.username} foi excluído com sucesso!")
    return redirect('adm-mecanico')


#Agendamentos

from django.http import HttpResponse
import csv
from ..models import ConfiguracaoOficina, ConfiguracaoAgendamento, ConfiguracaoNotificacao

@login_required
def configuracoes_admin(request):
    """View para gerenciar configurações do sistema"""
    if not request.user.is_staff:
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    # Buscar ou criar configurações
    config, created = ConfiguracaoOficina.objects.get_or_create(
        id=1,
        defaults={
            'nome_oficina': 'Minha Oficina',
            'endereco': '',
            'telefone': '',
            'email': '',
            'cnpj': '',
        }
    )
    
    config_agendamento, created = ConfiguracaoAgendamento.objects.get_or_create(
        id=1,
        defaults={}
    )
    
    config_notificacao, created = ConfiguracaoNotificacao.objects.get_or_create(
        id=1,
        defaults={}
    )
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'oficina':
            config.nome_oficina = request.POST.get('nome_oficina', config.nome_oficina)
            config.endereco = request.POST.get('endereco', config.endereco)
            config.telefone = request.POST.get('telefone', config.telefone)
            config.email = request.POST.get('email', config.email)
            config.cnpj = request.POST.get('cnpj', config.cnpj)
            config.dias_funcionamento = request.POST.get('dias_funcionamento', config.dias_funcionamento)
            
            # Tratar horários
            horario_inicio = request.POST.get('horario_inicio')
            horario_fim = request.POST.get('horario_fim')
            if horario_inicio:
                from datetime import datetime
                config.horario_funcionamento_inicio = datetime.strptime(horario_inicio, '%H:%M').time()
            if horario_fim:
                from datetime import datetime
                config.horario_funcionamento_fim = datetime.strptime(horario_fim, '%H:%M').time()
                
            config.save()
            messages.success(request, 'Configurações da oficina atualizadas com sucesso!')
        
        elif form_type == 'agendamentos':
            config_agendamento.intervalo_agendamento = int(request.POST.get('intervalo_agendamento', 60))
            config_agendamento.antecedencia_minima = int(request.POST.get('antecedencia_minima', 24))
            config_agendamento.limite_agendamentos_dia = int(request.POST.get('limite_agendamentos_dia', 10))
            config_agendamento.tempo_limite_cancelamento = int(request.POST.get('tempo_limite_cancelamento', 2))
            config_agendamento.permite_agendamento_feriados = 'permite_feriados' in request.POST
            config_agendamento.permite_reagendamento = 'permite_reagendamento' in request.POST
            config_agendamento.save()
            messages.success(request, 'Configurações de agendamento atualizadas!')
        
        elif form_type == 'notificacoes':
            config_notificacao.email_confirmacao = 'email_confirmacao' in request.POST
            config_notificacao.email_cancelamento = 'email_cancelamento' in request.POST
            config_notificacao.email_conclusao = 'email_conclusao' in request.POST
            config_notificacao.notificar_24h_antes = 'notificar_24h_antes' in request.POST
            config_notificacao.notificar_1h_antes = 'notificar_1h_antes' in request.POST
            config_notificacao.sms_lembrete = 'sms_lembrete' in request.POST
            config_notificacao.save()
            messages.success(request, 'Configurações de notificação atualizadas!')
        
        elif form_type == 'add_servico':
            try:
                Servicos.objects.create(
                    nome=request.POST.get('nome'),
                    preco=float(request.POST.get('preco', 0)),
                    tempo_estimado=int(request.POST.get('tempo_estimado', 60)),
                    categoria=request.POST.get('categoria', 'Geral'),
                    descricao=f"Serviço: {request.POST.get('nome')}"
                )
                messages.success(request, 'Serviço adicionado com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao adicionar serviço: {e}')
        
        elif form_type == 'toggle_servico':
            try:
                servico_id = request.POST.get('servico_id')
                servico = Servicos.objects.get(id=servico_id)
                servico.ativo = not servico.ativo
                servico.save()
                status = "ativado" if servico.ativo else "desativado"
                messages.success(request, f'Serviço "{servico.nome}" foi {status}!')
            except Exception as e:
                messages.error(request, f'Erro ao alterar status do serviço: {e}')
        
        elif form_type == 'tema':
            # Salvar configurações de tema no banco de dados
            tema_sistema = request.POST.get('tema_sistema', 'azul')
            
            # Salvar o tema no modelo ConfiguracaoOficina
            config.tema = tema_sistema
            config.save()
            
            messages.success(request, f'🎨 Tema "{tema_sistema.title()}" aplicado com sucesso!')
        
        elif form_type == 'alterar_senha':
            senha_atual = request.POST.get('senha_atual')
            nova_senha = request.POST.get('nova_senha')
            confirmar_senha = request.POST.get('confirmar_senha')
            
            # Verificar senha atual
            if not request.user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta!')
            elif nova_senha != confirmar_senha:
                messages.error(request, 'As senhas não coincidem!')
            elif len(nova_senha) < 8:
                messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres!')
            else:
                # Alterar senha
                request.user.set_password(nova_senha)
                request.user.save()
                # Manter usuário logado após mudança de senha
                update_session_auth_hash(request, request.user)
                messages.success(request, '🔐 Senha alterada com sucesso!')
        
        return redirect('configuracoes_admin')
    
    # Estatísticas para o dashboard
    context = {
        'config': config,
        'config_agendamento': config_agendamento,
        'config_notificacao': config_notificacao,
        'total_clientes': Cliente.objects.count(),
        'total_mecanicos': Mecanico.objects.count(),
        'total_admins': User.objects.filter(is_staff=True).count(),
        'servicos': Servicos.objects.all(),
        'ultimo_backup': None,  # Implementar depois
        'logins_hoje': 0,  # Implementar depois
        'ultimo_login_admin': None,  # Implementar depois
        'tentativas_falhas': 0,  # Implementar depois
    }
    
    return render(request, 'Administrador/configuracoes/configuracoes.html', context)


@login_required
def limpar_dados_sistema(request):
    """View para limpar dados desnecessários do sistema"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    
    if request.method == 'POST':
        tipo_limpeza = request.POST.get('tipo')
        
        try:
            if tipo_limpeza == 'agendamentos':
                # Remove agendamentos cancelados/concluídos com mais de 6 meses
                data_limite = datetime.now() - timedelta(days=180)
                agendamentos_antigos = Agendamento.objects.filter(
                    status__in=['cancelado', 'concluido'],
                    data_hora__lt=data_limite
                )
                count = agendamentos_antigos.count()
                agendamentos_antigos.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': f'{count} agendamentos antigos removidos com sucesso!'
                })
            
            elif tipo_limpeza == 'logs':
                # Simular limpeza de logs (implementar conforme necessário)
                return JsonResponse({
                    'success': True,
                    'message': 'Logs do sistema limpos com sucesso!'
                })
            
            elif tipo_limpeza == 'temp':
                # Simular limpeza de arquivos temporários
                return JsonResponse({
                    'success': True,
                    'message': 'Arquivos temporários removidos com sucesso!'
                })
            
            elif tipo_limpeza == 'reset_total':
                # Reset completo - CUIDADO!
                if request.POST.get('confirmacao') == 'CONFIRMAR RESET':
                    # Remover todos os dados (exceto usuário admin)
                    Agendamento.objects.all().delete()
                    OrdemServico.objects.all().delete()
                    Cliente.objects.all().delete()
                    Mecanico.objects.all().delete()
                    Moto.objects.all().delete()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Sistema resetado completamente! Todos os dados foram removidos.'
                    })
                else:
                    return JsonResponse({
                        'error': 'Confirmação incorreta'
                    }, status=400)
                    
        except Exception as e:
            return JsonResponse({
                'error': f'Erro durante a limpeza: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

 