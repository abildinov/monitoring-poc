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

# HTTP API для Telegram бота
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

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

# HTTP API для Telegram бота
http_app = FastAPI(title="MCP Monitoring API", version="1.0.0")

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
        Tool(
            name="get_network_status",
            description="Получить статус сети: трафик, соединения, ошибки. "
                       "Возвращает данные о сетевых интерфейсах и их состоянии.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_top_processes",
            description="Получить топ процессов по CPU и памяти. "
                       "Возвращает список процессов с наибольшим потреблением ресурсов.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Количество процессов для отображения (по умолчанию 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_active_alerts",
            description="Получить активные алерты системы. "
                       "Возвращает список текущих проблем и предупреждений.",
            inputSchema={
                "type": "object",
                "properties": {},
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
        
        elif name == "get_network_status":
            return await tool_get_network_status()
        
        elif name == "get_top_processes":
            limit = arguments.get("limit", 10)
            return await tool_get_top_processes(limit)
        
        elif name == "get_active_alerts":
            return await tool_get_active_alerts()
        
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


async def tool_get_network_status() -> list[TextContent]:
    """Tool: Получение статуса сети"""
    
    logger.info("Выполнение get_network_status")
    
    try:
        # Получаем данные из Prometheus
        network_data = await prometheus_client.get_network_status()
        
        # Форматируем результат
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
        
        logger.info("get_network_status выполнен успешно")
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.exception(f"Ошибка в get_network_status: {e}")
        return [TextContent(type="text", text=f"Ошибка получения статуса сети: {e}")]


async def tool_get_top_processes(limit: int = 10) -> list[TextContent]:
    """Tool: Получение топ процессов"""
    
    logger.info(f"Выполнение get_top_processes (limit={limit})")
    
    try:
        # Получаем данные из Prometheus
        cpu_processes = await prometheus_client.get_top_processes_by_cpu(limit)
        memory_processes = await prometheus_client.get_top_processes_by_memory(limit)
        
        # Форматируем результат
        result = f"Top Processes (limit={limit}):\n\n"
        
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
        
        logger.info("get_top_processes выполнен успешно")
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.exception(f"Ошибка в get_top_processes: {e}")
        return [TextContent(type="text", text=f"Ошибка получения топ процессов: {e}")]


async def tool_get_active_alerts() -> list[TextContent]:
    """Tool: Получение активных алертов"""
    
    logger.info("Выполнение get_active_alerts")
    
    try:
        # Инициализируем AlertManager если еще не инициализирован
        if not hasattr(tool_get_active_alerts, 'alert_manager'):
            from alerts.alert_manager import AlertManager
            tool_get_active_alerts.alert_manager = AlertManager()
        
        alert_manager = tool_get_active_alerts.alert_manager
        
        # Получаем активные алерты
        active_alerts = alert_manager.get_active_alerts()
        
        # Форматируем результат
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
        stats = alert_manager.get_stats()
        result += f"Statistics:\n"
        result += f"  Active alerts: {stats['active_alerts']}\n"
        result += f"  Total history: {stats['total_history']}\n"
        result += f"  Rules count: {stats['rules_count']}\n"
        
        if stats['severity_breakdown']:
            result += f"  Severity breakdown:\n"
            for severity, count in stats['severity_breakdown'].items():
                result += f"    {severity}: {count}\n"
        
        logger.info("get_active_alerts выполнен успешно")
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.exception(f"Ошибка в get_active_alerts: {e}")
        return [TextContent(type="text", text=f"Ошибка получения алертов: {e}")]


# ============================================================================
# HTTP API ENDPOINTS
# ============================================================================

@http_app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "MCP Monitoring API", "version": "1.0.0"}

@http_app.get("/tools")
async def list_tools():
    """Список доступных tools"""
    tools = [
        {"name": "get_cpu_usage", "description": "Получение загрузки CPU"},
        {"name": "get_memory_status", "description": "Получение статуса памяти"},
        {"name": "search_error_logs", "description": "Поиск ошибок в логах"},
        {"name": "get_network_status", "description": "Получение сетевой статистики"},
        {"name": "get_top_processes", "description": "Получение топ процессов"},
        {"name": "get_active_alerts", "description": "Получение активных алертов"}
    ]
    return {"tools": tools}

@http_app.post("/call_tool")
async def call_tool(request: dict):
    """Вызов MCP tool через HTTP"""
    try:
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        # Маппинг tool names на функции
        tool_mapping = {
            "get_cpu_usage": tool_get_cpu_usage,
            "get_memory_status": tool_get_memory_status,
            "search_error_logs": tool_search_error_logs,
            "get_network_status": tool_get_network_status,
            "get_top_processes": tool_get_top_processes,
            "get_active_alerts": tool_get_active_alerts
        }
        
        if tool_name not in tool_mapping:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Вызываем tool
        tool_func = tool_mapping[tool_name]
        result = await tool_func(**arguments)
        
        # Возвращаем результат в формате MCP
        return {"content": [{"type": "text", "text": result[0].text}]}
        
    except Exception as e:
        logger.exception(f"Ошибка при вызове tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@http_app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "healthy", "clients_initialized": bool(prometheus_client and loki_client and ollama_client)}


# ============================================================================
# MAIN
# ============================================================================

async def main(transport: str = "stdio"):
    """Главная функция с выбором транспорта"""
    logger.info(f"Запуск MCP сервера с транспортом {transport}...")
    
    # Инициализация клиентов
    await init_clients()
    
    try:
        if transport == "stdio":
            # Режим Claude Desktop
            async with stdio_server() as (read_stream, write_stream):
                logger.info("MCP сервер готов (stdio)")
                await app.run(read_stream, write_stream, app.create_initialization_options())
        
        elif transport == "http":
            # HTTP режим для Telegram бота
            logger.info("MCP сервер готов (HTTP) на http://localhost:3000")
            config = uvicorn.Config(http_app, host="localhost", port=3000, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
        
        elif transport == "sse":
            # HTTP/SSE режим для Telegram бота (fallback на HTTP)
            logger.warning("SSE transport не поддерживается. Используется HTTP режим.")
            logger.info("MCP сервер готов (HTTP) на http://localhost:3000")
            config = uvicorn.Config(http_app, host="localhost", port=3000, log_level="info")
            server = uvicorn.Server(config)
            await server.serve()
    
    finally:
        # Очистка при завершении
        await cleanup_clients()
        logger.info("MCP сервер остановлен")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server для мониторинга")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default="stdio",
                       help="Тип транспорта (stdio для Claude Desktop, http/sse для HTTP API)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.transport))
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания")
    except Exception as e:
        logger.exception("Критическая ошибка")
        sys.exit(1)

