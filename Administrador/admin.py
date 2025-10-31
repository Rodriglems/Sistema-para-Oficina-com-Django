from django.contrib import admin
from .models import (
    Servicos, Moto, Administrador, 
    Mecanico, Cliente, Agendamento, OrdemServico
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
