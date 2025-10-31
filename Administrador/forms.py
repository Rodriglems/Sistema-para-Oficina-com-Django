from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente, Mecanico

class ClienteRegistrationForm(forms.Form):
    nome_completo = forms.CharField(max_length=200, label="Nome completo")
    username = forms.CharField(max_length=150, label="Usuário")
    email = forms.EmailField(label="E-mail")
    telefone = forms.CharField(max_length=20, label="Telefone")
    cpf = forms.CharField(max_length=14, label="CPF")
    endereco = forms.CharField(max_length=355, label="Endereço")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Usuário já existe.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("E-mail já cadastrado.")
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if Cliente.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError("CPF já cadastrado.")
        return cpf

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As senhas não coincidem.")
        return cleaned

    def save(self):
        nome_completo = self.cleaned_data["nome_completo"]
        username = self.cleaned_data["username"]
        email = self.cleaned_data["email"]
        telefone = self.cleaned_data["telefone"]
        cpf = self.cleaned_data["cpf"]
        endereco = self.cleaned_data["endereco"]
        password = self.cleaned_data["password1"]

        user = User.objects.create_user(username=username, password=password)

        cliente = Cliente.objects.create(
            usuario=user,                # mantém assim se o campo for 'usuario'
            nome_completo=nome_completo,
            telefone=telefone,
            cpf=cpf,
            email=email,
            endereco=endereco,
        )
        return user



# Editar cliente 
class EditarClienteForm(forms.ModelForm):
    telefone = forms.CharField(max_length=15, required=False)
    endereco = forms.CharField(max_length=255, required=False)
    cpf = forms.CharField(max_length=14, required=False)
    nome_completo = forms.CharField(max_length=255, required=False)
    email = forms.CharField(max_length=255, required=False, label="E-mail")
    nova_senha = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Nova senha"
    )

    class Meta:
        model = User
        fields = ['username']
        help_texts = {'username': None}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche automaticamente se o User tiver um Cliente vinculado
        if hasattr(self.instance, 'cliente'):
            cliente = self.instance.cliente
            self.fields['telefone'].initial = cliente.telefone
            self.fields['endereco'].initial = cliente.endereco
            self.fields['cpf'].initial = cliente.cpf
            self.fields['nome_completo'].initial = cliente.nome_completo
            self.fields['email'].initial = cliente.email

    def save(self, commit=True):
        user = super().save(commit=False)
        nova_senha = self.cleaned_data.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)
        if commit:
            user.save()
            # Atualiza os dados do Cliente vinculado
            if hasattr(user, 'cliente'):
                cliente = user.cliente
                cliente.telefone = self.cleaned_data.get('telefone', cliente.telefone)
                cliente.endereco = self.cleaned_data.get('endereco', cliente.endereco)
                cliente.cpf = self.cleaned_data.get('cpf', cliente.cpf)
                cliente.nome_completo = self.cleaned_data.get('nome_completo', cliente.nome_completo)
                cliente.email = self.cleaned_data.get('email', cliente.email)
                cliente.save()
        return user


# Mecanicos

class MecanicoRegistrationForm(forms.Form):
    nome_completo = forms.CharField(max_length=200, label="Nome completo")
    telefone = forms.CharField(max_length=20, label="Telefone")
    especialidade = forms.CharField(max_length=100, label="Especialidade")
    disponibilidade = forms.CharField(max_length=100, label="Disponibilidade ex:(Segunda a Sexta 8h-17h)")
    username = forms.CharField(max_length=150, label="Usuário")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Senha")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Usuário já existe.")
        return username
    
    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "As senhas não coincidem.")
        return cleaned

    def save(self):
        nome_completo = self.cleaned_data["nome_completo"]
        telefone = self.cleaned_data["telefone"]
        especialidade = self.cleaned_data["especialidade"]
        disponibilidade = self.cleaned_data["disponibilidade"]
        username = self.cleaned_data["username"]
        password = self.cleaned_data["password1"]

        user = User.objects.create_user(username=username, password=password)

        mecanico = Mecanico.objects.create(
            usuario=user,
            telefone=telefone,
            especialidade=especialidade,
            nome_completo=nome_completo,
            disponibilidade=disponibilidade,
        )
        return user



# Editar mecanico
class EditarMecanicoForm(forms.ModelForm):
    telefone = forms.CharField(max_length=15, required=False)
    especialidade = forms.CharField(max_length=100, required=False)
    disponibilidade = forms.CharField(max_length=100, required=False)
    nome_completo = forms.CharField(max_length=200, required=False)
    nova_senha = forms.CharField(
        widget=forms.PasswordInput, 
        required=False, 
        label="Nova senha"
    )

    class Meta:
        model = User
        fields = ['username']
        help_texts = {
            'username': None,
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preencher campos do Mecanico se existir
        if hasattr(self.instance, 'mecanico'):
            self.fields['telefone'].initial = self.instance.mecanico.telefone
            self.fields['especialidade'].initial = self.instance.mecanico.especialidade
            self.fields['nome_completo'].initial = self.instance.mecanico.nome_completo
            self.fields['disponibilidade'].initial = self.instance.mecanico.disponibilidade
    
    def save(self, commit=True):
        user = super().save(commit=False)
        nova_senha = self.cleaned_data.get('nova_senha')
        if nova_senha:
            user.set_password(nova_senha)
        if commit:
            user.save()
            # Atualizar o perfil Mecanico
            if hasattr(user, 'mecanico'):
                user.mecanico.telefone = self.cleaned_data.get('telefone', user.mecanico.telefone)
                user.mecanico.especialidade = self.cleaned_data.get('especialidade', user.mecanico.especialidade)
                user.mecanico.nome_completo = self.cleaned_data.get('nome_completo', user.mecanico.nome_completo)
                user.mecanico.disponibilidade = self.cleaned_data.get('disponibilidade', user.mecanico.disponibilidade)
                user.mecanico.save()
        return user







