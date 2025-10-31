from django.contrib.auth import logout as django_logout
from ..models import Moto, Servicos, Agendamento, OrdemServico, Mecanico, Cliente, Administrador
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from datetime import date
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from ..forms import EditarClienteForm, ClienteRegistrationForm, MecanicoRegistrationForm, EditarMecanicoForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError


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
    """Página de gerenciamento de agendamentos"""
    if not (hasattr(request.user, 'administrador') or request.user.is_staff):
        messages.error(request, 'Acesso negado.')
        return redirect('login')
    
    agendamentos = Agendamento.objects.all().select_related(
        'cliente__usuario', 'moto', 'servico', 'mecanico__usuario'
    )
    context = {
        'agendamentos': agendamentos
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
        # Implementar lógica de edição aqui
        messages.success(request, 'Agendamento atualizado com sucesso!')
        return redirect('adm-agendamentos')
    
    # Por enquanto, apenas redireciona de volta
    messages.info(request, 'Edição de agendamentos será implementada em breve.')
    return redirect('adm-agendamentos')


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

