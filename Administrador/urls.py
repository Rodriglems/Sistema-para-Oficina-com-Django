from django.urls import path
from .Views import cliente, administrador, mecanico  # Importar todos os módulos
from . import login as forms

urlpatterns = [
    # Página inicial
    path('', cliente.dashboard_cliente, name='dashboard-cliente'),  # Mudança: usar dashboard como página inicial
    
    # Cliente
    path('agendar/', cliente.agendar_cliente, name='agendar-cliente'),
    path('agendamentos/', cliente.agendamentos_cliente, name='agendamentos-cliente'),
    path('historico/', cliente.historico_cliente, name='historico-cliente'),
    
    # Agendamento e serviços
    path('agendamento/', cliente.agendar_servico, name='agendar-servico'),
    path('lista-servicos/', cliente.listas_servicos, name='lista-servicos'),
    path('ordens-servico/', cliente.ordens_servico, name='ordens-servico'),
    path('criar-ordem/<int:agendamento_id>/', cliente.criar_ordem_servico, name='criar-ordem-servico'),
    
    # Autenticação
    path('login/', cliente.login, name='login'),  # Corrigido: remover _view
    path('logout/', cliente.logout_view, name='logout'),
    path('register/', forms.registrar_cliente, name='register'),
    
    # Admin - usando as funções do arquivo administrador.py
    path('dashboard-admin/', administrador.dashboard_admin, name='dashboard-admin'), 
    path('criar-admin/', administrador.criar_admin_padrao, name='criar-admin'),
    
    # Mecânico
    path('dashboard-mecanico/', mecanico.dashboard_mecanico, name='dashboard-mecanico'),
    path('painel-mecanico/', mecanico.painel_mecanico, name='painel-mecanico'),
    path('logout-mecanico/', mecanico.logout_mecanico, name='logout-mecanico'),
    
    path('adm-agendamentos/', administrador.agendamentos_admin, name='adm-agendamentos'),
    path('agendamento-admin/', administrador.agendar_servico_admin, name='agendar-servico-admin'), 
    
    # CRUD de Clientes pelo Admin
    path('editar_cliente/<int:pk>/', administrador.editar_cliente, name='editar_cliente'),
    path('adm/clientes/novo/', administrador.admin_registrar_cliente, name='admin_cliente_cadastrar'),
    path('adm-cliente/', administrador.clientes_admin, name='adm-cliente'),
    path('excluir_cliente/<int:id>/', administrador.excluir_cliente, name='excluir_cliente'),
    
    #CRUD de Mecanicos pelo Admin
    path('adm-mecanico/', administrador.mecanicos_admin, name='adm-mecanico'),
    path('adm/mecanicos/novo/', administrador.admin_criar_mecanico, name='admin_criar_mecanico'),
    path('editar_mecanico/<int:pk>/', administrador.editar_mecanico, name='admin_mecanico_editar'),
    path('excluir_mecanico/<int:id>/', administrador.excluir_mecanico, name='excluir_mecanico'),
    
    # CRUD de Agendamentos pelo Admin
    path('editar_agendamento/<int:id>/', administrador.editar_agendamento, name='editar_agendamento'),
    path('cancelar_agendamento/<int:id>/', administrador.cancelar_agendamento, name='cancelar_agendamento'),
    
    # Configurações do Administrador
    path('configuracoes/', administrador.configuracoes_admin, name='configuracoes_admin'),
    path('limpar-dados/', administrador.limpar_dados_sistema, name='limpar_dados_sistema'),
    
]
