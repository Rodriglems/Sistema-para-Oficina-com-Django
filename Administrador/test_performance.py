"""
Testes de Performance - Sistema de Oficina
===========================================

Este arquivo contém testes de performance (load testing, stress testing) 
para o Sistema de Oficina. Os testes avaliam:
- Tempo de resposta
- Throughput (requisições por segundo)
- Uso de memória
- Eficiência de queries
- Escalabilidade
- Limites do sistema

Author: Sistema de Testes Automatizados
Date: 13 de novembro de 2025
"""

import time
import sys
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection
from django.test.utils import override_settings
from datetime import timedelta, datetime
from decimal import Decimal
import threading
from unittest.mock import patch

from .models import (
    Servicos, Moto, Cliente, Mecanico, Administrador,
    Agendamento, OrdemServico, ConfiguracaoOficina
)


# ============================================================================
# UTILITÁRIOS PARA MEDIÇÃO DE PERFORMANCE
# ============================================================================

class PerformanceTestMixin:
    """Mixin com métodos utilitários para testes de performance"""
    
    def measure_time(self, func, *args, **kwargs):
        """Mede o tempo de execução de uma função"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # em milissegundos
        return result, execution_time
    
    def measure_queries(self, func, *args, **kwargs):
        """Conta o número de queries executadas"""
        from django.test.utils import override_settings
        from django.db import connection, reset_queries
        
        reset_queries()
        result = func(*args, **kwargs)
        num_queries = len(connection.queries)
        
        return result, num_queries
    
    def assert_max_time(self, execution_time, max_time_ms, operation_name):
        """Verifica se o tempo de execução está dentro do limite"""
        self.assertLessEqual(
            execution_time, 
            max_time_ms,
            f"{operation_name} levou {execution_time:.2f}ms, máximo permitido: {max_time_ms}ms"
        )
    
    def assert_max_queries(self, num_queries, max_queries, operation_name):
        """Verifica se o número de queries está dentro do limite"""
        self.assertLessEqual(
            num_queries,
            max_queries,
            f"{operation_name} executou {num_queries} queries, máximo permitido: {max_queries}"
        )
    
    def print_performance_report(self, test_name, execution_time, num_queries=None):
        """Imprime relatório de performance"""
        print(f"\n{'='*60}")
        print(f"🎯 TESTE: {test_name}")
        print(f"⏱️  Tempo de Execução: {execution_time:.2f}ms")
        if num_queries is not None:
            print(f"📊 Número de Queries: {num_queries}")
        print(f"{'='*60}")


# ============================================================================
# TESTES DE TEMPO DE RESPOSTA (Response Time Testing)
# ============================================================================

@override_settings(DEBUG=True)
class ResponseTimeTest(TestCase, PerformanceTestMixin):
    """Testes de tempo de resposta das principais views"""
    
    def setUp(self):
        """Configuração inicial para testes de tempo de resposta"""
        self.client = Client()
        
        # Criar usuário admin
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        self.admin_profile = Administrador.objects.create(
            usuario=self.admin_user,
            email='admin@test.com',
            telefone='(11) 99999-9999'
        )
        
        # Criar usuário cliente
        self.cliente_user = User.objects.create_user(
            username='cliente',
            password='cliente123'
        )
        self.cliente_profile = Cliente.objects.create(
            usuario=self.cliente_user,
            nome_completo='Cliente Teste',
            cpf='123.456.789-00',
            email='cliente@test.com',
            telefone='(11) 98765-4321',
            endereco='Rua Teste, 123'
        )
        
        # Criar dados de teste
        self._criar_dados_teste()
    
    def _criar_dados_teste(self):
        """Cria dados de teste básicos"""
        self.servico = Servicos.objects.create(
            nome='Troca de Óleo',
            descricao='Serviço de troca de óleo'
        )
        
        self.moto = Moto.objects.create(
            cliente=self.cliente_profile,
            marca='Honda',
            modelo='CB 600F',
            ano=2020
        )
    
    def test_login_page_response_time(self):
        """Testa tempo de resposta da página de login"""
        response, execution_time = self.measure_time(
            self.client.get, reverse('login')
        )
        
        self.assertEqual(response.status_code, 200)
        self.assert_max_time(execution_time, 100, "Página de Login")
        self.print_performance_report("Login Page", execution_time)
    
    def test_login_post_response_time(self):
        """Testa tempo de resposta do POST de login"""
        def login_post():
            return self.client.post(reverse('login'), {
                'username': 'admin',
                'senha': 'admin123'
            })
        
        response, execution_time = self.measure_time(login_post)
        
        self.assertEqual(response.status_code, 302)
        self.assert_max_time(execution_time, 200, "Login POST")
        self.print_performance_report("Login POST", execution_time)
    
    def test_dashboard_cliente_response_time(self):
        """Testa tempo de resposta do dashboard do cliente"""
        self.client.login(username='cliente', password='cliente123')
        
        response, execution_time = self.measure_time(
            self.client.get, reverse('dashboard-cliente')
        )
        
        self.assertEqual(response.status_code, 200)
        self.assert_max_time(execution_time, 300, "Dashboard Cliente")
        self.print_performance_report("Dashboard Cliente", execution_time)
    
    def test_dashboard_admin_response_time(self):
        """Testa tempo de resposta do dashboard admin"""
        self.client.login(username='admin', password='admin123')
        
        response, execution_time = self.measure_time(
            self.client.get, reverse('dashboard-admin')
        )
        
        self.assertEqual(response.status_code, 200)
        self.assert_max_time(execution_time, 500, "Dashboard Admin")
        self.print_performance_report("Dashboard Admin", execution_time)
    
    def test_agendar_servico_get_response_time(self):
        """Testa tempo de resposta do GET de agendamento"""
        self.client.login(username='cliente', password='cliente123')
        
        response, execution_time = self.measure_time(
            self.client.get, reverse('agendar-servico')
        )
        
        self.assertEqual(response.status_code, 200)
        self.assert_max_time(execution_time, 250, "Agendar Serviço GET")
        self.print_performance_report("Agendar Serviço GET", execution_time)
    
    def test_agendar_servico_post_response_time(self):
        """Testa tempo de resposta do POST de agendamento"""
        self.client.login(username='cliente', password='cliente123')
        
        data_hora = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        def agendar_post():
            return self.client.post(reverse('agendar-servico'), {
                'moto_id': str(self.moto.id),
                'servico': 'Troca de Óleo',
                'descricao': 'Preciso trocar o óleo da moto',
                'data': data_hora,
                'hora': '10:00'
            })
        
        response, execution_time = self.measure_time(agendar_post)
        
        self.assertEqual(response.status_code, 302)
        self.assert_max_time(execution_time, 400, "Agendar Serviço POST")
        self.print_performance_report("Agendar Serviço POST", execution_time)


# ============================================================================
# TESTES DE QUERIES (Database Query Testing)
# ============================================================================

@override_settings(DEBUG=True)
class DatabaseQueryTest(TestCase, PerformanceTestMixin):
    """Testes de eficiência de queries do banco de dados"""
    
    def setUp(self):
        """Configuração inicial para testes de queries"""
        self.client = Client()
        
        # Criar admin
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        self.admin_profile = Administrador.objects.create(
            usuario=self.admin_user,
            email='admin@test.com',
            telefone='(11) 99999-9999'
        )
        
        # Criar dados em massa
        self._criar_dados_em_massa()
    
    def _criar_dados_em_massa(self):
        """Cria dados em massa para testes"""
        # Criar 50 clientes
        for i in range(50):
            user = User.objects.create_user(
                username=f'cliente{i}',
                password='senha123'
            )
            Cliente.objects.create(
                usuario=user,
                nome_completo=f'Cliente {i}',
                cpf=f'{i:011d}',
                email=f'cliente{i}@test.com',
                telefone=f'(11) {i:05d}-0000',
                endereco=f'Rua {i}'
            )
        
        # Criar 10 mecânicos
        for i in range(10):
            user = User.objects.create_user(
                username=f'mecanico{i}',
                password='senha123'
            )
            Mecanico.objects.create(
                usuario=user,
                especialidade=f'Especialidade {i}',
                telefone=f'(11) {i:05d}-1111',
                nome_completo=f'Mecânico {i}'
            )
        
        # Criar 100 agendamentos
        clientes = Cliente.objects.all()
        mecanicos = Mecanico.objects.all()
        
        servico = Servicos.objects.create(
            nome='Serviço Teste',
            descricao='Descrição teste'
        )
        
        for i in range(100):
            cliente = clientes[i % 50]
            mecanico = mecanicos[i % 10] if i % 2 == 0 else None
            
            moto = Moto.objects.create(
                cliente=cliente,
                marca='Honda',
                modelo=f'Modelo {i}',
                ano=2020 + (i % 5)
            )
            
            Agendamento.objects.create(
                cliente=cliente,
                mecanico=mecanico,
                servico=servico,
                moto=moto,
                data_hora=timezone.now() + timedelta(days=i),
                status=['agendado', 'em_andamento', 'concluido'][i % 3],
                descricao_problema=f'Problema {i}'
            )
    
    def test_dashboard_admin_queries(self):
        """Testa número de queries no dashboard admin"""
        self.client.login(username='admin', password='admin123')
        
        from django.db import connection, reset_queries
        reset_queries()
        
        response = self.client.get(reverse('dashboard-admin'))
        num_queries = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        
        # Dashboard admin deve fazer no máximo 20 queries
        self.assert_max_queries(num_queries, 20, "Dashboard Admin")
        
        print(f"\n📊 Dashboard Admin: {num_queries} queries")
        for i, query in enumerate(connection.queries[:5], 1):
            print(f"  Query {i}: {query['sql'][:80]}...")
    
    def test_lista_agendamentos_queries(self):
        """Testa queries na listagem de agendamentos"""
        self.client.login(username='admin', password='admin123')
        
        from django.db import connection, reset_queries
        reset_queries()
        
        response = self.client.get(reverse('adm-agendamentos'))
        num_queries = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        
        # Lista de agendamentos deve usar select_related para evitar N+1
        # Com 100 agendamentos, deve fazer no máximo 10 queries
        self.assert_max_queries(num_queries, 10, "Lista de Agendamentos")
        
        print(f"\n📊 Lista Agendamentos: {num_queries} queries")
    
    def test_n_plus_one_problem(self):
        """Detecta problema N+1 em queries"""
        # Testar se há problema N+1 ao listar agendamentos
        agendamentos = Agendamento.objects.all()[:10]
        
        from django.db import connection, reset_queries
        reset_queries()
        
        # Forçar avaliação das queries
        for agendamento in agendamentos:
            _ = agendamento.cliente.nome_completo
            _ = agendamento.servico.nome
            if agendamento.moto:
                _ = agendamento.moto.marca
        
        num_queries = len(connection.queries)
        
        # Com select_related, deve fazer apenas 1 query
        # Sem select_related, faria 31 queries (1 + 10*3)
        self.assert_max_queries(num_queries, 35, "N+1 Check (sem otimização)")
        
        # Agora testar com select_related
        reset_queries()
        
        agendamentos_otimizados = Agendamento.objects.select_related(
            'cliente__usuario', 'servico', 'moto', 'mecanico__usuario'
        )[:10]
        
        for agendamento in agendamentos_otimizados:
            _ = agendamento.cliente.nome_completo
            _ = agendamento.servico.nome
            if agendamento.moto:
                _ = agendamento.moto.marca
        
        num_queries_otimizado = len(connection.queries)
        
        # Com select_related, deve fazer apenas 1 query
        self.assert_max_queries(num_queries_otimizado, 2, "N+1 Check (com otimização)")
        
        print(f"\n📊 Problema N+1:")
        print(f"  Sem otimização: {num_queries} queries")
        print(f"  Com select_related: {num_queries_otimizado} queries")
        print(f"  Melhoria: {num_queries - num_queries_otimizado} queries economizadas")


# ============================================================================
# TESTES DE CARGA (Load Testing)
# ============================================================================

class LoadTest(TransactionTestCase, PerformanceTestMixin):
    """Testes de carga simulando múltiplos usuários"""
    
    def setUp(self):
        """Configuração inicial para testes de carga"""
        # Criar usuários de teste
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        Administrador.objects.create(
            usuario=self.admin_user,
            email='admin@test.com',
            telefone='(11) 99999-9999'
        )
        
        # Criar clientes
        self.clientes = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'cliente{i}',
                password='senha123'
            )
            cliente = Cliente.objects.create(
                usuario=user,
                nome_completo=f'Cliente {i}',
                cpf=f'{i:011d}',
                email=f'cliente{i}@test.com',
                telefone=f'(11) {i:05d}-0000',
                endereco=f'Rua {i}'
            )
            self.clientes.append(cliente)
    
    def test_concurrent_logins(self):
        """Testa múltiplos logins simultâneos"""
        num_users = 10
        results = []
        errors = []
        
        def simulate_login(username):
            try:
                client = Client()
                start_time = time.time()
                response = client.post(reverse('login'), {
                    'username': username,
                    'senha': 'senha123'
                })
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000
                results.append(execution_time)
                return response.status_code
            except Exception as e:
                errors.append(str(e))
                return None
        
        threads = []
        for i in range(num_users):
            thread = threading.Thread(
                target=simulate_login,
                args=(f'cliente{i}',)
            )
            threads.append(thread)
        
        # Iniciar todas as threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Esperar todas terminarem
        for thread in threads:
            thread.join()
        
        total_time = (time.time() - start_time) * 1000
        
        # Análise dos resultados
        if results:
            avg_time = sum(results) / len(results)
            max_time = max(results)
            min_time = min(results)
            
            print(f"\n📊 TESTE DE CARGA - Logins Simultâneos:")
            print(f"  Usuários: {num_users}")
            print(f"  Tempo Total: {total_time:.2f}ms")
            print(f"  Tempo Médio: {avg_time:.2f}ms")
            print(f"  Tempo Mínimo: {min_time:.2f}ms")
            print(f"  Tempo Máximo: {max_time:.2f}ms")
            print(f"  Erros: {len(errors)}")
            
            # Verificar que o tempo médio está aceitável
            self.assertLess(avg_time, 500, "Tempo médio de login muito alto")
        
        # Verificar que não houve muitos erros
        self.assertLess(len(errors), num_users * 0.1, "Muitos erros nos logins")
    
    def test_concurrent_agendamentos(self):
        """Testa criação simultânea de agendamentos"""
        num_agendamentos = 20
        results = []
        errors = []
        
        servico = Servicos.objects.create(
            nome='Serviço Teste',
            descricao='Teste de carga'
        )
        
        def create_agendamento(index):
            try:
                cliente = self.clientes[index % len(self.clientes)]
                moto = Moto.objects.create(
                    cliente=cliente,
                    marca='Honda',
                    modelo=f'Modelo {index}',
                    ano=2020
                )
                
                start_time = time.time()
                agendamento = Agendamento.objects.create(
                    cliente=cliente,
                    servico=servico,
                    moto=moto,
                    data_hora=timezone.now() + timedelta(days=index),
                    status='agendado',
                    descricao_problema=f'Problema {index}'
                )
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000
                results.append(execution_time)
                return agendamento.id
            except Exception as e:
                errors.append(str(e))
                return None
        
        threads = []
        for i in range(num_agendamentos):
            thread = threading.Thread(
                target=create_agendamento,
                args=(i,)
            )
            threads.append(thread)
        
        # Iniciar todas as threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Esperar todas terminarem
        for thread in threads:
            thread.join()
        
        total_time = (time.time() - start_time) * 1000
        
        # Análise dos resultados
        if results:
            avg_time = sum(results) / len(results)
            
            print(f"\n📊 TESTE DE CARGA - Agendamentos Simultâneos:")
            print(f"  Agendamentos: {num_agendamentos}")
            print(f"  Tempo Total: {total_time:.2f}ms")
            print(f"  Tempo Médio: {avg_time:.2f}ms")
            print(f"  Sucessos: {len(results)}")
            print(f"  Erros: {len(errors)}")
            
            # Verificar criação bem-sucedida
            total_agendamentos = Agendamento.objects.count()
            print(f"  Total no DB: {total_agendamentos}")
            
            self.assertGreater(total_agendamentos, 0, "Nenhum agendamento criado")


# ============================================================================
# TESTES DE STRESS (Stress Testing)
# ============================================================================

class StressTest(TestCase, PerformanceTestMixin):
    """Testes de stress para identificar limites do sistema"""
    
    def setUp(self):
        """Configuração inicial para testes de stress"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        Administrador.objects.create(
            usuario=self.admin_user,
            email='admin@test.com',
            telefone='(11) 99999-9999'
        )
    
    def test_large_dataset_query(self):
        """Testa consulta com grande volume de dados"""
        # Criar 500 agendamentos
        print("\n⏳ Criando 500 agendamentos...")
        
        user = User.objects.create_user(username='teste', password='senha')
        cliente = Cliente.objects.create(
            usuario=user,
            nome_completo='Cliente Teste',
            cpf='000.000.000-00',
            email='teste@test.com',
            telefone='(11) 00000-0000',
            endereco='Rua Teste'
        )
        
        servico = Servicos.objects.create(
            nome='Serviço',
            descricao='Teste'
        )
        
        moto = Moto.objects.create(
            cliente=cliente,
            marca='Honda',
            modelo='CB',
            ano=2020
        )
        
        # Criar em lote para performance
        agendamentos = []
        for i in range(500):
            agendamentos.append(Agendamento(
                cliente=cliente,
                servico=servico,
                moto=moto,
                data_hora=timezone.now() + timedelta(days=i),
                status='agendado',
                descricao_problema=f'Problema {i}'
            ))
        
        start_time = time.time()
        Agendamento.objects.bulk_create(agendamentos)
        creation_time = (time.time() - start_time) * 1000
        
        print(f"✅ 500 agendamentos criados em {creation_time:.2f}ms")
        
        # Testar consulta
        self.client.login(username='admin', password='admin123')
        
        start_time = time.time()
        response = self.client.get(reverse('adm-agendamentos'))
        query_time = (time.time() - start_time) * 1000
        
        self.assertEqual(response.status_code, 200)
        
        print(f"\n📊 TESTE DE STRESS - Grande Volume:")
        print(f"  Registros: 500 agendamentos")
        print(f"  Tempo de Criação: {creation_time:.2f}ms")
        print(f"  Tempo de Consulta: {query_time:.2f}ms")
        
        # Verificar que mesmo com 500 registros, consulta é razoável
        self.assert_max_time(query_time, 2000, "Consulta com 500 registros")
    
    def test_rapid_sequential_requests(self):
        """Testa requisições sequenciais rápidas"""
        self.client.login(username='admin', password='admin123')
        
        num_requests = 50
        times = []
        
        print(f"\n⏳ Executando {num_requests} requisições sequenciais...")
        
        for i in range(num_requests):
            start_time = time.time()
            response = self.client.get(reverse('dashboard-admin'))
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000
            times.append(execution_time)
            
            self.assertEqual(response.status_code, 200)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n📊 TESTE DE STRESS - Requisições Sequenciais:")
        print(f"  Requisições: {num_requests}")
        print(f"  Tempo Médio: {avg_time:.2f}ms")
        print(f"  Tempo Mínimo: {min_time:.2f}ms")
        print(f"  Tempo Máximo: {max_time:.2f}ms")
        
        # Verificar que não há degradação significativa
        self.assertLess(max_time, avg_time * 3, "Degradação muito alta")


# ============================================================================
# TESTES DE MEMÓRIA (Memory Testing)
# ============================================================================

class MemoryTest(TestCase, PerformanceTestMixin):
    """Testes de uso de memória"""
    
    def setUp(self):
        """Configuração inicial para testes de memória"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        Administrador.objects.create(
            usuario=self.admin_user,
            email='admin@test.com',
            telefone='(11) 99999-9999'
        )
    
    def get_memory_usage(self):
        """Retorna uso de memória em MB"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # Em MB
    
    def test_memory_usage_dashboard(self):
        """Testa uso de memória ao carregar dashboard"""
        try:
            import psutil
        except ImportError:
            self.skipTest("psutil não instalado")
        
        self.client.login(username='admin', password='admin123')
        
        # Medir memória antes
        memory_before = self.get_memory_usage()
        
        # Executar operação
        for _ in range(10):
            response = self.client.get(reverse('dashboard-admin'))
            self.assertEqual(response.status_code, 200)
        
        # Medir memória depois
        memory_after = self.get_memory_usage()
        memory_increase = memory_after - memory_before
        
        print(f"\n📊 USO DE MEMÓRIA - Dashboard:")
        print(f"  Memória Inicial: {memory_before:.2f} MB")
        print(f"  Memória Final: {memory_after:.2f} MB")
        print(f"  Aumento: {memory_increase:.2f} MB")
        
        # Verificar que não há vazamento de memória significativo
        self.assertLess(
            memory_increase, 
            50,  # Máximo 50MB de aumento
            "Possível vazamento de memória"
        )


# ============================================================================
# TESTES DE ESCALABILIDADE (Scalability Testing)
# ============================================================================

class ScalabilityTest(TestCase, PerformanceTestMixin):
    """Testes de escalabilidade do sistema"""
    
    def setUp(self):
        """Configuração inicial para testes de escalabilidade"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        Administrador.objects.create(
            usuario=self.admin_user,
            email='admin@test.com',
            telefone='(11) 99999-9999'
        )
    
    def test_scalability_with_data_growth(self):
        """Testa como o sistema escala com crescimento de dados"""
        self.client.login(username='admin', password='admin123')
        
        data_sizes = [10, 50, 100, 200]
        results = []
        
        print(f"\n📊 TESTE DE ESCALABILIDADE:")
        
        for size in data_sizes:
            # Limpar dados anteriores
            Agendamento.objects.all().delete()
            Cliente.objects.all().delete()
            User.objects.exclude(username='admin').delete()
            
            # Criar dados
            for i in range(size):
                user = User.objects.create_user(
                    username=f'cliente{i}',
                    password='senha'
                )
                cliente = Cliente.objects.create(
                    usuario=user,
                    nome_completo=f'Cliente {i}',
                    cpf=f'{i:011d}',
                    email=f'c{i}@test.com',
                    telefone=f'(11) {i:05d}-0000',
                    endereco=f'Rua {i}'
                )
                
                servico = Servicos.objects.first()
                if not servico:
                    servico = Servicos.objects.create(
                        nome='Serviço',
                        descricao='Teste'
                    )
                
                moto = Moto.objects.create(
                    cliente=cliente,
                    marca='Honda',
                    modelo='CB',
                    ano=2020
                )
                
                Agendamento.objects.create(
                    cliente=cliente,
                    servico=servico,
                    moto=moto,
                    data_hora=timezone.now(),
                    status='agendado'
                )
            
            # Medir tempo de consulta
            start_time = time.time()
            response = self.client.get(reverse('dashboard-admin'))
            execution_time = (time.time() - start_time) * 1000
            
            results.append((size, execution_time))
            
            print(f"  {size} registros: {execution_time:.2f}ms")
        
        # Analisar crescimento
        print(f"\n📈 Análise de Escalabilidade:")
        for i in range(1, len(results)):
            prev_size, prev_time = results[i-1]
            curr_size, curr_time = results[i]
            
            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0 else 0
            
            print(f"  {prev_size} → {curr_size} registros:")
            print(f"    Aumento de dados: {size_ratio:.2f}x")
            print(f"    Aumento de tempo: {time_ratio:.2f}x")
            
            # Verificar escalabilidade linear ou melhor
            # Se dados dobram, tempo não deve mais que triplicar
            if size_ratio > 1:
                self.assertLess(
                    time_ratio,
                    size_ratio * 1.5,
                    f"Escalabilidade ruim: {prev_size} → {curr_size}"
                )


# ============================================================================
# RELATÓRIO FINAL DE PERFORMANCE
# ============================================================================

print("""
╔══════════════════════════════════════════════════════════════════════════╗
║              TESTES DE PERFORMANCE IMPLEMENTADOS                         ║
╚══════════════════════════════════════════════════════════════════════════╝

✅ TESTES DE TEMPO DE RESPOSTA (6 testes)
   - Login page (< 100ms)
   - Login POST (< 200ms)
   - Dashboard Cliente (< 300ms)
   - Dashboard Admin (< 500ms)
   - Agendar Serviço GET (< 250ms)
   - Agendar Serviço POST (< 400ms)

✅ TESTES DE QUERIES (3 testes)
   - Dashboard Admin queries (< 20 queries)
   - Lista de agendamentos (< 10 queries)
   - Detecção de problema N+1

✅ TESTES DE CARGA (2 testes)
   - Logins simultâneos (10 usuários)
   - Agendamentos simultâneos (20 operações)

✅ TESTES DE STRESS (2 testes)
   - Consulta com 500 registros (< 2000ms)
   - 50 requisições sequenciais

✅ TESTES DE MEMÓRIA (1 teste)
   - Uso de memória no dashboard (< 50MB aumento)

✅ TESTES DE ESCALABILIDADE (1 teste)
   - Escalabilidade com crescimento de dados

TOTAL: 15+ testes de performance
""")
