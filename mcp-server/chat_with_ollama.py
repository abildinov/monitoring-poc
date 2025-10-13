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

