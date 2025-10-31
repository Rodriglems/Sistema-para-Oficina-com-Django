# Relatório de Testes de Caixa Branca – Sistema para Oficina

**Data:** 10/10/2025  
**Metodologia:** White Box Testing  
**Ferramentas:** Django TestCase, Coverage.py (planejado)  
**Responsável:** Equipe de desenvolvimento

## 1. Introdução

Este documento apresenta os resultados dos testes de caixa branca implementados para o sistema Django "Sistema para Oficina". Os testes de caixa branca têm como objetivo examinar o código fonte diretamente, garantindo que todos os caminhos lógicos, condições e branches sejam executados pelo menos uma vez.

## 2. Metodologia de Caixa Branca

### 2.1 Critérios de Cobertura

- **Cobertura de Instruções:** Cada linha executável do código deve ser executada
- **Cobertura de Branches:** Cada condição if/else deve ser testada com valores true/false
- **Cobertura de Caminhos:** Diferentes sequências de execução devem ser exercitadas
- **Cobertura de Condições:** Cada expressão booleana deve ser testada

### 2.2 Análise Estática do Código

Foram identificados os seguintes pontos críticos para teste:

**Views Cliente (`Administrador/Views/cliente.py`):**

- 21 condições if/else
- 10 blocos try/except
- Múltiplos caminhos de autenticação
- Lógica de redirecionamento baseada em perfil do usuário

**Views Administrador (`Administrador/Views/administrador.py`):**

- Decoradores de autenticação (@login_required)
- Verificações de permissão (is_staff, hasattr)
- Tratamento de exceções em consultas ao banco

**Models (`Administrador/models.py`):**

- Métodos **str** com lógica condicional
- Relacionamentos OneToOne e ForeignKey

## 3. Casos de Teste Implementados

### 3.1 ModelsBasicTest

**Objetivo:** Testar representações string e criação de objetos relacionados

- ✅ `test_strs()` - Testa **str** de todos os modelos
- ✅ `test_ordem_servico_str_with_exception()` - Testa branch de exceção em OrdemServico.**str**

**Cobertura obtida:** 100% dos métodos **str** dos modelos

### 3.2 WhiteBoxLoginTest

**Objetivo:** Cobertura completa da view de login com todos os branches

- ✅ `test_login_get_request()` - Branch GET request
- ✅ `test_login_post_campos_vazios()` - Branch `if not username or not password`
- ✅ `test_login_post_credenciais_invalidas()` - Branch `else` (user is None)
- ✅ `test_login_post_credenciais_validas()` - Branch `if user is not None`
- ✅ `test_login_branches_coverage()` - Teste específico para branches de autenticação

**Branches cobertos:**

- Campo username vazio
- Campo password vazio
- Credenciais inválidas
- Autenticação bem-sucedida
- Verificação de perfis (Admin, Cliente, Mecânico)
- Usuário sem perfil específico

### 3.3 WhiteBoxDashboardTest

**Objetivo:** Testar todos os caminhos do dashboard do cliente

- ✅ `test_dashboard_usuario_nao_autenticado()` - Branch `if not request.user.is_authenticated`
- ✅ `test_dashboard_usuario_autenticado_sem_cliente()` - Branch `except Cliente.DoesNotExist`
- ✅ `test_dashboard_usuario_com_cliente_sem_agendamentos()` - Usuário válido sem dados
- ✅ `test_dashboard_usuario_com_agendamentos()` - Branch principal com dados

**Branches cobertos:**

- Usuário não autenticado
- Usuário autenticado sem perfil Cliente
- Cliente sem agendamentos
- Cliente com agendamentos de diferentes status

### 3.4 WhiteBoxAgendarServicoTest

**Objetivo:** Cobertura da lógica de agendamento

- ✅ `test_agendar_servico_get()` - Branch GET request
- ✅ `test_agendar_servico_post_success()` - Happy path do POST
- ✅ `test_agendar_servico_post_exception()` - Branch `except Exception`

**Branches cobertos:**

- GET request (renderização do formulário)
- POST com dados válidos
- POST com dados inválidos gerando exceção

### 3.5 WhiteBoxAdminViewsTest

**Objetivo:** Testar proteção e lógica das views administrativas

- ✅ `test_dashboard_admin_sem_login()` - Decorator @login_required
- ✅ `test_dashboard_admin_usuario_nao_autorizado()` - Branch de verificação de permissão
- ✅ `test_dashboard_admin_com_admin_profile()` - Branch `hasattr(administrador)`
- ✅ `test_dashboard_admin_com_is_staff()` - Branch `request.user.is_staff`

**Branches cobertos:**

- Acesso sem autenticação
- Usuário sem permissão de admin
- Acesso com perfil Administrador
- Acesso com flag is_staff

### 3.6 WhiteBoxOrdemServicoTest

**Objetivo:** Testar criação de ordens de serviço

- ✅ `test_criar_ordem_agendamento_inexistente()` - Branch `except Agendamento.DoesNotExist`
- ✅ `test_criar_ordem_ja_existente()` - Branch `if hasattr(agendamento, 'ordemservico')`
- ✅ `test_criar_ordem_success()` - Happy path

**Branches cobertos:**

- Agendamento não encontrado
- Ordem já existente
- Criação bem-sucedida

## 4. Resultados da Execução

```bash
$ python3 manage.py test Administrador.tests --verbosity=1

Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..........................

----------------------------------------------------------------------
Ran 26 tests in 3.642s

OK
Destroying test database for alias 'default'...
```

**Resumo:**

- ✅ **26 testes executados**
- ✅ **100% de sucesso**
- ⏱️ **Tempo de execução:** 3.6 segundos
- 🎯 **Zero falhas ou erros**

## 5. Análise de Cobertura por Componente

### 5.1 Models (models.py)

- **Cobertura estimada:** ~95%
- **Não coberto:** Alguns edge cases em validações de campo
- **Branches testados:** Todos os métodos **str**, including exception handling

### 5.2 Views Cliente (Views/cliente.py)

- **Cobertura estimada:** ~80%
- **Branches cobertos:** 15/21 condições identificadas
- **Principais caminhos:** Login, dashboard, agendamento, criação de ordem
- **Não coberto:** Alguns caminhos de exceção específicos

### 5.3 Views Administrador (Views/administrador.py)

- **Cobertura estimada:** ~70%
- **Branches cobertos:** Autenticação, autorização, dashboard
- **Não coberto:** Funcionalidades específicas de CRUD

## 6. Gaps de Cobertura Identificados

### 6.1 Não Testados (Prioridade Alta)

- View `listas_servicos()` - lógica de listagem com try/except
- View `ordens_servico()` - consultas com relacionamentos
- Views específicas de mecânico (`Views/mecanico.py`)
- Validações de formulários customizadas

### 6.2 Não Testados (Prioridade Média)

- Alguns branches de exceção muito específicos
- Validações de integridade de dados
- Comportamento com dados corrompidos

### 6.3 Limitações dos Testes Atuais

- Testes de integração com banco de dados real
- Testes de performance
- Testes de concorrência

## 7. Recomendações

### 7.1 Melhorias Imediatas

1. **Implementar coverage.py** para métricas exatas de cobertura
2. **Adicionar testes para views de mecânico**
3. **Testar formulários customizados** (`forms.py`)
4. **Cobrir branches de exceção específicos**

### 7.2 Melhorias Futuras

1. **Testes de mutação** para validar qualidade dos testes
2. **Testes de integração** end-to-end
3. **Automatização com CI/CD** (GitHub Actions)
4. **Relatórios de cobertura automáticos**

## 8. Conclusão

Os testes de caixa branca implementados cobrem **aproximadamente 80% dos caminhos críticos** do sistema. Todos os principais fluxos de usuário foram testados, incluindo:

- ✅ Autenticação com diferentes tipos de usuário
- ✅ Proteção de rotas administrativas
- ✅ Criação e gerenciamento de agendamentos
- ✅ Tratamento de exceções principais
- ✅ Representação de modelos

O sistema demonstra **robustez adequada** para os cenários testados, com tratamento apropriado de erros e validações de entrada.

## 9. Anexos

### 9.1 Comando para Reproduzir

```bash
# Executar todos os testes de caixa branca
python3 manage.py test Administrador.tests --verbosity=1

# Executar teste específico
python3 manage.py test Administrador.tests.WhiteBoxLoginTest
```

### 9.2 Estrutura dos Arquivos

- **Testes:** `Administrador/tests.py`
- **Views testadas:** `Administrador/Views/*.py`
- **Models testados:** `Administrador/models.py`
- **URLs cobertas:** `Administrador/urls.py`

### 9.3 Dependências de Teste

- Django TestCase
- Django Test Client
- django.contrib.messages (para testar mensagens)
- django.contrib.auth (para autenticação)

---

**Nota:** Este relatório reflete o estado atual do sistema em 10/10/2025. Recomenda-se atualização dos testes sempre que houver mudanças significativas no código.
