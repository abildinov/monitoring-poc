"""
Telegram уведомитель для системы алертов
"""

import httpx
from typing import Optional
from datetime import datetime
from loguru import logger
from .alert_manager import Alert


class TelegramNotifier:
    """Уведомитель для отправки алертов в Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Инициализация Telegram уведомителя
        
        Args:
            bot_token: Токен Telegram бота
            chat_id: ID чата для отправки сообщений
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.client = httpx.AsyncClient(timeout=30)
        
        logger.info(f"TelegramNotifier инициализирован для чата {chat_id}")
    
    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            text: Текст сообщения
            parse_mode: Режим форматирования (Markdown, HTML)
            
        Returns:
            True если сообщение отправлено успешно
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            
            logger.info("Сообщение отправлено в Telegram")
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Ошибка HTTP при отправке в Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return False
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Отправить алерт в Telegram
        
        Args:
            alert: Объект алерта
            
        Returns:
            True если алерт отправлен успешно
        """
        # Форматирование сообщения
        severity_emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        emoji = severity_emoji.get(alert.severity, '📢')
        
        # Форматирование времени
        time_str = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Создание сообщения
        message = f"""
{emoji} *{alert.name}*

*Сообщение:* {alert.message}
*Метрика:* `{alert.metric_name}`
*Текущее значение:* `{alert.current_value:.2f}`
*Порог:* `{alert.threshold}`
*Время:* {time_str}

*Статус:* {alert.severity.upper()}
        """.strip()
        
        return await self.send_message(message)
    
    async def send_resolved_alert(self, alert: Alert) -> bool:
        """
        Отправить уведомление о разрешении алерта
        
        Args:
            alert: Объект алерта
            
        Returns:
            True если уведомление отправлено успешно
        """
        if not alert.resolved_at:
            return False
        
        time_str = alert.resolved_at.strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
✅ *Алерт разрешен*

*Название:* {alert.name}
*Метрика:* `{alert.metric_name}`
*Время разрешения:* {time_str}

Проблема устранена.
        """.strip()
        
        return await self.send_message(message)
    
    async def send_summary(self, stats: dict) -> bool:
        """
        Отправить сводку по алертам
        
        Args:
            stats: Статистика алертов
            
        Returns:
            True если сводка отправлена успешно
        """
        active_count = stats.get('active_alerts', 0)
        severity_breakdown = stats.get('severity_breakdown', {})
        
        message = f"""
📊 *Сводка по алертам*

*Активных алертов:* {active_count}

*По критичности:*
"""
        
        for severity, count in severity_breakdown.items():
            emoji = {'critical': '🚨', 'warning': '⚠️', 'info': 'ℹ️'}.get(severity, '📢')
            message += f"{emoji} {severity}: {count}\n"
        
        message += f"\n*Время:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self.send_message(message)
    
    async def test_connection(self) -> bool:
        """
        Проверить соединение с Telegram API
        
        Returns:
            True если соединение работает
        """
        try:
            url = f"{self.base_url}/getMe"
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                logger.info(f"Telegram бот подключен: @{bot_info.get('username', 'unknown')}")
                return True
            else:
                logger.error(f"Ошибка Telegram API: {data.get('description', 'Unknown error')}")
                return False
                
        except httpx.HTTPError as e:
            logger.error(f"Ошибка HTTP при проверке Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки Telegram: {e}")
            return False
    
    async def close(self):
        """Закрыть соединения"""
        await self.client.aclose()
        logger.info("TelegramNotifier закрыт")


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Замените на реальные значения
        bot_token = "YOUR_BOT_TOKEN"
        chat_id = "YOUR_CHAT_ID"
        
        notifier = TelegramNotifier(bot_token, chat_id)
        
        # Тест соединения
        if await notifier.test_connection():
            print("✅ Telegram бот подключен")
            
            # Тест отправки сообщения
            if await notifier.send_message("Тестовое сообщение"):
                print("✅ Сообщение отправлено")
            
            # Тест алерта
            from .alert_manager import Alert
            
            test_alert = Alert(
                id="test_alert",
                name="Test Alert",
                severity="warning",
                message="Тестовый алерт",
                metric_name="cpu_usage",
                current_value=85.5,
                threshold=80.0,
                timestamp=datetime.now()
            )
            
            if await notifier.send_alert(test_alert):
                print("✅ Алерт отправлен")
        
        await notifier.close()
    
    asyncio.run(test())
