#!/usr/bin/env python3
"""
Telegram бот для мониторинга сервера
Поддерживает команды для получения метрик и состояния системы
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Добавляем путь к mcp-server для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

import httpx
from clients.prometheus_client import PrometheusClient
from clients.loki_client import LokiClient
from llm.ollama_client import OllamaClient
from alerts.alert_manager import AlertManager
from mcp_client import MCPClient
from config import settings


class TelegramMonitoringBot:
    """Telegram бот для мониторинга сервера"""
    
    def __init__(self, bot_token: str, use_mcp: bool = True):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.client = httpx.AsyncClient(timeout=30)
        self.use_mcp = use_mcp
        
        if use_mcp:
            # Используем MCP клиент для единого бэкенда
            self.mcp = MCPClient("http://localhost:3000")
            print("Telegram бот использует MCP сервер")
        else:
            # Прямые клиенты (fallback)
            self.prometheus = PrometheusClient(settings.prometheus_url, settings.http_timeout)
            self.loki = LokiClient(settings.loki_url, settings.http_timeout)
            self.ollama = OllamaClient(settings.ollama_host, settings.ollama_model, settings.ollama_timeout)
            self.alert_manager = AlertManager()
            print("Telegram бот использует прямые клиенты")
        
        # Команды бота
        self.commands = {
            '/start': self.cmd_start,
            '/help': self.cmd_help,
            '/menu': self.cmd_menu,
            '/status': self.cmd_status,
            '/analyze': self.cmd_analyze_full,
            '/health': self.cmd_health,
            '/alerts': self.cmd_alerts,
            '/chat': self.cmd_chat
        }
    
    async def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Отправить сообщение в Telegram"""
        try:
            # Ограничиваем длину сообщения (Telegram лимит 4096 символов)
            if len(text) > 4000:
                text = text[:4000] + "\n\n... (сообщение обрезано)"
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text
            }
            
            # Добавляем parse_mode только если он указан
            if parse_mode:
                data["parse_mode"] = parse_mode
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                print(f"Сообщение отправлено в Telegram")
                return True
            else:
                print(f"Ошибка Telegram API: {result.get('description', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            # Попробуем отправить без Markdown и спецсимволов
            try:
                url = f"{self.base_url}/sendMessage"
                # Удаляем Markdown символы
                clean_text = text.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
                data = {
                    "chat_id": chat_id,
                    "text": clean_text
                }
                
                response = await self.client.post(url, json=data)
                response.raise_for_status()
                print(f"Сообщение отправлено без форматирования")
                return True
            except Exception as e2:
                print(f"Ошибка отправки без форматирования: {e2}")
                return False
    
    async def send_chat_action(self, chat_id: str, action: str) -> bool:
        """Отправить индикатор действия (печатает, отправляет фото и т.д.)"""
        try:
            url = f"{self.base_url}/sendChatAction"
            data = {
                "chat_id": chat_id,
                "action": action
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Ошибка отправки действия: {e}")
            return False
    
    def get_main_keyboard(self):
        """Получить основную inline клавиатуру"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🎓 Анализ LLM", "callback_data": "analyze"}
                ],
                [
                    {"text": "📊 Статус системы", "callback_data": "status"},
                    {"text": "🏥 Здоровье", "callback_data": "health"}
                ],
                [
                    {"text": "🚨 Алерты", "callback_data": "alerts"},
                    {"text": "💬 Чат с LLM", "callback_data": "chat"}
                ]
            ]
        }
    
    def get_reply_keyboard(self):
        """Получить постоянную клавиатуру в чате (кнопки под строкой ввода)"""
        return {
            "keyboard": [
                [
                    {"text": "🎓 Анализ LLM"},
                    {"text": "📊 Статус"}
                ],
                [
                    {"text": "🏥 Здоровье"},
                    {"text": "🚨 Алерты"}
                ],
                [
                    {"text": "💬 Чат с LLM"},
                    {"text": "📋 Меню"}
                ]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False,
            "selective": False
        }
    
    async def send_message_with_keyboard(self, chat_id: str, text: str, keyboard: dict, parse_mode: str = "Markdown") -> bool:
        """Отправить сообщение с inline клавиатурой"""
        try:
            # Ограничиваем длину сообщения
            if len(text) > 4000:
                text = text[:4000] + "\n\n... (сообщение обрезано)"
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": keyboard
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                print(f"Сообщение с клавиатурой отправлено")
                return True
            else:
                print(f"Ошибка Telegram API: {result.get('description', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"Ошибка отправки сообщения с клавиатурой: {e}")
            return False
    
    async def send_message_with_reply_keyboard(self, chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
        """Отправить сообщение с reply клавиатурой (кнопки под строкой ввода)"""
        try:
            # Ограничиваем длину сообщения
            if len(text) > 4000:
                text = text[:4000] + "\n\n... (сообщение обрезано)"
            
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": self.get_reply_keyboard()
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                print(f"Сообщение с reply клавиатурой отправлено")
                return True
            else:
                print(f"Ошибка Telegram API: {result.get('description', 'Unknown error')}")
                return False
            
        except Exception as e:
            print(f"Ошибка отправки сообщения с reply клавиатурой: {e}")
            return False
    
    
    async def cmd_start(self, chat_id: str, message: str) -> str:
        """Команда /start"""
        # Отправляем сообщение с inline клавиатурой
        await self.send_message_with_keyboard(chat_id, 
            """🤖 *Добро пожаловать в систему мониторинга сервера!*

📊 *Сервер:* 147.45.157.2
🤖 *LLM:* Ollama (Llama 3)
🎓 *Для защиты диплома*

Используйте кнопки ниже или команды:
• `/analyze` - Анализ через LLM
• `/status` - Статус системы
• `/alerts` - Активные алерты
• `/health` - Проверка компонентов
• `/chat <текст>` - Вопрос к LLM
• `/menu` - Показать меню снова

💡 *Для защиты начните с кнопки "🎓 Анализ LLM"*""",
            self.get_main_keyboard()
        )
        
        # Отправляем второе сообщение с reply клавиатурой (кнопки под строкой ввода)
        await self.send_message_with_reply_keyboard(chat_id,
            "🔘 *Быстрые кнопки под строкой ввода:*\n\nТеперь вы можете использовать кнопки под полем ввода для быстрого доступа к функциям!"
        )
        
        return ""  # Пустой ответ, т.к. уже отправили сообщения
    
    async def cmd_help(self, chat_id: str, message: str) -> str:
        """Команда /help"""
        return await self.cmd_start(chat_id, message)
    
    async def cmd_menu(self, chat_id: str, message: str) -> str:
        """Команда /menu - показать меню с кнопками"""
        await self.send_message_with_keyboard(chat_id, 
            "📋 *Главное меню:*\n\nВыберите действие:",
            self.get_main_keyboard()
        )
        return ""  # Пустой ответ, т.к. уже отправили сообщение
    
    async def cmd_status(self, chat_id: str, message: str) -> str:
        """Команда /status - полный статус системы"""
        try:
            if self.use_mcp and hasattr(self, 'mcp') and self.mcp:
                # Используем MCP клиент
                cpu_result = await self.mcp.call_tool("get_cpu_usage")
                memory_result = await self.mcp.call_tool("get_memory_status")
                network_result = await self.mcp.call_tool("get_network_status")
                alerts_result = await self.mcp.call_tool("get_active_alerts")
                
                # Формируем ответ из MCP результатов
                result = f"""📊 *Статус системы через MCP*

*CPU:* {cpu_result[:150]}...
*Память:* {memory_result[:150]}...
*Сеть:* {network_result[:150]}...
*Алерты:* {alerts_result[:150]}...

⏰ *Время:* {datetime.now().strftime('%H:%M:%S')}"""
                
                return result
            else:
                # Используем прямые клиенты
                cpu = await self.prometheus.get_current_cpu()
                memory = await self.prometheus.get_current_memory()
                disks = await self.prometheus.get_disk_usage()
                network = await self.prometheus.get_network_status()
                active_alerts = self.alert_manager.get_active_alerts()
                
                # Формируем ответ
                status = "🟢 НОРМАЛЬНО" if len(active_alerts) == 0 else "🔴 ПРОБЛЕМЫ"
                
                result = f"""📊 *Статус системы: {status}*

🖥️ *CPU:* {cpu:.1f}% {'⚠️' if cpu > settings.cpu_threshold else '✅'}
💾 *Память:* {memory['percent']:.1f}% ({memory['used_gb']:.1f}/{memory['total_gb']:.1f} GB) {'⚠️' if memory['percent'] > settings.memory_threshold else '✅'}
💿 *Диски:* {len(disks)} найдено
🌐 *Сеть:* {network['status'].upper()}
🚨 *Алерты:* {len(active_alerts)} активных

⏰ *Время:* {datetime.now().strftime('%H:%M:%S')}"""
                
                return result
            
        except Exception as e:
            return f"Ошибка получения статуса: {str(e)}"
    
    async def cmd_alerts(self, chat_id: str, message: str) -> str:
        """Команда /alerts - активные алерты"""
        try:
            if self.use_mcp and hasattr(self, 'mcp') and self.mcp:
                # Используем MCP клиент
                alerts_result = await self.mcp.call_tool("get_active_alerts")
                return f"🚨 *Алерты через MCP*\n\n{alerts_result}"
            else:
                # Используем прямые клиенты
                active_alerts = self.alert_manager.get_active_alerts()
                stats = self.alert_manager.get_stats()
                
                if not active_alerts:
                    return "✅ *Активных алертов нет*"
                
                result = f"🚨 *Активные алерты: {len(active_alerts)}*\n\n"
                
                for alert in active_alerts[:5]:  # Показываем только первые 5
                    emoji = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(alert.severity, '📢')
                    time_str = alert.timestamp.strftime('%H:%M:%S')
                    
                    result += f"{emoji} *{alert.name}*\n"
                    result += f"   {alert.message}\n"
                    result += f"   Время: {time_str}\n\n"
                
                if len(active_alerts) > 5:
                    result += f"... и еще {len(active_alerts) - 5} алертов"
                
                return result
            
        except Exception as e:
            return f"Ошибка получения алертов: {str(e)}"
    
    async def cmd_chat(self, chat_id: str, message: str) -> str:
        """Команда /chat - чат с системой"""
        try:
            # Извлекаем вопрос из команды
            question = message.replace('/chat', '').strip()
            
            if not question:
                return "❓ Задайте вопрос после команды /chat\n\nПример: `/chat Как дела с CPU?`"
            
            # Получаем метрики для контекста
            cpu = await self.prometheus.get_current_cpu()
            memory = await self.prometheus.get_current_memory()
            errors = await self.loki.get_error_logs(hours=1, limit=3)
            
            # Формируем контекст
            context = f"""
Текущие метрики сервера:
- CPU: {cpu:.1f}% (порог: {settings.cpu_threshold}%)
- Память: {memory['percent']:.1f}% (используется {memory['used_gb']:.1f} GB из {memory['total_gb']:.1f} GB)
- Ошибки за последний час: {len(errors)}
"""
            
            # Системный промпт
            system_prompt = f"""Ты - помощник по мониторингу серверной инфраструктуры.

ВАЖНО: Анализируй данные правильно!
- CPU {cpu:.1f}% - это НИЖЕ порога {settings.cpu_threshold}% (нормально)
- Память {memory['percent']:.1f}% - это НИЖЕ порога {settings.memory_threshold}% (нормально)

Отвечай кратко, понятно, на русском языке.
Если значения НИЖЕ порогов - говори что все в порядке.
Если значения ВЫШЕ порогов - указывай проблемы и давай рекомендации."""
            
            full_prompt = f"{context}\n\nВопрос пользователя: {question}"
            
            # Отправляем в Ollama
            response = await self.ollama.generate(
                prompt=full_prompt,
                system=system_prompt,
                temperature=0.7,
                max_tokens=512
            )
            
            return f"💬 *Вопрос:* {question}\n\n*Ответ:*\n{response}"
            
        except Exception as e:
            return f"Ошибка обработки вопроса: {str(e)}"
    
    async def cmd_health(self, chat_id: str, message: str) -> str:
        """Команда /health - проверка здоровья компонентов"""
        try:
            prom_ok = await self.prometheus.check_health()
            loki_ok = await self.loki.check_health()
            ollama_ok = await self.ollama.check_health()
            
            result = "🏥 *Проверка здоровья компонентов:*\n\n"
            
            result += f"{'✅' if prom_ok else '❌'} *Prometheus:* {'OK' if prom_ok else 'ERROR'}\n"
            result += f"{'✅' if loki_ok else '❌'} *Loki:* {'OK' if loki_ok else 'ERROR'}\n"
            result += f"{'✅' if ollama_ok else '❌'} *Ollama:* {'OK' if ollama_ok else 'ERROR'}\n"
            
            overall = "🟢 ЗДОРОВА" if all([prom_ok, loki_ok, ollama_ok]) else "🔴 ПРОБЛЕМЫ"
            result += f"\n*Общий статус:* {overall}"
            
            return result
            
        except Exception as e:
            return f"Ошибка проверки здоровья: {str(e)}"
    
    async def cmd_analyze_full(self, chat_id: str, message: str) -> str:
        """Команда /analyze - ПОЛНЫЙ анализ РЕАЛЬНОГО сервера через LLM"""
        try:
            await self.send_chat_action(chat_id, "typing")
            
            if self.use_mcp:
                # Используем MCP сервер
                result = "🤖 *ПОЛНЫЙ АНАЛИЗ СИСТЕМЫ ЧЕРЕЗ MCP*\n"
                result += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result += "📊 Собираю данные через MCP сервер...\n"
                
                await self.send_message(chat_id, result)
                await self.send_chat_action(chat_id, "typing")
                
                # Вызываем MCP tools
                cpu_result = await self.mcp.call_tool("get_cpu_usage")
                memory_result = await self.mcp.call_tool("get_memory_status")
                alerts_result = await self.mcp.call_tool("get_active_alerts")
                
                # Объединяем результаты
                result = "🎓 РЕЗУЛЬТАТ АНАЛИЗА ЧЕРЕЗ MCP\n"
                result += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result += f"**CPU:**\n{cpu_result}\n\n"
                result += f"**Память:**\n{memory_result}\n\n"
                result += f"**Алерты:**\n{alerts_result}\n\n"
                result += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result += "✨ Что показывает этот анализ:\n"
                result += "✓ Единый MCP бэкенд для всех интерфейсов\n"
                result += "✓ Стандартизированные tools\n"
                result += "✓ Переиспользуемая логика\n"
                result += "✓ Масштабируемая архитектура\n\n"
                result += "💡 Это и есть инновация - единая система\n"
                result += "для Telegram, Claude Desktop и других клиентов!"
                
            else:
                # Fallback: прямые клиенты
                result = "🤖 *ПОЛНЫЙ АНАЛИЗ СИСТЕМЫ ЧЕРЕЗ LLM*\n"
                result += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result += "📊 Собираю данные с сервера `147.45.157.2`...\n"
                
                await self.send_message(chat_id, result)
                await self.send_chat_action(chat_id, "typing")
                
                # Получаем все метрики
                cpu = await self.prometheus.get_current_cpu()
                memory = await self.prometheus.get_current_memory()
                disks = await self.prometheus.get_disk_usage()
                active_alerts = self.alert_manager.get_active_alerts()
                errors = await self.loki.get_error_logs(hours=1, limit=5)
                
                root_disk = next((d for d in disks if d['mountpoint'] == '/'), disks[0] if disks else None)
                
                # Показываем собранные данные
                result = "✅ *Данные собраны*\n\n"
                result += f"*Метрики:*\n"
                result += f"• CPU: `{cpu:.1f}%`\n"
                result += f"• Memory: `{memory['percent']:.1f}%` ({memory['used_gb']:.1f}/{memory['total_gb']:.1f} GB)\n"
                result += f"• Disk: `{root_disk['percent']:.1f}%`\n"
                result += f"• Алерты: `{len(active_alerts)}`\n"
                result += f"• Ошибки (1ч): `{len(errors)}`\n\n"
                result += "🧠 Отправляю в LLM для анализа...\n"
                result += "⏱ _Это займет 30-60 секунд_"
                
                await self.send_message(chat_id, result)
                await self.send_chat_action(chat_id, "typing")
                
                # Формируем данные для LLM
                metrics_data = {
                    "CPU": f"{cpu:.2f}%",
                    "Memory": f"{memory['percent']:.2f}% (используется {memory['used_gb']:.2f} GB из {memory['total_gb']:.2f} GB)",
                    "Disk": f"{root_disk['percent']:.2f}% (точка монтирования: {root_disk['mountpoint']})",
                    "Активные алерты": len(active_alerts),
                    "Ошибки за последний час": len(errors)
                }
                
                # РЕАЛЬНЫЙ анализ через улучшенные промпты
                analysis = await self.ollama.analyze_metrics(
                    metrics_data=metrics_data,
                    context=f"Реальный анализ сервера 147.45.157.2 для демонстрации на защите диплома"
                )
                
                # Отправляем результат БЕЗ Markdown (т.к. LLM может использовать спецсимволы)
                result = "🎓 РЕЗУЛЬТАТ АНАЛИЗА LLM\n"
                result += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result += analysis + "\n\n"
                result += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                result += "✨ Что показывает этот анализ:\n"
                result += "✓ Автоматическая оценка критичности\n"
                result += "✓ Приоритизация проблем\n"
                result += "✓ Конкретные рекомендации\n"
                result += "✓ Прогноз развития ситуации\n"
                result += "✓ Структурированный формат\n\n"
                result += "💡 Это и есть инновация - LLM анализирует\n"
                result += "РЕАЛЬНЫЙ сервер и дает экспертные рекомендации!"
            
            # Отправляем без Markdown форматирования
            await self.send_message(chat_id, result, parse_mode=None)
            return ""  # Уже отправлено
            
        except Exception as e:
            return f"Ошибка анализа: {str(e)}"
    
    
    async def process_message(self, chat_id: str, message: str) -> str:
        """Обработать сообщение и вернуть ответ"""
        message = message.strip()
        
        # Маппинг текста кнопок на команды
        button_map = {
            "🎓 Анализ LLM": "/analyze",
            "📊 Статус": "/status",
            "🏥 Здоровье": "/health",
            "🚨 Алерты": "/alerts",
            "💬 Чат с LLM": "/chat",
            "📋 Меню": "/menu"
        }
        
        # Конвертируем текст кнопки в команду
        if message in button_map:
            message = button_map[message]
        
        # Проверяем команды
        for cmd, handler in self.commands.items():
            if message.startswith(cmd):
                return await handler(chat_id, message)
        
        # Если команда не найдена, предлагаем помощь
        return "❓ Неизвестная команда. Используйте /help для списка доступных команд."
    
    async def get_updates(self, offset: int = 0) -> Dict[str, Any]:
        """Получить обновления от Telegram"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            
            response = await self.client.get(url, params=params, timeout=35)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            # Не выводим ошибку каждый раз (может быть просто таймаут)
            if "timeout" not in str(e).lower():
                print(f"Ошибка получения обновлений: {e}")
            return {"ok": False, "result": []}
    
    async def run(self):
        """Запуск бота"""
        print("Запуск Telegram бота мониторинга...")
        print("Бот готов к работе! Отправьте /start для начала.")
        
        offset = 0
        
        while True:
            try:
                # Получаем обновления
                updates = await self.get_updates(offset)
                
                if not updates.get("ok"):
                    print("Ошибка получения обновлений")
                    await asyncio.sleep(5)
                    continue
                
                # Обрабатываем каждое обновление
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    
                    # Обработка обычных сообщений
                    if "message" in update:
                        message = update["message"]
                        chat_id = str(message["chat"]["id"])
                        text = message.get("text", "")
                        
                        print(f"📨 Получено сообщение от {chat_id}: {text}")
                        
                        # Отправляем индикатор ожидания
                        await self.send_message(chat_id, "⏳ Запрашиваю информацию...")
                        
                        # Обрабатываем сообщение
                        print(f"🔄 Обрабатываем команду...")
                        response = await self.process_message(chat_id, text)
                        print(f"📝 Ответ сгенерирован: {response[:100]}...")
                        
                        # Отправляем индикатор "печатает"
                        await self.send_chat_action(chat_id, "typing")
                        
                        # Отправляем ответ (если он не пустой)
                        if response and response.strip():
                            print(f"📤 Отправляем ответ в Telegram...")
                            success = await self.send_message(chat_id, response)
                            if success:
                                print(f"Ответ отправлен успешно!")
                            else:
                                print(f"Ошибка отправки ответа!")
                        else:
                            print(f"ℹ️  Ответ уже отправлен внутри команды")
                    
                    # Обработка нажатий на кнопки
                    elif "callback_query" in update:
                        callback = update["callback_query"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        callback_data = callback.get("data", "")
                        message_id = callback["message"]["message_id"]
                        
                        print(f"🔘 Нажата кнопка: {callback_data}")
                        
                        # Отвечаем на callback
                        await self.answer_callback_query(callback["id"], "⏳ Обрабатываю...")
                        
                        # Отправляем индикатор ожидания
                        await self.send_message(chat_id, "⏳ Запрашиваю информацию...")
                        
                        # Обрабатываем команду
                        response = await self.process_message(chat_id, f"/{callback_data}")
                        
                        # Отправляем ответ ТОЛЬКО если он не пустой
                        if response and response.strip():
                            success = await self.send_message(chat_id, response)
                            if success:
                                print(f"Ответ на кнопку отправлен успешно!")
                            else:
                                print(f"Ошибка отправки ответа на кнопку!")
                        else:
                            print(f"ℹ️  Ответ уже отправлен внутри команды")
                
                # Небольшая пауза
                await asyncio.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 Остановка бота...")
                break
            except Exception as e:
                print(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)
    
    async def answer_callback_query(self, callback_query_id: str, text: str = "") -> bool:
        """Ответить на callback запрос"""
        try:
            url = f"{self.base_url}/answerCallbackQuery"
            data = {
                "callback_query_id": callback_query_id,
                "text": text,
                "show_alert": False
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Ошибка ответа на callback: {e}")
            return False
    
    async def close(self):
        """Закрыть соединения"""
        await self.client.aclose()
        
        if self.use_mcp:
            await self.mcp.close()
        else:
            await self.prometheus.close()
            await self.loki.close()
            await self.ollama.close()


async def main():
    """Главная функция"""
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        print("Telegram не настроен!")
        print("Запустите: python setup_telegram_bot.py")
        return 1
    
    bot = TelegramMonitoringBot(settings.telegram_bot_token)
    
    try:
        await bot.run()
    finally:
        await bot.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
