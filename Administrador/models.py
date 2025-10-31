from django.db import models
from django.contrib.auth.models import User


class Servicos(models.Model):
    nome = models.CharField(max_length=150)
    data = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    descricao = models.TextField()

    def __str__(self):
        return self.nome
    
    
    
    
class Moto(models.Model):
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    ano = models.IntegerField()    
    
    
    # Método especial que define como o objeto será representado como string
    # Retorna uma formatação legível: "marca modelo - placa" (ex: "Honda CB600F - ABC-1234")
    def __str__(self):
        return self.marca
    
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