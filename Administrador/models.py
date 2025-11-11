from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time


class Servicos(models.Model):
    nome = models.CharField(max_length=150)
    data = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    descricao = models.TextField()

    def __str__(self):
        return self.nome
    
    
    
    
class Moto(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, null=True, blank=True, related_name='motos')
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    ano = models.IntegerField()
    placa = models.CharField(max_length=10, null=True, blank=True)
    cor = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.ano})"
    
    class Meta:
        ordering = ['-id']
    
#Sem __str__ mostraria: <Moto object (1)>
# Com __str__ mostra: "Yamaha MT-07 - XYZ-9876"
# Resultado: Yamaha MT-07 - XYZ-9876




class Administrador(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    telefone = models.CharField(max_length=15)
    
    def __str__(self):
        return self.usuario.username
    
    
    
class Mecanico(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mecanico')
    especialidade = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15)
    nome_completo = models.CharField(max_length=200, default='Nome Completo')
    disponibilidade = models.CharField(max_length=100, default='Segunda a Sexta 8h-17h')
    
    
    def __str__(self):
        return self.usuario.username
    
    
    
class Cliente(models.Model):
    nome_completo = models.CharField(max_length=255, default='Nome Completo')
    cpf = models.CharField(max_length=14, default='000.000.000-00')
    email = models.EmailField(unique=True, default='email@exemplo.com')
    telefone = models.CharField(max_length=15)
    endereco = models.CharField(max_length=255)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE,  related_name='cliente')

    def __str__(self):
        return self.nome_completo

    
    
    
class Agendamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    mecanico = models.ForeignKey(Mecanico, on_delete=models.CASCADE, null=True, blank=True)  # Agora é opcional
    servico = models.ForeignKey(Servicos, on_delete=models.CASCADE)
    descricao_problema = models.TextField(null=True, blank=True)
    descricao_mecanico = models.TextField(null=True, blank=True, verbose_name='Descrição do Mecânico')
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Valor do Serviço')
    data_hora = models.DateTimeField()
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ('agendado', 'Agendado'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado')
    ], default='agendado')
    
    def __str__(self):
        return f"{self.servico.nome} - {self.cliente.usuario.username}"
    
    
    
class OrdemServico(models.Model):
    agendamento = models.OneToOneField(Agendamento, on_delete=models.CASCADE)
    descricao_cliente = models.TextField(null=True, blank=True)
    descricao_servico = models.TextField()
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado')
    ], default='pendente')

    def __str__(self):
        # Retorna uma representação legível que inclui id e referência do agendamento
        try:
            return f"OS #{self.id} - {self.agendamento}"
        except Exception:
            return f"OS #{self.id}"
        
        
        
        
# Configurações adicionais para o sistema de agendamentos e ordens de serviço
class ConfiguracaoOficina(models.Model):
    nome_oficina = models.CharField(max_length=200, default="Minha Oficina")
    endereco = models.TextField()
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    cnpj = models.CharField(max_length=18)
    horario_funcionamento_inicio = models.TimeField(default=time(8, 0))
    horario_funcionamento_fim = models.TimeField(default=time(18, 0))
    dias_funcionamento = models.CharField(max_length=100, default="Segunda a Sexta")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    tema = models.CharField(max_length=20, default="azul", choices=[
        ('azul', 'Azul Oficial'),
        ('verde', 'Verde Mecânico'),
        ('roxo', 'Roxo Premium'),
        ('vermelho', 'Vermelho Dinâmico'),
        ('escuro', 'Modo Escuro'),
    ])
    
    def __str__(self):
        return self.nome_oficina
    
class ConfiguracaoAgendamento(models.Model):
    intervalo_agendamento = models.IntegerField(default=60, help_text="Intervalo em minutos")
    antecedencia_minima = models.IntegerField(default=24, help_text="Horas de antecedência")
    limite_agendamentos_dia = models.IntegerField(default=10)
    permite_agendamento_feriados = models.BooleanField(default=False)
    permite_reagendamento = models.BooleanField(default=True)
    tempo_limite_cancelamento = models.IntegerField(default=2, help_text="Horas antes do agendamento")
    
    
class ConfiguracaoNotificacao(models.Model):
    email_confirmacao = models.BooleanField(default=True)
    sms_lembrete = models.BooleanField(default=False)
    notificar_24h_antes = models.BooleanField(default=True)
    notificar_1h_antes = models.BooleanField(default=True)
    email_cancelamento = models.BooleanField(default=True)
    email_conclusao = models.BooleanField(default=True)
    

class LogAuditoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    acao = models.CharField(max_length=100)
    modelo = models.CharField(max_length=50)
    objeto_id = models.IntegerField()
    descricao = models.TextField()
    data_hora = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.acao} - {self.data_hora}"
    
    class Meta:
        ordering = ['-data_hora']


 