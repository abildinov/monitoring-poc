"""
MCP Server для мониторинга серверной инфраструктуры
Предоставляет tools для работы с Prometheus, Loki и анализа через Ollama
"""

import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from clients.prometheus_client import PrometheusClient
from clients.loki_client import LokiClient
from llm.ollama_client import OllamaClient
from config import settings
from loguru import logger

# Настройка логирования
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Инициализация глобальных клиентов
prometheus_client: PrometheusClient = None
loki_client: LokiClient = None
ollama_client: OllamaClient = None

# Создание MCP сервера
app = Server(settings.mcp_server_name)

logger.info(f"Инициализация {settings.mcp_server_name} v{settings.mcp_server_version}")


async def init_clients():
    """Инициализация клиентов при старте сервера"""
    global prometheus_client, loki_client, ollama_client
    
    logger.info("Инициализация клиентов...")
    
    prometheus_client = PrometheusClient(settings.prometheus_url, settings.http_timeout)
    loki_client = LokiClient(settings.loki_url, settings.http_timeout)
    ollama_client = OllamaClient(
        settings.ollama_host,
        settings.ollama_model,
        settings.ollama_timeout
    )
    
    # Проверка доступности
    prom_ok = await prometheus_client.check_health()
    loki_ok = await loki_client.check_health()
    ollama_ok = await ollama_client.check_health()
    
    logger.info(f"Статус клиентов - Prometheus: {prom_ok}, Loki: {loki_ok}, Ollama: {ollama_ok}")
    
    if not all([prom_ok, loki_ok, ollama_ok]):
        logger.warning("Некоторые клиенты недоступны, но сервер продолжит работу")


async def cleanup_clients():
    """Очистка ресурсов при завершении"""
    global prometheus_client, loki_client, ollama_client
    
    logger.info("Закрытие клиентов...")
    
    if prometheus_client:
        await prometheus_client.close()
    if loki_client:
        await loki_client.close()
    if ollama_client:
        await ollama_client.close()


# ============================================================================
# MCP TOOLS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Список доступных tools
    """
    return [
        Tool(
            name="get_cpu_usage",
            description="Получить текущую загрузку CPU сервера в процентах. "
                       "Возвращает значение CPU usage и анализ от LLM.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_memory_status",
            description="Получить текущее состояние памяти сервера (RAM). "
                       "Возвращает total, used, available память и процент использования с анализом.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_error_logs",
            description="Найти ошибки в логах за указанный период времени. "
                       "Возвращает список ошибок с анализом от LLM.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "number",
                        "description": "Сколько часов назад искать (по умолчанию 1)",
                        "default": 1
                    }
                },
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Обработка вызовов tools
    """
    logger.info(f"Вызов tool: {name} с аргументами: {arguments}")
    
    try:
        if name == "get_cpu_usage":
            return await tool_get_cpu_usage()
        
        elif name == "get_memory_status":
            return await tool_get_memory_status()
        
        elif name == "search_error_logs":
            hours = arguments.get("hours", 1)
            return await tool_search_error_logs(hours)
        
        else:
            logger.error(f"Неизвестный tool: {name}")
            return [TextContent(
                type="text",
                text=f"Ошибка: tool '{name}' не найден"
            )]
    
    except Exception as e:
        logger.exception(f"Ошибка при выполнении tool {name}")
        return [TextContent(
            type="text",
            text=f"Ошибка при выполнении {name}: {str(e)}"
        )]


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_get_cpu_usage() -> list[TextContent]:
    """Tool: Получение загрузки CPU"""
    
    logger.info("Выполнение get_cpu_usage")
    
    # Получаем данные из Prometheus
    cpu = await prometheus_client.get_current_cpu()
    
    if cpu is None:
        return [TextContent(
            type="text",
            text="Ошибка: не удалось получить метрики CPU из Prometheus"
        )]
    
    # Анализ через LLM
    logger.info(f"CPU: {cpu:.2f}%, отправка на анализ в Ollama...")
    
    analysis = await ollama_client.analyze_metrics(
        {
            "cpu_percent": cpu,
            "threshold": settings.cpu_threshold,
            "status": "high" if cpu > settings.cpu_threshold else "normal"
        },
        context="Анализ текущей нагрузки CPU на сервере мониторинга"
    )
    
    # Форматирование результата
    result = f"""CPU Usage: {cpu:.2f}%
Threshold: {settings.cpu_threshold}%
Status: {'⚠️ HIGH' if cpu > settings.cpu_threshold else '✓ NORMAL'}

Анализ LLM:
{analysis}
"""
    
    logger.info("get_cpu_usage выполнен успешно")
    
    return [TextContent(type="text", text=result)]


async def tool_get_memory_status() -> list[TextContent]:
    """Tool: Получение состояния памяти"""
    
    logger.info("Выполнение get_memory_status")
    
    # Получаем данные из Prometheus
    memory = await prometheus_client.get_current_memory()
    
    if memory is None:
        return [TextContent(
            type="text",
            text="Ошибка: не удалось получить метрики памяти из Prometheus"
        )]
    
    # Анализ через LLM
    logger.info(f"Memory: {memory['percent']:.2f}%, отправка на анализ...")
    
    analysis = await ollama_client.analyze_metrics(
        memory,
        context="Анализ использования оперативной памяти на сервере"
    )
    
    # Форматирование результата
    result = f"""Memory Status:
- Total: {memory['total_gb']:.2f} GB
- Used: {memory['used_gb']:.2f} GB
- Available: {memory['available_gb']:.2f} GB
- Usage: {memory['percent']:.2f}%
- Threshold: {settings.memory_threshold}%
- Status: {'⚠️ HIGH' if memory['percent'] > settings.memory_threshold else '✓ NORMAL'}

Анализ LLM:
{analysis}
"""
    
    logger.info("get_memory_status выполнен успешно")
    
    return [TextContent(type="text", text=result)]


async def tool_search_error_logs(hours: int = 1) -> list[TextContent]:
    """Tool: Поиск ошибок в логах"""
    
    logger.info(f"Выполнение search_error_logs за последние {hours}ч")
    
    # Получаем ошибки из Loki
    errors = await loki_client.get_error_logs(hours=hours, limit=20)
    
    if not errors:
        return [TextContent(
            type="text",
            text=f"Ошибок за последние {hours}ч не найдено ✓"
        )]
    
    # Анализ через LLM
    logger.info(f"Найдено {len(errors)} ошибок, отправка на анализ...")
    
    log_messages = [e['message'] for e in errors[:10]]
    
    analysis = await ollama_client.analyze_logs(
        log_messages,
        context=f"Анализ ошибок в логах за последние {hours}ч"
    )
    
    # Форматирование результата
    result = f"""Найдено ошибок: {len(errors)}
Период: последние {hours} час(ов)

Последние 5 ошибок:
"""
    
    for i, err in enumerate(errors[:5], 1):
        result += f"\n{i}. [{err['timestamp']}] {err['container']}\n"
        result += f"   {err['message'][:150]}...\n"
    
    result += f"\nАнализ LLM:\n{analysis}\n"
    
    logger.info("search_error_logs выполнен успешно")
    
    return [TextContent(type="text", text=result)]


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Главная функция запуска сервера"""
    
    logger.info("Запуск MCP сервера...")
    
    # Инициализация клиентов
    await init_clients()
    
    try:
        # Запуск сервера через stdio
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP сервер запущен и готов к работе")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    finally:
        # Очистка при завершении
        await cleanup_clients()
        logger.info("MCP сервер остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.exception("Критическая ошибка")
        sys.exit(1)

