from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout
from ..models import Moto, Servicos, Agendamento, OrdemServico, Mecanico
from ..models import Cliente
from django.contrib.auth import authenticate, login as login_user
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User
from ..models import Administrador
from django.contrib import messages

def Mostrar(request):
    # Exibe o dashboard do cliente com serviços, agendamentos futuros, último serviço e totais de status.
    servicos = Servicos.objects.all()
    agendamentos = []
    ultimo_servico = None
    total_finalizados = 0
    total_cancelados = 0
    total_pendentes = 0

    if request.user.is_authenticated:
        try:
            cliente = Cliente.objects.get(usuario=request.user)
            agendamentos = Agendamento.objects.filter(
                cliente=cliente, 
                data_hora__gte=timezone.now()
            ).order_by('data_hora')[:5]
            
            ultimo_servico = Agendamento.objects.filter(
                cliente=cliente,
                status='concluido'
            ).order_by('-data_hora').first()
            
            total_finalizados = Agendamento.objects.filter(cliente=cliente, status='concluido').count()
            total_cancelados = Agendamento.objects.filter(cliente=cliente, status='cancelado').count()
            total_pendentes = Agendamento.objects.filter(cliente=cliente, status='agendado').count()
            
        except Cliente.DoesNotExist:
            pass

    context = {
        'servicos': servicos,
        'agendamentos': agendamentos,
        'ultimo_servico': ultimo_servico,
        'total_finalizados': total_finalizados,
        'total_cancelados': total_cancelados,
        'total_pendentes': total_pendentes,
    }
    
    return render(request, 'Cliente/dasbord-cliente.html', context)

def login(request):
    """View de login unificado para clientes e administradores"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('senha')
        
        if not username or not password:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'LoginSistemy/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login_user(request, user)
            
            try:
                # Verificar se é um Administrador (staff ou superuser)
                if user.is_staff or user.is_superuser:
                    messages.success(request, f'Bem-vindo, Administrador {user.first_name or user.username}!')
                    return redirect('dashboard-admin')
                
                # Verificar se tem perfil de Administrador
                try:
                    admin_profile = Administrador.objects.get(usuario=user)
                    messages.success(request, f'Bem-vindo, Administrador {user.first_name or user.username}!')
                    return redirect('dashboard-admin')
                except Administrador.DoesNotExist:
                    pass
                
                # Verificar se tem perfil de Cliente
                try:
                    cliente_profile = Cliente.objects.get(usuario=user)
                    messages.success(request, f'Bem-vindo, {user.first_name or user.username}!')
                    return redirect('dashboard-cliente')
                except Cliente.DoesNotExist:
                    pass
                
                # Verificar se tem perfil de Mecânico
                try:
                    mecanico_profile = Mecanico.objects.get(usuario=user)
                    messages.success(request, f'Bem-vindo, Mecânico {user.first_name or user.username}!')
                    return redirect('dashboard-cliente')
                except Mecanico.DoesNotExist:
                    pass
                
                # Se não tem nenhum perfil específico, redirecionar para cliente
                messages.warning(request, 'Usuário sem perfil específico. Redirecionando...')
                return redirect('dashboard-cliente')
            except Exception as e:
                messages.error(request, f'Erro ao identificar usuário: {e}')
                return render(request, 'LoginSistemy/login.html')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'LoginSistemy/login.html')

def logout_view(request):
    django_logout(request)
    messages.success(request, 'Logout realizado com sucesso!')
    return redirect('login')

def dashboard_cliente(request):
    """Dashboard do cliente - redireciona para a função Mostrar"""
    return Mostrar(request)

def agendar_servico(request):
    if request.method == 'POST':
        # Dados da moto
        marca = request.POST.get('marca')
        modelo = request.POST.get('modelo')
        ano = request.POST.get('ano')
        
        # Dados do serviço
        nome_servico = request.POST.get('nome_servico')
        descricao = request.POST.get('descricao')
        data_hora_str = request.POST.get('data_hora')
        
        try:
            # Criar ou buscar a moto
            moto, created = Moto.objects.get_or_create(
                marca=marca,
                modelo=modelo,
                ano=int(ano)
            )
            
            # Criar ou buscar o serviço
            servico, created = Servicos.objects.get_or_create(
                nome=nome_servico,
                defaults={'descricao': descricao}
            )
            
            # Converter string de data/hora para datetime
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
            data_hora = timezone.make_aware(data_hora)
            
            # Buscar ou criar cliente
            cliente, created = Cliente.objects.get_or_create(
                usuario=request.user,
                defaults={
                    'telefone': '(00) 00000-0000',
                    'endereco': 'Endereço não informado'
                }
            )
            
            # Criar agendamento
            agendamento = Agendamento.objects.create(
                cliente=cliente,
                mecanico=None,  # Será atribuído depois
                servico=servico,
                data_hora=data_hora,
                moto=moto,
                status='agendado'
            )
            
            messages.success(request, f'Agendamento criado com sucesso! ID: {agendamento.id}')
            return redirect('lista-servicos')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar agendamento: {e}')
    
    return render(request, 'Cliente/agendar-cliente.html')

def listas_servicos(request):
    """Exibe a lista de motos, serviços e agendamentos"""
    try:
        motos = Moto.objects.all()
        servicos = Servicos.objects.all()
        agendamentos = Agendamento.objects.all().select_related('cliente__usuario', 'moto', 'servico')
        ordens_servico = OrdemServico.objects.all().select_related('agendamento')
        
        print(f"📊 Debug - Dados encontrados:")
        print(f"  Motos: {motos.count()}")
        print(f"  Serviços: {servicos.count()}")
        print(f"  Agendamentos: {agendamentos.count()}")
        print(f"  Ordens de Serviço: {ordens_servico.count()}")
        
        context = {
            'motos': motos,
            'servicos': servicos,
            'agendamentos': agendamentos,
            'ordens_servico': ordens_servico,
        }
        
        return render(request, 'Cliente/listas_servicos.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao carregar dados: {e}')
        return render(request, 'Cliente/listas_servicos.html', {
            'motos': [],
            'servicos': [],
            'agendamentos': [],
            'ordens_servico': [],
        })

def ordens_servico(request):
    """Lista todas as ordens de serviço"""
    try:
        ordens = OrdemServico.objects.all().select_related(
            'agendamento__cliente__usuario',
            'agendamento__moto',
            'agendamento__servico'
        )
        
        context = {
            'ordens_servico': ordens
        }
        
        return render(request, 'Cliente/ordens_servico.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao carregar ordens de serviço: {e}')
        return render(request, 'Cliente/ordens_servico.html', {'ordens_servico': []})

def criar_ordem_servico(request, agendamento_id):
    """Cria uma ordem de serviço a partir de um agendamento"""
    try:
        agendamento = Agendamento.objects.get(id=agendamento_id)
        
        # Verificar se já existe ordem para este agendamento
        if hasattr(agendamento, 'ordemservico'):
            messages.info(request, 'Já existe uma ordem de serviço para este agendamento.')
            return redirect('ordens-servico')
        
        # Criar ordem de serviço
        ordem = OrdemServico.objects.create(
            agendamento=agendamento,
            descricao_problema='Problema a ser diagnosticado',
            descricao_servico=agendamento.servico.descricao,
            custo=150.00,  # Valor padrão
            status='pendente'
        )
        
        messages.success(request, f'Ordem de serviço #{ordem.id} criada com sucesso!')
        return redirect('ordens-servico')
        
    except Agendamento.DoesNotExist:
        messages.error(request, 'Agendamento não encontrado.')
        return redirect('lista-servicos')
    except Exception as e:
        messages.error(request, f'Erro ao criar ordem de serviço: {e}')
        return redirect('lista-servicos')

# Funções implementadas
def agendar_cliente(request):
    """Redireciona para a função de agendamento principal"""
    # Corrige nome da rota: 'agendar-servico' conforme urls.py
    return redirect('agendar-servico')

def agendamentos_cliente(request):
    """Mostra agendamentos específicos do cliente logado"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        agendamentos = Agendamento.objects.filter(cliente=cliente).select_related(
            'moto', 'servico', 'mecanico__usuario'
        ).order_by('-data_hora')
        
        context = {
            'agendamentos': agendamentos,
            'cliente': cliente
        }
        return render(request, 'Cliente/agendamentos-cliente.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao carregar agendamentos: {e}')
        return redirect('dashboard-cliente')

def historico_cliente(request):
    """Mostra histórico de serviços do cliente"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        agendamentos_concluidos = Agendamento.objects.filter(
            cliente=cliente, 
            status='concluido'
        ).select_related('moto', 'servico').order_by('-data_hora')
        
        context = {
            'agendamentos_concluidos': agendamentos_concluidos,
            'cliente': cliente
        }
        return render(request, 'Cliente/historico-cliente.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao carregar histórico: {e}')
        return redirect('dashboard-cliente')
