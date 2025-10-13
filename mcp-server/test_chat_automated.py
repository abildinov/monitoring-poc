"""
Автоматический тест интерактивного чата
Проверяет работу всех компонентов без необходимости ручного ввода
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
logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")


async def test_initialization():
    """Тест инициализации всех клиентов"""
    print("\n" + "="*70)
    print("ТЕСТ 1: ИНИЦИАЛИЗАЦИЯ КОМПОНЕНТОВ")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    loki = LokiClient(settings.loki_url, settings.http_timeout)
    ollama = OllamaClient(
        settings.ollama_host,
        settings.ollama_model,
        settings.ollama_timeout
    )
    
    # Проверка доступности
    prom_ok = await prometheus.check_health()
    loki_ok = await loki.check_health()
    ollama_ok = await ollama.check_health()
    
    print(f"\n  Prometheus: {'[OK]' if prom_ok else '[FAIL]'}")
    print(f"  Loki:       {'[OK]' if loki_ok else '[FAIL]'}")
    print(f"  Ollama:     {'[OK]' if ollama_ok else '[FAIL]'}")
    
    success = all([prom_ok, loki_ok, ollama_ok])
    
    await prometheus.close()
    await loki.close()
    await ollama.close()
    
    return success, prometheus, loki, ollama


async def test_quick_command_cpu():
    """Тест команды /cpu"""
    print("\n" + "="*70)
    print("ТЕСТ 2: КОМАНДА /cpu")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    
    try:
        cpu = await prometheus.get_current_cpu()
        
        if cpu is None:
            print("\n  [FAIL] Не удалось получить CPU метрики")
            return False
        
        status = "ВЫСОКАЯ" if cpu > settings.cpu_threshold else "НОРМАЛЬНАЯ"
        print(f"\n  CPU: {cpu:.2f}% (порог: {settings.cpu_threshold}%)")
        print(f"  Статус: {status}")
        print("\n  [OK] Команда /cpu работает корректно")
        
        await prometheus.close()
        return True
        
    except Exception as e:
        print(f"\n  [FAIL] Ошибка: {e}")
        await prometheus.close()
        return False


async def test_quick_command_memory():
    """Тест команды /memory"""
    print("\n" + "="*70)
    print("ТЕСТ 3: КОМАНДА /memory")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    
    try:
        memory = await prometheus.get_current_memory()
        
        if memory is None:
            print("\n  [FAIL] Не удалось получить Memory метрики")
            return False
        
        status = "ВЫСОКОЕ" if memory['percent'] > settings.memory_threshold else "НОРМАЛЬНОЕ"
        
        print(f"\n  Memory:")
        print(f"    Total:     {memory['total_gb']:.2f} GB")
        print(f"    Used:      {memory['used_gb']:.2f} GB")
        print(f"    Available: {memory['available_gb']:.2f} GB")
        print(f"    Usage:     {memory['percent']:.2f}% (порог: {settings.memory_threshold}%)")
        print(f"    Статус:    {status}")
        print("\n  [OK] Команда /memory работает корректно")
        
        await prometheus.close()
        return True
        
    except Exception as e:
        print(f"\n  [FAIL] Ошибка: {e}")
        await prometheus.close()
        return False


async def test_quick_command_logs():
    """Тест команды /logs"""
    print("\n" + "="*70)
    print("ТЕСТ 4: КОМАНДА /logs")
    print("="*70)
    
    loki = LokiClient(settings.loki_url, settings.http_timeout)
    
    try:
        errors = await loki.get_error_logs(hours=24, limit=10)
        
        if errors:
            print(f"\n  Найдено {len(errors)} ошибок за последние 24ч:")
            for i, err in enumerate(errors[:3], 1):
                print(f"\n  {i}. [{err['timestamp']}] {err['container']}")
                print(f"     {err['message'][:60]}...")
        else:
            print("\n  Ошибок за последние 24 часа не найдено [OK]")
        
        print("\n  [OK] Команда /logs работает корректно")
        
        await loki.close()
        return True
        
    except Exception as e:
        print(f"\n  [FAIL] Ошибка: {e}")
        await loki.close()
        return False


async def test_full_status():
    """Тест команды /status"""
    print("\n" + "="*70)
    print("ТЕСТ 5: КОМАНДА /status")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    loki = LokiClient(settings.loki_url, settings.http_timeout)
    
    try:
        print(f"\n  СТАТУС СИСТЕМЫ ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):")
        
        # CPU
        cpu = await prometheus.get_current_cpu()
        if cpu:
            status = "ВЫСОКАЯ" if cpu > settings.cpu_threshold else "НОРМАЛЬНАЯ"
            print(f"\n  CPU: {cpu:.2f}% - {status}")
        
        # Memory
        memory = await prometheus.get_current_memory()
        if memory:
            status = "ВЫСОКОЕ" if memory['percent'] > settings.memory_threshold else "НОРМАЛЬНОЕ"
            print(f"  Memory: {memory['percent']:.2f}% ({memory['used_gb']:.2f}GB / {memory['total_gb']:.2f}GB) - {status}")
        
        # Disk
        disks = await prometheus.get_disk_usage()
        if disks:
            print(f"\n  Disks:")
            for disk in disks[:3]:
                status = "HIGH" if disk['percent'] > settings.disk_threshold else "OK"
                print(f"    {disk['mountpoint']:20} {disk['percent']:5.1f}% [{status}]")
        
        # Logs
        errors = await loki.get_error_logs(hours=1, limit=5)
        print(f"\n  Errors (last hour): {len(errors)}")
        
        print("\n  [OK] Команда /status работает корректно")
        
        await prometheus.close()
        await loki.close()
        return True
        
    except Exception as e:
        print(f"\n  [FAIL] Ошибка: {e}")
        await prometheus.close()
        await loki.close()
        return False


async def test_llm_question():
    """Тест работы с LLM на естественном языке"""
    print("\n" + "="*70)
    print("ТЕСТ 6: ВОПРОС К LLM")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    ollama = OllamaClient(
        settings.ollama_host,
        settings.ollama_model,
        settings.ollama_timeout
    )
    
    try:
        print("\n  Вопрос: 'Какая нагрузка на сервере?'")
        print("  [~] Получение метрик...")
        
        # Собираем метрики
        cpu = await prometheus.get_current_cpu()
        memory = await prometheus.get_current_memory()
        
        context = f"""
Текущие метрики сервера:
- CPU: {cpu:.2f}% (порог: {settings.cpu_threshold}%)
- Memory: {memory['percent']:.2f}% (используется {memory['used_gb']:.2f} GB из {memory['total_gb']:.2f} GB)
"""
        
        system_prompt = """Ты - помощник по мониторингу серверной инфраструктуры.
У тебя есть доступ к метрикам сервера. Отвечай кратко, понятно, на русском языке.
Если видишь проблемы - указывай их."""
        
        question = "Какая нагрузка на сервере?"
        full_prompt = f"{context}\n\nВопрос: {question}"
        
        print("  [~] Отправка запроса в Ollama (может занять 30-60 сек)...")
        
        response = await ollama.generate(
            prompt=full_prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=512
        )
        
        print(f"\n  Ответ LLM:")
        print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")
        print("\n  [OK] LLM анализ работает корректно")
        
        await prometheus.close()
        await ollama.close()
        return True
        
    except Exception as e:
        print(f"\n  [FAIL] Ошибка: {e}")
        await prometheus.close()
        await ollama.close()
        return False


async def main():
    """Главная функция тестирования"""
    print("\n" + "="*70)
    print("АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИНТЕРАКТИВНОГО ЧАТА")
    print("="*70)
    
    print(f"\nКонфигурация:")
    print(f"  Prometheus: {settings.prometheus_url}")
    print(f"  Loki: {settings.loki_url}")
    print(f"  Ollama: {settings.ollama_host}")
    print(f"  Модель: {settings.ollama_model}")
    
    results = []
    
    # Тест 1: Инициализация
    success, *_ = await test_initialization()
    results.append(("Инициализация компонентов", success))
    
    if not success:
        print("\n" + "="*70)
        print("[FAIL] Некоторые компоненты недоступны. Проверьте:")
        print("  - Ollama запущен: ollama list")
        print("  - Сервер доступен: http://147.45.157.2:9090")
        print("="*70)
        return 1
    
    # Тест 2-5: Быстрые команды
    results.append(("Команда /cpu", await test_quick_command_cpu()))
    results.append(("Команда /memory", await test_quick_command_memory()))
    results.append(("Команда /logs", await test_quick_command_logs()))
    results.append(("Команда /status", await test_full_status()))
    
    # Тест 6: LLM вопрос
    results.append(("LLM анализ", await test_llm_question()))
    
    # Итоги
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("="*70)
    
    for name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"  {name:30} {status}")
    
    all_ok = all(success for _, success in results)
    
    print("\n" + "="*70)
    if all_ok:
        print("[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\nИнтерактивный чат готов к использованию:")
        print("  python chat_with_ollama.py")
    else:
        print("[FAIL] НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("Проверьте логи выше для деталей.")
    print("="*70 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[!] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

