from django.contrib import admin
from .models import (
    Servicos, Moto, Administrador, 
    Mecanico, Cliente, Agendamento, OrdemServico,
    ConfiguracaoOficina, ConfiguracaoAgendamento, 
    ConfiguracaoNotificacao, LogAuditoria
)


@admin.register(Servicos)
class ServicosAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)


@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'modelo', 'ano')
    search_fields = ('marca', 'modelo')
    list_filter = ('marca', 'ano')


@admin.register(Administrador)
class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'email', 'telefone')
    search_fields = ('usuario__username', 'email')


@admin.register(Mecanico)
class MecanicoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'especialidade', 'telefone')
    search_fields = ('usuario__username', 'especialidade')
    list_filter = ('especialidade',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'telefone', 'endereco')
    search_fields = ('usuario__username', 'endereco')


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'mecanico', 'servico', 'data_hora', 'status')
    search_fields = ('cliente__usuario__username', 'mecanico__usuario__username')
    list_filter = ('status', 'data_hora', 'servico')
    date_hierarchy = 'data_hora'


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = ('agendamento', 'custo', 'status', 'data_conclusao')
    search_fields = ('agendamento__cliente__usuario__username',)
    list_filter = ('status', 'data_conclusao')
    date_hierarchy = 'data_conclusao'


@admin.register(ConfiguracaoOficina)
class ConfiguracaoOficinaAdmin(admin.ModelAdmin):
    list_display = ('nome_oficina', 'telefone', 'email', 'tema')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_oficina', 'cnpj', 'endereco', 'telefone', 'email')
        }),
        ('Horário de Funcionamento', {
            'fields': ('horario_funcionamento_inicio', 'horario_funcionamento_fim', 'dias_funcionamento')
        }),
        ('Personalização', {
            'fields': ('logo', 'tema')
        }),
    )


@admin.register(ConfiguracaoAgendamento)
class ConfiguracaoAgendamentoAdmin(admin.ModelAdmin):
    list_display = ('intervalo_agendamento', 'antecedencia_minima', 'limite_agendamentos_dia', 'permite_reagendamento')
    fieldsets = (
        ('Intervalos e Limites', {
            'fields': ('intervalo_agendamento', 'antecedencia_minima', 'limite_agendamentos_dia')
        }),
        ('Permissões', {
            'fields': ('permite_agendamento_feriados', 'permite_reagendamento', 'tempo_limite_cancelamento')
        }),
    )


@admin.register(ConfiguracaoNotificacao)
class ConfiguracaoNotificacaoAdmin(admin.ModelAdmin):
    list_display = ('email_confirmacao', 'notificar_24h_antes', 'notificar_1h_antes', 'email_conclusao')
    fieldsets = (
        ('Notificações por Email', {
            'fields': ('email_confirmacao', 'email_cancelamento', 'email_conclusao')
        }),
        ('Lembretes', {
            'fields': ('notificar_24h_antes', 'notificar_1h_antes', 'sms_lembrete')
        }),
    )


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'acao', 'modelo', 'objeto_id', 'data_hora', 'ip_address')
    search_fields = ('usuario__username', 'acao', 'modelo', 'descricao')
    list_filter = ('acao', 'modelo', 'data_hora')
    date_hierarchy = 'data_hora'
    readonly_fields = ('usuario', 'acao', 'modelo', 'objeto_id', 'descricao', 'data_hora', 'ip_address')
    
    def has_add_permission(self, request):
        # Impede criação manual de logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Apenas superusuários podem deletar logs
        return request.user.is_superuser
