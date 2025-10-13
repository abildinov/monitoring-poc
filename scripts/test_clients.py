"""
Скрипт проверки работы всех клиентов
Проверяет подключение к Prometheus, Loki и Ollama
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к mcp-server
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from clients.prometheus_client import PrometheusClient
from clients.loki_client import LokiClient
from llm.ollama_client import OllamaClient
from config import settings


async def test_prometheus():
    """Тест Prometheus клиента"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ PROMETHEUS")
    print("="*60)
    
    client = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    
    try:
        # Health check
        is_healthy = await client.check_health()
        print(f"[+] Health check: {'OK' if is_healthy else 'FAIL'}")
        
        if is_healthy:
            # CPU
            cpu = await client.get_current_cpu()
            if cpu is not None:
                print(f"[+] CPU Usage: {cpu:.2f}%")
            
            # Memory
            memory = await client.get_current_memory()
            if memory:
                print(f"[+] Memory: {memory['percent']:.2f}% used ({memory['used_gb']:.2f}GB / {memory['total_gb']:.2f}GB)")
            
            # Disk
            disks = await client.get_disk_usage()
            if disks:
                print(f"[+] Disk usage:")
                for disk in disks[:3]:
                    print(f"    {disk['mountpoint']}: {disk['percent']:.1f}%")
        
        return True
    
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    finally:
        await client.close()


async def test_loki():
    """Тест Loki клиента"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ LOKI")
    print("="*60)
    
    client = LokiClient(settings.loki_url, settings.http_timeout)
    
    try:
        # Health check
        is_healthy = await client.check_health()
        print(f"[+] Health check: {'OK' if is_healthy else 'FAIL'}")
        
        if is_healthy:
            # Labels
            labels = await client.get_log_labels()
            if labels:
                print(f"[+] Доступные labels: {', '.join(labels)}")
            
            # Containers
            if labels and "container_name" in labels:
                containers = await client.get_label_values("container_name")
                if containers:
                    print(f"[+] Контейнеры: {', '.join(containers)}")
            
            # Ошибки
            errors = await client.get_error_logs(hours=24, limit=5)
            print(f"[+] Найдено ошибок за 24ч: {len(errors)}")
            if errors:
                print(f"  Последние ошибки:")
                for err in errors[:2]:
                    print(f"    [{err['timestamp']}] {err['container']}: {err['message'][:60]}...")
        
        return True
    
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    finally:
        await client.close()


async def test_ollama():
    """Тест Ollama клиента"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ OLLAMA (локальная LLM)")
    print("="*60)
    
    client = OllamaClient(
        settings.ollama_host, 
        settings.ollama_model, 
        settings.ollama_timeout
    )
    
    try:
        # Health check
        is_healthy = await client.check_health()
        print(f"[+] Health check: {'OK' if is_healthy else 'FAIL'}")
        
        if is_healthy:
            # Простой тест генерации
            print(f"[+] Модель: {settings.ollama_model}")
            print(f"  Тестовый запрос...")
            
            response = await client.generate(
                "Объясни в одном предложении, что такое CPU load average?",
                temperature=0.5
            )
            print(f"[+] Ответ получен ({len(response)} символов):")
            print(f"  {response[:200]}...")
            
            # Тест анализа метрик
            print(f"\n  Тест анализа метрик...")
            analysis = await client.analyze_metrics({
                "cpu_percent": 75.0,
                "memory_percent": 82.0,
                "disk_percent": 45.0
            })
            print(f"[+] Анализ метрик:")
            print(f"  {analysis[:150]}...")
        
        return True
    
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    finally:
        await client.close()


async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("ПРОВЕРКА ВСЕХ КОМПОНЕНТОВ СИСТЕМЫ")
    print("="*60)
    print(f"\nКонфигурация:")
    print(f"  Prometheus: {settings.prometheus_url}")
    print(f"  Loki: {settings.loki_url}")
    print(f"  Ollama: {settings.ollama_host}")
    
    # Запускаем тесты
    results = []
    
    results.append(("Prometheus", await test_prometheus()))
    results.append(("Loki", await test_loki()))
    results.append(("Ollama", await test_ollama()))
    
    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ")
    print("="*60)
    
    for name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"{name:15} {status}")
    
    all_ok = all(success for _, success in results)
    
    print("\n" + "="*60)
    if all_ok:
        print("ВСЕ КОМПОНЕНТЫ РАБОТАЮТ!")
        print("Готовы к разработке MCP сервера.")
    else:
        print("НЕКОТОРЫЕ КОМПОНЕНТЫ НЕ РАБОТАЮТ")
        print("Проверьте доступность сервисов.")
    print("="*60 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

