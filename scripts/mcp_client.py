"""
MCP клиент для подключения Telegram бота к MCP серверу
"""

import httpx
import json
from typing import Dict, Any, Optional
from loguru import logger


class MCPClient:
    """Клиент для подключения к MCP серверу через HTTP/SSE"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Инициализация MCP клиента
        
        Args:
            base_url: URL MCP сервера
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300)
        logger.info(f"MCPClient инициализирован: {self.base_url}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """
        Вызвать MCP tool через HTTP
        
        Args:
            tool_name: Название tool
            arguments: Аргументы для tool
            
        Returns:
            Результат выполнения tool
        """
        try:
            # Формируем запрос
            payload = {
                "name": tool_name,
                "arguments": arguments or {}
            }
            
            logger.info(f"Вызов MCP tool: {tool_name} с аргументами: {arguments}")
            
            # Отправляем запрос
            response = await self.client.post(
                f"{self.base_url}/call_tool",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Парсим ответ
            result = response.json()
            
            # Извлекаем текст из ответа
            if "content" in result and len(result["content"]) > 0:
                text_content = result["content"][0].get("text", "")
                logger.info(f"MCP tool {tool_name} выполнен успешно")
                return text_content
            else:
                logger.warning(f"MCP tool {tool_name} вернул пустой ответ")
                return "Пустой ответ от MCP tool"
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP ошибка при вызове MCP tool {tool_name}: {e}")
            return f"Ошибка HTTP: {str(e)}"
        except Exception as e:
            logger.error(f"Ошибка при вызове MCP tool {tool_name}: {e}")
            return f"Ошибка: {str(e)}"
    
    async def list_tools(self) -> list:
        """
        Получить список доступных MCP tools
        
        Returns:
            Список доступных tools
        """
        try:
            response = await self.client.get(f"{self.base_url}/list_tools")
            response.raise_for_status()
            result = response.json()
            return result.get("tools", [])
        except Exception as e:
            logger.error(f"Ошибка получения списка tools: {e}")
            return []
    
    async def health_check(self) -> bool:
        """
        Проверить доступность MCP сервера
        
        Returns:
            True если сервер доступен
        """
        try:
            response = await self.client.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Закрыть соединение"""
        await self.client.aclose()
        logger.info("MCPClient закрыт")


