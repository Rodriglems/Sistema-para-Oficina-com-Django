from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as django_logout, authenticate, login as login_user
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from ..models import Moto, Servicos, Agendamento, OrdemServico, Mecanico, Cliente, Administrador, ConfiguracaoOficina

def Mostrar(request):
    # Dashboard profissional do cliente com estatísticas completas
    servicos = Servicos.objects.all()
    agendamentos = []
    ultimo_servico = None
    total_finalizados = 0
    total_cancelados = 0
    total_pendentes = 0
    total_em_andamento = 0
    total_motos = 0
    total_gasto = 0
    proximo_agendamento = None
    
    if request.user.is_authenticated:
        try:
            cliente = Cliente.objects.get(usuario=request.user)
            
            # Próximos agendamentos (futuros e não cancelados)
            agendamentos = Agendamento.objects.filter(
                cliente=cliente, 
                data_hora__gte=timezone.now()
            ).exclude(status='cancelado').order_by('data_hora')[:5]
            
            # Próximo agendamento
            proximo_agendamento = agendamentos.first() if agendamentos else None
            
            # Último serviço concluído
            ultimo_servico = Agendamento.objects.filter(
                cliente=cliente,
                status='concluido'
            ).order_by('-data_hora').first()
            
            # Estatísticas de serviços
            total_finalizados = Agendamento.objects.filter(cliente=cliente, status='concluido').count()
            total_cancelados = Agendamento.objects.filter(cliente=cliente, status='cancelado').count()
            total_pendentes = Agendamento.objects.filter(cliente=cliente, status='agendado').count()
            total_em_andamento = Agendamento.objects.filter(cliente=cliente, status='em_andamento').count()
            
            # Total de motos cadastradas
            total_motos = Moto.objects.filter(cliente=cliente).count()
            
            # Total gasto em serviços concluídos
            from django.db.models import Sum
            total_gasto = Agendamento.objects.filter(
                cliente=cliente, 
                status='concluido'
            ).aggregate(Sum('valor_servico'))['valor_servico__sum'] or 0
            
        except Cliente.DoesNotExist:
            pass

    context = {
        'servicos': servicos,
        'agendamentos': agendamentos,
        'proximo_agendamento': proximo_agendamento,
        'ultimo_servico': ultimo_servico,
        'total_finalizados': total_finalizados,
        'total_cancelados': total_cancelados,
        'total_pendentes': total_pendentes,
        'total_em_andamento': total_em_andamento,
        'total_motos': total_motos,
        'total_gasto': total_gasto,
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
                    return redirect('dashboard-mecanico')
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
    # Verificar se o usuário está autenticado
    if not request.user.is_authenticated:
        messages.error(request, ' Você precisa estar logado para fazer um agendamento!')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        minhas_motos = Moto.objects.filter(cliente=cliente).order_by('-id')
    except Cliente.DoesNotExist:
        cliente = None
        minhas_motos = []
    
    if request.method == 'POST':
        # Verificar se está usando moto cadastrada ou criando nova
        moto_id = request.POST.get('moto_id')
        
        # Dados do serviço
        nome_servico = request.POST.get('servico')
        descricao = request.POST.get('descricao')
        data = request.POST.get('data')
        hora = request.POST.get('hora')
        
        try:
            # Validar campos obrigatórios
            if not all([nome_servico, descricao, data, hora]):
                messages.error(request, ' Todos os campos são obrigatórios!')
                return redirect('agendar-servico')
            
            # Obter ou criar moto
            if moto_id and moto_id != 'nova':
                # Usar moto cadastrada
                moto = get_object_or_404(Moto, id=moto_id, cliente=cliente)
                print(f" Usando moto cadastrada: {moto.marca} {moto.modelo} (ID: {moto.id})")
            else:
                # Criar nova moto
                marca = request.POST.get('marca')
                modelo = request.POST.get('modelo')
                ano = request.POST.get('ano')
                
                if not all([marca, modelo, ano]):
                    messages.error(request, ' Para cadastrar nova moto, preencha marca, modelo e ano!')
                    return redirect('agendar-servico')
                
                moto = Moto.objects.create(
                    cliente=cliente,
                    marca=marca,
                    modelo=modelo,
                    ano=int(ano)
                )
                print(f" Nova moto criada: {moto.marca} {moto.modelo} (ID: {moto.id})")
            
            # Criar ou buscar o serviço
            servico, servico_created = Servicos.objects.get_or_create(
                nome=nome_servico,
                defaults={'descricao': descricao}
            )
            print(f"Serviço {'CRIADO' if servico_created else 'ENCONTRADO'}: {servico.nome} (ID: {servico.id})")
            
            # Converter data e hora para datetime
            data_hora_str = f"{data} {hora}"
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M')
            data_hora = timezone.make_aware(data_hora)
            print(f" Data/Hora formatada: {data_hora}")
            
            # Buscar ou criar cliente - IMPORTANTE: garantir que o perfil existe
            cliente, cliente_created = Cliente.objects.get_or_create(
                usuario=request.user,
                defaults={
                    'nome_completo': request.user.get_full_name() or request.user.username,
                    'email': request.user.email or f'{request.user.username}@oficina.com',
                    'telefone': '(00) 00000-0000',
                    'endereco': 'Endereço não informado',
                    'cpf': '000.000.000-00'
                }
            )
            print(f"Cliente {'CRIADO' if cliente_created else 'ENCONTRADO'}: {cliente.nome_completo} (ID: {cliente.id})")
            
            # Criar agendamento com STATUS AGENDADO
            agendamento = Agendamento.objects.create(
                cliente=cliente,
                mecanico=None,  # Será atribuído depois pelo mecânico
                servico=servico,
                data_hora=data_hora,
                moto=moto,
                descricao_problema=descricao,
                status='agendado'  # IMPORTANTE: status correto
            )
            print(f" AGENDAMENTO CRIADO COM SUCESSO!")
            print(f"   ID: {agendamento.id}")
            print(f"   Status: {agendamento.status}")
            print(f"   Cliente: {agendamento.cliente.nome_completo}")
            print(f"   Data/Hora: {agendamento.data_hora}")
            print(f"{'='*60}\n")
            
            messages.success(request, f' Agendamento #{agendamento.id} criado com sucesso! Aguarde a confirmação do mecânico.')
            return redirect('dashboard-cliente')
            
        except Exception as e:
            print(f" ERRO CRÍTICO ao criar agendamento:")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensagem: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            messages.error(request, f' Erro ao criar agendamento: {e}')
            return redirect('agendar-servico')
    
    context = {
        'minhas_motos': minhas_motos,
        'cliente': cliente
    }
    return render(request, 'Cliente/agendar-cliente.html', context)



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
        # Buscar apenas agendamentos ativos (não concluídos nem cancelados)
        agendamentos = Agendamento.objects.filter(
            cliente=cliente
        ).exclude(
            status__in=['concluido', 'cancelado']
        ).select_related(
            'moto', 'servico', 'mecanico__usuario'
        ).order_by('data_hora')
        
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


def cancelar_agendamento_cliente(request, agendamento_id):
    """Permite que o cliente cancele seu próprio agendamento"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        agendamento = get_object_or_404(Agendamento, id=agendamento_id, cliente=cliente)
        
        # Verificar se o agendamento pode ser cancelado
        if agendamento.status == 'concluido':
            messages.error(request, 'Não é possível cancelar um agendamento já concluído.')
            return redirect('agendamentos-cliente')
        
        if agendamento.status == 'cancelado':
            messages.warning(request, 'Este agendamento já está cancelado.')
            return redirect('agendamentos-cliente')
        
        # Cancelar o agendamento
        agendamento.status = 'cancelado'
        agendamento.save()
        
        messages.success(request, f'Agendamento #{agendamento.id} cancelado com sucesso!')
        return redirect('agendamentos-cliente')
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao cancelar agendamento: {e}')
        return redirect('agendamentos-cliente')



def remarcar_agendamento_cliente(request, agendamento_id):
    """Permite que o cliente remarque (edite) seu agendamento"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        agendamento = get_object_or_404(Agendamento, id=agendamento_id, cliente=cliente)
        
        # Verificar se o agendamento pode ser remarcado
        if agendamento.status == 'concluido':
            messages.error(request, 'Não é possível remarcar um agendamento já concluído.')
            return redirect('agendamentos-cliente')
        
        if agendamento.status == 'cancelado':
            messages.error(request, 'Não é possível remarcar um agendamento cancelado.')
            return redirect('agendamentos-cliente')
        
        if request.method == 'POST':
            # Capturar dados do formulário
            marca = request.POST.get('marca')
            modelo = request.POST.get('modelo')
            ano = request.POST.get('ano')
            nome_servico = request.POST.get('servico')
            descricao = request.POST.get('descricao')
            data = request.POST.get('data')
            hora = request.POST.get('hora')
            
            # Validar campos
            if not all([marca, modelo, ano, nome_servico, descricao, data, hora]):
                messages.error(request, 'Todos os campos são obrigatórios!')
                return redirect('remarcar-agendamento-cliente', agendamento_id=agendamento_id)
            
            # Atualizar ou criar moto
            moto, _ = Moto.objects.get_or_create(
                marca=marca,
                modelo=modelo,
                ano=int(ano)
            )
            
            # Atualizar ou criar serviço
            servico, _ = Servicos.objects.get_or_create(
                nome=nome_servico,
                defaults={'descricao': descricao}
            )
            
            # Converter data e hora
            data_hora_str = f"{data} {hora}"
            data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M')
            data_hora = timezone.make_aware(data_hora)
            
            # Atualizar agendamento
            agendamento.moto = moto
            agendamento.servico = servico
            agendamento.data_hora = data_hora
            agendamento.descricao_problema = descricao
            
            # Se estava em andamento, voltar para agendado
            if agendamento.status == 'em_andamento':
                agendamento.status = 'agendado'
                agendamento.mecanico = None
            
            agendamento.save()
            
            messages.success(request, f'Agendamento #{agendamento.id} remarcado com sucesso!')
            return redirect('agendamentos-cliente')
        
        # GET - Mostrar formulário
        context = {
            'agendamento': agendamento,
            'cliente': cliente
        }
        return render(request, 'Cliente/remarcar-agendamento.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao remarcar agendamento: {e}')
        return redirect('agendamentos-cliente')



def historico_cliente(request):
    """Mostra histórico completo de serviços do cliente"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        
        # Buscar agendamentos concluídos e cancelados
        agendamentos_concluidos = Agendamento.objects.filter(
            cliente=cliente, 
            status='concluido'
        ).select_related('moto', 'servico', 'mecanico__usuario').order_by('-data_hora')
        
        agendamentos_cancelados = Agendamento.objects.filter(
            cliente=cliente, 
            status='cancelado'
        ).select_related('moto', 'servico', 'mecanico__usuario').order_by('-data_hora')
        
        # Combinar todos os agendamentos (concluídos e cancelados)
        todos_agendamentos = list(agendamentos_concluidos) + list(agendamentos_cancelados)
        todos_agendamentos.sort(key=lambda x: x.data_hora, reverse=True)
        
        # Estatísticas
        total_servicos = agendamentos_concluidos.count()
        total_cancelados = agendamentos_cancelados.count()
        total_gasto = sum([a.valor_servico for a in agendamentos_concluidos if a.valor_servico]) or 0
        
        context = {
            'agendamentos_concluidos': agendamentos_concluidos,
            'agendamentos_cancelados': agendamentos_cancelados,
            'todos_agendamentos': todos_agendamentos,
            'total_servicos': total_servicos,
            'total_cancelados': total_cancelados,
            'total_gasto': total_gasto,
            'cliente': cliente
        }
        return render(request, 'Cliente/historico-cliente.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao carregar histórico: {e}')
        return redirect('dashboard-cliente')


def minhas_motos(request):
    """Lista e permite cadastrar motos do cliente"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        motos = Moto.objects.filter(cliente=cliente).order_by('-id')
        
        context = {
            'motos': motos,
            'cliente': cliente
        }
        return render(request, 'Cliente/minhas-motos.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao carregar motos: {e}')
        return redirect('dashboard-cliente')


def cadastrar_moto(request):
    """Cadastra uma nova moto para o cliente"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        
        if request.method == 'POST':
            marca = request.POST.get('marca')
            modelo = request.POST.get('modelo')
            ano = request.POST.get('ano')
            placa = request.POST.get('placa', '').upper()
            cor = request.POST.get('cor', '')
            
            # Validar campos obrigatórios
            if not all([marca, modelo, ano]):
                messages.error(request, 'Marca, modelo e ano são obrigatórios!')
                return redirect('cadastrar-moto')
            
            # Criar moto
            moto = Moto.objects.create(
                cliente=cliente,
                marca=marca,
                modelo=modelo,
                ano=int(ano),
                placa=placa if placa else None,
                cor=cor if cor else None
            )
            
            messages.success(request, f'Moto {moto.marca} {moto.modelo} cadastrada com sucesso!')
            return redirect('minhas-motos')
        
        return render(request, 'Cliente/cadastrar-moto.html', {'cliente': cliente})
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao cadastrar moto: {e}')
        return redirect('minhas-motos')


def editar_moto(request, moto_id):
    """Edita uma moto do cliente"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        moto = get_object_or_404(Moto, id=moto_id, cliente=cliente)
        
        if request.method == 'POST':
            moto.marca = request.POST.get('marca')
            moto.modelo = request.POST.get('modelo')
            moto.ano = int(request.POST.get('ano'))
            moto.placa = request.POST.get('placa', '').upper() or None
            moto.cor = request.POST.get('cor', '') or None
            moto.save()
            
            messages.success(request, f'Moto {moto.marca} {moto.modelo} atualizada com sucesso!')
            return redirect('minhas-motos')
        
        context = {
            'moto': moto,
            'cliente': cliente
        }
        return render(request, 'Cliente/editar-moto.html', context)
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao editar moto: {e}')
        return redirect('minhas-motos')


def excluir_moto(request, moto_id):
    """Exclui uma moto do cliente"""
    if not request.user.is_authenticated:
        messages.error(request, 'Você precisa estar logado.')
        return redirect('login')
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)
        moto = get_object_or_404(Moto, id=moto_id, cliente=cliente)
        
        # Verificar se a moto tem agendamentos
        agendamentos_count = Agendamento.objects.filter(moto=moto).count()
        
        if agendamentos_count > 0:
            messages.warning(request, f'Não é possível excluir esta moto pois ela possui {agendamentos_count} agendamento(s) associado(s).')
            return redirect('minhas-motos')
        
        marca_modelo = f"{moto.marca} {moto.modelo}"
        moto.delete()
        
        messages.success(request, f'Moto {marca_modelo} excluída com sucesso!')
        return redirect('minhas-motos')
        
    except Cliente.DoesNotExist:
        messages.error(request, 'Perfil de cliente não encontrado.')
        return redirect('dashboard-cliente')
    except Exception as e:
        messages.error(request, f'Erro ao excluir moto: {e}')
        return redirect('minhas-motos')
