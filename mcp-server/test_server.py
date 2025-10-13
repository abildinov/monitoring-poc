"""
Локальное тестирование MCP tools без Claude Desktop
Прямой вызов функций для проверки работоспособности
"""

import asyncio
import sys
from loguru import logger

# Импорт всех необходимых компонентов
from clients.prometheus_client import PrometheusClient
from clients.loki_client import LokiClient
from llm.ollama_client import OllamaClient
from config import settings

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


async def test_tool_cpu():
    """Тест tool: get_cpu_usage"""
    
    print("\n" + "="*70)
    print("TEST 1: GET_CPU_USAGE")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    ollama = OllamaClient(settings.ollama_host, settings.ollama_model, settings.ollama_timeout)
    
    try:
        # Получаем CPU
        cpu = await prometheus.get_current_cpu()
        
        if cpu is None:
            print("[-] Ошибка: не удалось получить CPU метрики")
            return False
        
        print(f"[+] CPU получен: {cpu:.2f}%")
        
        # Анализ через LLM
        print(f"[~] Отправка на анализ в Ollama (может занять ~30 сек)...")
        
        analysis = await ollama.analyze_metrics(
            {
                "cpu_percent": cpu,
                "threshold": settings.cpu_threshold,
                "status": "high" if cpu > settings.cpu_threshold else "normal"
            },
            context="Анализ текущей нагрузки CPU"
        )
        
        print(f"\n[+] Анализ получен ({len(analysis)} символов)")
        print(f"\nРезультат:")
        print("-" * 70)
        print(f"CPU Usage: {cpu:.2f}%")
        print(f"Threshold: {settings.cpu_threshold}%")
        print(f"Status: {'HIGH' if cpu > settings.cpu_threshold else 'NORMAL'}")
        print(f"\nАнализ LLM:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    finally:
        await prometheus.close()
        await ollama.close()


async def test_tool_memory():
    """Тест tool: get_memory_status"""
    
    print("\n" + "="*70)
    print("TEST 2: GET_MEMORY_STATUS")
    print("="*70)
    
    prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    ollama = OllamaClient(settings.ollama_host, settings.ollama_model, settings.ollama_timeout)
    
    try:
        # Получаем Memory
        memory = await prometheus.get_current_memory()
        
        if memory is None:
            print("[-] Ошибка: не удалось получить Memory метрики")
            return False
        
        print(f"[+] Memory получен: {memory['percent']:.2f}%")
        print(f"  Total: {memory['total_gb']:.2f} GB")
        print(f"  Used: {memory['used_gb']:.2f} GB")
        print(f"  Available: {memory['available_gb']:.2f} GB")
        
        # Анализ через LLM
        print(f"[~] Отправка на анализ в Ollama...")
        
        analysis = await ollama.analyze_metrics(
            memory,
            context="Анализ использования памяти"
        )
        
        print(f"\n[+] Анализ получен ({len(analysis)} символов)")
        print(f"\nРезультат:")
        print("-" * 70)
        print(f"Memory Status:")
        print(f"- Total: {memory['total_gb']:.2f} GB")
        print(f"- Used: {memory['used_gb']:.2f} GB")
        print(f"- Available: {memory['available_gb']:.2f} GB")
        print(f"- Usage: {memory['percent']:.2f}%")
        print(f"- Threshold: {settings.memory_threshold}%")
        print(f"- Status: {'HIGH' if memory['percent'] > settings.memory_threshold else 'NORMAL'}")
        print(f"\nАнализ LLM:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    finally:
        await prometheus.close()
        await ollama.close()


async def test_tool_logs():
    """Тест tool: search_error_logs"""
    
    print("\n" + "="*70)
    print("TEST 3: SEARCH_ERROR_LOGS")
    print("="*70)
    
    loki = LokiClient(settings.loki_url, settings.http_timeout)
    ollama = OllamaClient(settings.ollama_host, settings.ollama_model, settings.ollama_timeout)
    
    try:
        # Получаем ошибки
        hours = 24
        print(f"[~] Поиск ошибок за последние {hours} часов...")
        
        errors = await loki.get_error_logs(hours=hours, limit=20)
        
        if not errors:
            print(f"[+] Ошибок за последние {hours}ч не найдено")
            return True
        
        print(f"[+] Найдено ошибок: {len(errors)}")
        
        # Показываем несколько примеров
        print(f"\nПримеры ошибок:")
        for i, err in enumerate(errors[:3], 1):
            print(f"\n{i}. [{err['timestamp']}] {err['container']}")
            print(f"   {err['message'][:100]}...")
        
        # Анализ через LLM
        print(f"\n[~] Отправка на анализ в Ollama...")
        
        log_messages = [e['message'] for e in errors[:10]]
        
        analysis = await ollama.analyze_logs(
            log_messages,
            context=f"Анализ ошибок за последние {hours}ч"
        )
        
        print(f"\n[+] Анализ получен ({len(analysis)} символов)")
        print(f"\nРезультат:")
        print("-" * 70)
        print(f"Найдено ошибок: {len(errors)}")
        print(f"Период: последние {hours} час(ов)")
        print(f"\nАнализ LLM:")
        print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return False
    
    finally:
        await loki.close()
        await ollama.close()


async def main():
    """Главная функция тестирования"""
    
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ MCP TOOLS")
    print("="*70)
    print(f"\nКонфигурация:")
    print(f"  Prometheus: {settings.prometheus_url}")
    print(f"  Loki: {settings.loki_url}")
    print(f"  Ollama: {settings.ollama_host}")
    print(f"  Модель: {settings.ollama_model}")
    print(f"\nЗапуск тестов...\n")
    
    results = []
    
    # Тест 1: CPU
    result_cpu = await test_tool_cpu()
    results.append(("get_cpu_usage", result_cpu))
    
    # Небольшая пауза между тестами
    await asyncio.sleep(2)
    
    # Тест 2: Memory
    result_memory = await test_tool_memory()
    results.append(("get_memory_status", result_memory))
    
    await asyncio.sleep(2)
    
    # Тест 3: Logs
    result_logs = await test_tool_logs()
    results.append(("search_error_logs", result_logs))
    
    # Итоги
    print("\n" + "="*70)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*70)
    
    all_ok = True
    for tool_name, success in results:
        status = "[OK]" if success else "[FAIL]"
        print(f"{tool_name:25} {status}")
        if not success:
            all_ok = False
    
    print("="*70)
    
    if all_ok:
        print("\n[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("MCP сервер готов к работе с Claude Desktop.")
    else:
        print("\n[FAIL] НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("Проверьте логи и доступность сервисов.")
    
    print("\n" + "="*70 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[-] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

