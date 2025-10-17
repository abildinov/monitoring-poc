"""
Интерактивный чат с Ollama для запросов о метриках сервера
Позволяет общаться с LLM и получать данные о системе в реальном времени
"""

import asyncio
import sys
from datetime import datetime
from loguru import logger

from clients.prometheus_client import PrometheusClient
from clients.loki_client import LokiClient
from llm.ollama_client import OllamaClient
from config import settings

# Настройка логирования
logger.remove()
logger.add(
    sys.stderr,
    level="WARNING",  # Показываем только предупреждения и ошибки
    format="<red>{level}</red>: {message}"
)


class MonitoringChat:
    """Интерактивный чат с доступом к метрикам"""
    
    def __init__(self):
        self.prometheus = None
        self.loki = None
        self.ollama = None
        self.running = True
        
    async def initialize(self):
        """Инициализация клиентов"""
        print("\n" + "="*70)
        print("МОНИТОРИНГ ЧАТ - Интерактивное общение с системой")
        print("="*70)
        print("\nИнициализация компонентов...")
        
        self.prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
        self.loki = LokiClient(settings.loki_url, settings.http_timeout)
        self.ollama = OllamaClient(
            settings.ollama_host,
            settings.ollama_model,
            settings.ollama_timeout
        )
        
        # Проверка доступности
        prom_ok = await self.prometheus.check_health()
        loki_ok = await self.loki.check_health()
        ollama_ok = await self.ollama.check_health()
        
        print(f"  Prometheus: {'[OK]' if prom_ok else '[FAIL]'}")
        print(f"  Loki:       {'[OK]' if loki_ok else '[FAIL]'}")
        print(f"  Ollama:     {'[OK]' if ollama_ok else '[FAIL]'}")
        
        if not all([prom_ok, loki_ok, ollama_ok]):
            print("\n[!] Предупреждение: Некоторые компоненты недоступны")
        
        print("\n" + "="*70)
        print("\nДоступные команды:")
        print("  /cpu       - Показать загрузку CPU")
        print("  /memory    - Показать использование памяти")
        print("  /disk      - Показать использование дисков")
        print("  /logs      - Показать последние ошибки в логах")
        print("  /status    - Полный статус системы")
        print("  /help      - Показать эту справку")
        print("  /exit      - Выход")
        print("\nИли просто задавайте вопросы на русском языке!")
        print("Например: 'Какая нагрузка на сервере?' или 'Есть ли проблемы?'")
        print("="*70 + "\n")
    
    async def get_cpu_info(self):
        """Получить информацию о CPU"""
        cpu = await self.prometheus.get_current_cpu()
        if cpu is None:
            return "Ошибка получения CPU метрик"
        
        status = "ВЫСОКАЯ" if cpu > settings.cpu_threshold else "НОРМАЛЬНАЯ"
        return f"CPU: {cpu:.2f}% (порог: {settings.cpu_threshold}%) - {status}"
    
    async def get_memory_info(self):
        """Получить информацию о памяти"""
        memory = await self.prometheus.get_current_memory()
        if memory is None:
            return "Ошибка получения Memory метрик"
        
        status = "ВЫСОКОЕ" if memory['percent'] > settings.memory_threshold else "НОРМАЛЬНОЕ"
        return f"""Memory:
  Total:     {memory['total_gb']:.2f} GB
  Used:      {memory['used_gb']:.2f} GB
  Available: {memory['available_gb']:.2f} GB
  Usage:     {memory['percent']:.2f}% (порог: {settings.memory_threshold}%)
  Status:    {status}"""
    
    async def get_disk_info(self):
        """Получить информацию о дисках"""
        disks = await self.prometheus.get_disk_usage()
        if not disks:
            return "Ошибка получения Disk метрик"
        
        result = "Disk Usage:\n"
        for disk in disks[:5]:
            status = "HIGH" if disk['percent'] > settings.disk_threshold else "OK"
            result += f"  {disk['mountpoint']:20} {disk['percent']:5.1f}% [{status}]\n"
        
        return result
    
    async def get_logs_info(self):
        """Получить последние ошибки"""
        errors = await self.loki.get_error_logs(hours=24, limit=10)
        
        if not errors:
            return "Ошибок за последние 24 часа не найдено [OK]"
        
        result = f"Найдено {len(errors)} ошибок за последние 24ч:\n\n"
        for i, err in enumerate(errors[:5], 1):
            result += f"{i}. [{err['timestamp']}] {err['container']}\n"
            result += f"   {err['message'][:80]}...\n\n"
        
        return result
    
    async def get_full_status(self):
        """Получить полный статус системы"""
        print("\n[~] Сбор данных о системе...")
        
        cpu_info = await self.get_cpu_info()
        memory_info = await self.get_memory_info()
        disk_info = await self.get_disk_info()
        logs_info = await self.get_logs_info()
        
        status = f"""
СТАТУС СИСТЕМЫ ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):

{cpu_info}

{memory_info}

{disk_info}

{logs_info}
"""
        return status
    
    async def get_network_info(self) -> str:
        """Получить информацию о сети"""
        try:
            network_data = await self.prometheus.get_network_status()
            
            result = "Network Status:\n"
            result += f"Status: {network_data['status'].upper()}\n\n"
            
            # Трафик
            traffic = network_data['traffic']
            result += f"Traffic:\n"
            result += f"  Total interfaces: {traffic['total_interfaces']}\n"
            result += f"  Active interfaces: {traffic['active_interfaces']}\n"
            
            for interface, data in traffic['interfaces'].items():
                rx_gb = data.get('rx_bytes', 0) / (1024**3)
                tx_gb = data.get('tx_bytes', 0) / (1024**3)
                status = "UP" if data.get('up', False) else "DOWN"
                result += f"  {interface}: RX={rx_gb:.2f}GB, TX={tx_gb:.2f}GB [{status}]\n"
            
            # Соединения
            connections = network_data['connections']
            result += f"\nConnections:\n"
            result += f"  TCP established: {connections['tcp_established']}\n"
            result += f"  UDP datagrams: {connections['udp_datagrams']}\n"
            result += f"  Total: {connections['total']}\n"
            
            # Ошибки
            errors = network_data['errors']
            result += f"\nErrors:\n"
            result += f"  RX errors: {errors['rx_errors']}\n"
            result += f"  TX errors: {errors['tx_errors']}\n"
            result += f"  Total errors: {errors['total_errors']}\n"
            
            if errors['interfaces_with_errors']:
                result += f"  Interfaces with errors: {', '.join(errors['interfaces_with_errors'])}\n"
            
            return result
            
        except Exception as e:
            return f"Ошибка получения информации о сети: {e}"
    
    async def get_processes_info(self) -> str:
        """Получить информацию о процессах"""
        try:
            cpu_processes = await self.prometheus.get_top_processes_by_cpu(10)
            memory_processes = await self.prometheus.get_top_processes_by_memory(10)
            
            result = "Top Processes:\n\n"
            
            # CPU процессы
            result += "CPU Usage:\n"
            if cpu_processes:
                for process in cpu_processes:
                    result += f"  {process['rank']}. {process['name']}: {process['cpu_usage']:.2f}%\n"
            else:
                result += "  No CPU process data available\n"
            
            # Memory процессы
            result += "\nMemory Usage:\n"
            if memory_processes:
                for process in memory_processes:
                    result += f"  {process['rank']}. {process['name']}: {process['memory_usage_gb']:.2f}GB ({process['memory_percent']:.1f}%)\n"
            else:
                result += "  No memory process data available\n"
            
            return result
            
        except Exception as e:
            return f"Ошибка получения информации о процессах: {e}"
    
    async def get_alerts_info(self) -> str:
        """Получить информацию об алертах"""
        try:
            # Инициализируем AlertManager если еще не инициализирован
            if not hasattr(self, 'alert_manager'):
                from alerts.alert_manager import AlertManager
                self.alert_manager = AlertManager()
            
            # Получаем активные алерты
            active_alerts = self.alert_manager.get_active_alerts()
            
            result = "Active Alerts:\n"
            
            if not active_alerts:
                result += "  No active alerts\n"
            else:
                result += f"  Total active alerts: {len(active_alerts)}\n\n"
                
                for alert in active_alerts:
                    severity_emoji = {
                        'critical': '🚨',
                        'warning': '⚠️',
                        'info': 'ℹ️'
                    }
                    emoji = severity_emoji.get(alert.severity, '📢')
                    
                    time_str = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    result += f"  {emoji} {alert.name} ({alert.severity.upper()})\n"
                    result += f"    Message: {alert.message}\n"
                    result += f"    Metric: {alert.metric_name}\n"
                    result += f"    Current: {alert.current_value:.2f}\n"
                    result += f"    Threshold: {alert.threshold}\n"
                    result += f"    Time: {time_str}\n\n"
            
            # Статистика
            stats = self.alert_manager.get_stats()
            result += f"Statistics:\n"
            result += f"  Active alerts: {stats['active_alerts']}\n"
            result += f"  Total history: {stats['total_history']}\n"
            result += f"  Rules count: {stats['rules_count']}\n"
            
            if stats['severity_breakdown']:
                result += f"  Severity breakdown:\n"
                for severity, count in stats['severity_breakdown'].items():
                    result += f"    {severity}: {count}\n"
            
            return result
            
        except Exception as e:
            return f"Ошибка получения информации об алертах: {e}"
    
    async def ask_llm(self, question: str, include_metrics: bool = True):
        """Задать вопрос LLM с контекстом метрик"""
        
        context = ""
        
        if include_metrics:
            print("\n[~] Получение метрик...")
            
            # Собираем актуальные данные
            cpu = await self.prometheus.get_current_cpu()
            memory = await self.prometheus.get_current_memory()
            disks = await self.prometheus.get_disk_usage()
            errors = await self.loki.get_error_logs(hours=1, limit=5)
            
            context = f"""
Текущие метрики сервера:
- CPU: {cpu:.2f}% (порог: {settings.cpu_threshold}%)
- Memory: {memory['percent']:.2f}% (используется {memory['used_gb']:.2f} GB из {memory['total_gb']:.2f} GB)
- Disk: {len(disks) if disks else 0} дисков
- Ошибки за последний час: {len(errors)}
"""
        
        # Формируем системный промпт
        system_prompt = """Ты - помощник по мониторингу серверной инфраструктуры.
У тебя есть доступ к метрикам сервера через Prometheus и логам через Loki.

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Никогда не используй английский язык в ответах.
Отвечай кратко, понятно, на русском языке.
Если видишь проблемы - указывай их и давай рекомендации."""
        
        full_prompt = f"{context}\n\nВопрос пользователя: {question}"
        
        print("[~] Отправка запроса в Ollama (может занять 30-60 сек)...")
        
        response = await self.ollama.generate(
            prompt=full_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=1024
        )
        
        return response
    
    async def process_command(self, command: str):
        """Обработка команды или вопроса"""
        
        command = command.strip()
        
        if not command:
            return
        
        # Команды
        if command == "/exit":
            self.running = False
            print("\nДо свидания!")
            return
        
        elif command == "/help":
            print("\nДоступные команды:")
            print("  /cpu       - Показать загрузку CPU")
            print("  /memory    - Показать использование памяти")
            print("  /disk      - Показать использование дисков")
            print("  /logs      - Показать последние ошибки")
            print("  /network   - Показать статус сети")
            print("  /processes - Показать топ процессов")
            print("  /alerts    - Показать активные алерты")
            print("  /status    - Полный статус системы")
            print("  /help      - Эта справка")
            print("  /exit      - Выход")
            return
        
        elif command == "/cpu":
            result = await self.get_cpu_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/memory":
            result = await self.get_memory_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/disk":
            result = await self.get_disk_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/logs":
            result = await self.get_logs_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/network":
            result = await self.get_network_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/processes":
            result = await self.get_processes_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/alerts":
            result = await self.get_alerts_info()
            print(f"\n{result}\n")
            return
        
        elif command == "/status":
            result = await self.get_full_status()
            print(result)
            return
        
        # Если это не команда, отправляем вопрос в LLM
        else:
            try:
                response = await self.ask_llm(command)
                print(f"\n{response}\n")
            except Exception as e:
                print(f"\n[!] Ошибка: {e}\n")
    
    async def run(self):
        """Основной цикл чата"""
        await self.initialize()
        
        while self.running:
            try:
                # Читаем ввод пользователя
                user_input = input("Вы> ").strip()
                
                if user_input:
                    await self.process_command(user_input)
                    
            except KeyboardInterrupt:
                print("\n\nПрервано пользователем")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"\n[!] Ошибка: {e}\n")
        
        # Закрытие соединений
        await self.cleanup()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.prometheus:
            await self.prometheus.close()
        if self.loki:
            await self.loki.close()
        if self.ollama:
            await self.ollama.close()


async def main():
    """Главная функция"""
    chat = MonitoringChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nВыход...")
    except Exception as e:
        print(f"\n[!] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

