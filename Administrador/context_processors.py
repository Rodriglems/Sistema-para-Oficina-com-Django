"""
Context Processors para disponibilizar variáveis globalmente nos templates
"""
from .models import ConfiguracaoOficina


def configuracao_oficina(request):
    """
    Disponibiliza as configurações da oficina em todos os templates
    """
    try:
        config = ConfiguracaoOficina.objects.first()
        if not config:
            # Criar configuração padrão se não existir
            config = ConfiguracaoOficina.objects.create(
                nome_oficina="MotoService",
                endereco="Endereço não configurado",
                telefone="(00) 0000-0000",
                email="contato@oficina.com",
                cnpj="00.000.000/0000-00",
                dias_funcionamento="Segunda a Sexta",
            )
    except Exception as e:
        # Em caso de erro, retornar configuração padrão vazia
        config = None
    
    return {
        'config_oficina': config
    }
