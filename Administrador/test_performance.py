import time
import statistics
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.test.utils import override_settings
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

from Administrador.models import (
    Servicos, Moto, Cliente, Mecanico, Administrador,
    Agendamento, OrdemServico
)


class PerformanceTestCase(TestCase):
    """Classe base para testes de performance com utilitários"""
    
    def setUp(self):
        self.client = Client()
        self.performance_data = {}
    
    def measure_time(self, func, *args, **kwargs):
        """Mede o tempo de execução de uma função"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    def measure_memory(self):
        """Mede uso de memória atual"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def create_bulk_data(self, num_records=100):
        """Cria dados em massa para testes de carga"""
        users = []
        clientes = []
        motos = []
        servicos = []
        agendamentos = []
        
        # Criar usuários em lote
        # Gerar IDs únicos baseados em timestamp para evitar conflitos
        import time
        timestamp = int(time.time() * 1000000)  # microseconds
        
        for i in range(num_records):
            user = User(
                username=f'perfuser_{timestamp}_{i}',
                email=f'perfuser_{timestamp}_{i}@test.com',
                first_name=f'PerfUser{i}'
            )
            user.set_password('testpass123')
            users.append(user)
        
        User.objects.bulk_create(users)
        created_users = User.objects.filter(username__startswith=f'perfuser_{timestamp}_')
        
        # Criar clientes
        for user in created_users:
            clientes.append(Cliente(
                usuario=user,
                telefone=f'(11) 9999-{user.id:04d}',
                endereco=f'Rua Test {user.id}'
            ))
        Cliente.objects.bulk_create(clientes)
        
        # Criar motos
        marcas = ['Honda', 'Yamaha', 'Suzuki', 'Kawasaki', 'BMW']
        modelos = ['CB600F', 'MT-07', 'GSX-R', 'Ninja', 'R1200']
        
        for i in range(num_records):
            motos.append(Moto(
                marca=marcas[i % len(marcas)],
                modelo=modelos[i % len(modelos)],
                ano=2015 + (i % 8)
            ))
        Moto.objects.bulk_create(motos)
        
        # Criar serviços
        servico_tipos = ['Troca de óleo', 'Revisão', 'Reparo freios', 'Balanceamento', 'Troca pneus']
        for i, tipo in enumerate(servico_tipos):
            servicos.append(Servicos(
                nome=tipo,
                descricao=f'Descrição do serviço {tipo}'
            ))
        Servicos.objects.bulk_create(servicos)
        
        # Criar agendamentos
        created_clientes = Cliente.objects.all()[:num_records]
        created_motos = Moto.objects.all()[:num_records]
        created_servicos = Servicos.objects.all()
        
        for i in range(num_records):
            cliente = created_clientes[i % len(created_clientes)]
            moto = created_motos[i % len(created_motos)]
            servico = created_servicos[i % len(created_servicos)]
            
            agendamentos.append(Agendamento(
                cliente=cliente,
                servico=servico,
                moto=moto,
                data_hora=timezone.now() + timedelta(days=i % 30),
                status=['agendado', 'em_andamento', 'concluido', 'cancelado'][i % 4]
            ))
        
        Agendamento.objects.bulk_create(agendamentos)
        
        return {
            'users': len(users),
            'clientes': len(clientes),
            'motos': len(motos),
            'servicos': len(servicos),
            'agendamentos': len(agendamentos)
        }


class ViewResponseTimeTests(PerformanceTestCase):
    """Testes de tempo de resposta das views principais"""
    
    def setUp(self):
        super().setUp()
        # Criar dados mínimos para os testes
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.admin_user = User.objects.create_user(
            username='admin', password='pass', is_staff=True
        )
        self.admin_profile = Administrador.objects.create(
            usuario=self.admin_user, email='admin@test.com', telefone='123'
        )
        self.cliente = Cliente.objects.create(
            usuario=self.user, telefone='123', endereco='Rua A'
        )
    
    def test_dashboard_cliente_response_time(self):
        """Testa tempo de resposta do dashboard do cliente"""
        url = reverse('dashboard-cliente')
        
        # Teste sem dados
        response, time_empty = self.measure_time(self.client.get, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(time_empty, 1.0, "Dashboard vazio deve responder em < 1s")
        
        # Criar alguns dados
        self.create_bulk_data(50)
        
        # Teste com dados
        response, time_with_data = self.measure_time(self.client.get, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(time_with_data, 2.0, "Dashboard com dados deve responder em < 2s")
        
        print(f"Dashboard - Vazio: {time_empty:.3f}s, Com dados: {time_with_data:.3f}s")
    
    def test_login_response_time(self):
        """Testa tempo de resposta da página de login"""
        url = reverse('login')
        
        # GET request
        response, get_time = self.measure_time(self.client.get, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(get_time, 0.5, "Página de login deve carregar em < 0.5s")
        
        # POST request válido
        login_data = {'username': 'testuser', 'password': 'pass'}
        response, post_time = self.measure_time(self.client.post, url, login_data)
        self.assertIn(response.status_code, [200, 302])
        self.assertLess(post_time, 1.0, "Login deve processar em < 1s")
        
        print(f"Login - GET: {get_time:.3f}s, POST: {post_time:.3f}s")
    
    def test_admin_dashboard_response_time(self):
        """Testa tempo de resposta do dashboard admin"""
        self.client.login(username='admin', password='pass')
        url = reverse('dashboard-admin')
        
        response, admin_time = self.measure_time(self.client.get, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(admin_time, 1.5, "Dashboard admin deve responder em < 1.5s")
        
        print(f"Dashboard Admin: {admin_time:.3f}s")
    
    def test_agendar_servico_response_time(self):
        """Testa tempo de resposta da página de agendamento"""
        self.client.login(username='testuser', password='pass')
        url = reverse('agendar-servico')
        
        # GET request
        response, get_time = self.measure_time(self.client.get, url)
        self.assertEqual(response.status_code, 200)
        self.assertLess(get_time, 1.0, "Página de agendamento deve carregar em < 1s")
        
        print(f"Agendar Serviço - GET: {get_time:.3f}s")


class ScalabilityTests(PerformanceTestCase):
    """Testes de escalabilidade com grandes volumes de dados"""
    
    def test_dashboard_performance_with_large_dataset(self):
        """Testa performance do dashboard com muitos dados"""
        sizes = [100, 500, 1000]
        times = []
        
        for size in sizes:
            # Limpar dados anteriores
            Agendamento.objects.all().delete()
            Cliente.objects.all().delete()
            User.objects.filter(username__startswith='perfuser_').delete()
            Moto.objects.all().delete()
            Servicos.objects.all().delete()
            
            # Criar dados
            memory_before = self.measure_memory()
            creation_start = time.perf_counter()
            
            data_created = self.create_bulk_data(size)
            
            creation_time = time.perf_counter() - creation_start
            memory_after = self.measure_memory()
            
            # Testar dashboard
            url = reverse('dashboard-cliente')
            response, dashboard_time = self.measure_time(self.client.get, url)
            
            self.assertEqual(response.status_code, 200)
            
            result = {
                'size': size,
                'creation_time': creation_time,
                'dashboard_time': dashboard_time,
                'memory_used': memory_after - memory_before,
                'data_created': data_created
            }
            times.append(result)
            
            print(f"Size {size}: Dashboard {dashboard_time:.3f}s, "
                  f"Creation {creation_time:.3f}s, Memory {result['memory_used']:.1f}MB")
        
        # Verificar que o tempo não cresce exponencialmente
        time_1000 = next(t['dashboard_time'] for t in times if t['size'] == 1000)
        time_100 = next(t['dashboard_time'] for t in times if t['size'] == 100)
        
        growth_factor = time_1000 / time_100
        self.assertLess(growth_factor, 5.0, 
            f"Tempo não deve crescer mais que 5x com 10x mais dados. "
            f"Atual: {growth_factor:.2f}x")
    
    def test_database_query_performance(self):
        """Testa performance de queries específicas"""
        self.create_bulk_data(1000)
        
        # Query complexa: agendamentos com relacionamentos
        query_start = time.perf_counter()
        agendamentos = list(Agendamento.objects.select_related(
            'cliente__usuario', 'moto', 'servico'
        ).filter(status='agendado')[:100])
        query_time = time.perf_counter() - query_start
        
        self.assertLess(query_time, 0.5, "Query complexa deve executar em < 0.5s")
        self.assertGreater(len(agendamentos), 0, "Deve retornar resultados")
        
        print(f"Query complexa (1000 registros): {query_time:.3f}s, "
              f"Resultados: {len(agendamentos)}")


class ConcurrencyTests(PerformanceTestCase):
    """Testes de concorrência simulando múltiplos usuários"""
    
    def setUp(self):
        super().setUp()
        # Criar múltiplos usuários para testes de concorrência
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'concurrent_user_{i}',
                password='pass'
            )
            Cliente.objects.create(
                usuario=user,
                telefone=f'(11) 9999-{i:04d}',
                endereco=f'Rua Concorrência {i}'
            )
            self.users.append(user)
    
    def simulate_user_session(self, username):
        """Simula uma sessão completa de usuário"""
        client = Client()
        times = {}
        
        # Login
        start = time.perf_counter()
        response = client.post(reverse('login'), {
            'username': username,
            'password': 'pass'
        })
        times['login'] = time.perf_counter() - start
        
        # Dashboard
        start = time.perf_counter()
        response = client.get(reverse('dashboard-cliente'))
        times['dashboard'] = time.perf_counter() - start
        
        # Agendar serviço (GET)
        start = time.perf_counter()
        response = client.get(reverse('agendar-servico'))
        times['agendar_get'] = time.perf_counter() - start
        
        # Lista serviços
        start = time.perf_counter()
        response = client.get(reverse('lista-servicos'))
        times['lista_servicos'] = time.perf_counter() - start
        
        times['total'] = sum(times.values())
        times['username'] = username
        
        return times
    
    def test_concurrent_users(self):
        """Testa múltiplos usuários simultâneos"""
        num_users = 5
        usernames = [f'concurrent_user_{i}' for i in range(num_users)]
        
        # Execução sequencial (baseline)
        sequential_times = []
        total_sequential_start = time.perf_counter()
        
        for username in usernames:
            times = self.simulate_user_session(username)
            sequential_times.append(times)
        
        total_sequential_time = time.perf_counter() - total_sequential_start
        
        # Execução concorrente
        concurrent_times = []
        total_concurrent_start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(self.simulate_user_session, username)
                for username in usernames
            ]
            
            for future in as_completed(futures):
                times = future.result()
                concurrent_times.append(times)
        
        total_concurrent_time = time.perf_counter() - total_concurrent_start
        
        # Análise dos resultados
        avg_sequential = statistics.mean([t['total'] for t in sequential_times])
        avg_concurrent = statistics.mean([t['total'] for t in concurrent_times])
        
        speedup = total_sequential_time / total_concurrent_time
        
        print(f"\nTeste de Concorrência ({num_users} usuários):")
        print(f"Tempo total sequencial: {total_sequential_time:.3f}s")
        print(f"Tempo total concorrente: {total_concurrent_time:.3f}s")
        print(f"Speedup: {speedup:.2f}x")
        print(f"Tempo médio por usuário - Seq: {avg_sequential:.3f}s, "
              f"Conc: {avg_concurrent:.3f}s")
        
        # Verificações (ajustadas para aplicação simples)
        self.assertGreater(speedup, 0.8, 
            f"Execução concorrente não deve ser muito mais lenta. "
            f"Atual: {speedup:.2f}x")
        
        # Nenhuma sessão individual deve ser muito lenta
        max_concurrent_time = max(t['total'] for t in concurrent_times)
        self.assertLess(max_concurrent_time, avg_sequential * 2,
            "Nenhuma sessão concorrente deve ser 2x mais lenta que a média sequencial")


class MemoryUsageTests(PerformanceTestCase):
    """Testes de uso de memória"""
    
    def test_memory_usage_dashboard(self):
        """Testa uso de memória do dashboard"""
        initial_memory = self.measure_memory()
        
        # Criar dados e medir memória uma única vez para evitar conflitos
        memory_before = self.measure_memory()
        
        # Criar dados de teste
        self.create_bulk_data(100)
        
        # Forçar coleta de lixo
        import gc
        gc.collect()
        
        # Carregar dashboard múltiplas vezes
        for i in range(5):
            response = self.client.get(reverse('dashboard-cliente'))
            self.assertEqual(response.status_code, 200)
        
        memory_after = self.measure_memory()
        memory_used = memory_after - memory_before
        
        print(f"Memory test: Used {memory_used:.1f}MB, Total {memory_after:.1f}MB")
        
        # Verificar que não há vazamentos excessivos
        memory_growth = memory_after - initial_memory
        
        self.assertLess(memory_growth, 50, 
            f"Crescimento de memória deve ser < 50MB. Atual: {memory_growth:.1f}MB")


class StressTests(PerformanceTestCase):
    """Testes de stress para identificar limites"""
    
    def test_rapid_requests(self):
        """Testa muitas requisições em sequência rápida"""
        url = reverse('dashboard-cliente')
        num_requests = 50
        times = []
        
        print(f"\nTeste de stress: {num_requests} requisições rápidas")
        
        for i in range(num_requests):
            response, request_time = self.measure_time(self.client.get, url)
            times.append(request_time)
            
            self.assertEqual(response.status_code, 200)
            
            if i % 10 == 0:
                print(f"Requisição {i}: {request_time:.3f}s")
        
        # Estatísticas
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\nEstatísticas ({num_requests} requisições):")
        print(f"Média: {avg_time:.3f}s")
        print(f"Mediana: {median_time:.3f}s")
        print(f"Mínimo: {min_time:.3f}s")
        print(f"Máximo: {max_time:.3f}s")
        
        # Verificações
        self.assertLess(avg_time, 1.0, "Tempo médio deve ser < 1s")
        self.assertLess(max_time, 3.0, "Tempo máximo deve ser < 3s")
        
        # Verificar se não há degradação significativa
        first_10 = statistics.mean(times[:10])
        last_10 = statistics.mean(times[-10:])
        degradation = last_10 / first_10
        
        self.assertLess(degradation, 2.0, 
            f"Performance não deve degradar > 2x. Atual: {degradation:.2f}x")