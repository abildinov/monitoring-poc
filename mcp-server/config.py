"""
Конфигурация MCP сервера для мониторинга
"""

import os
from typing import Optional

# Простая конфигурация без pydantic для совместимости
class Settings:
    """Настройки MCP сервера"""
    
    def __init__(self):
        # Основные настройки сервера
        self.mcp_server_name = os.getenv("MCP_SERVER_NAME", "monitoring-server")
        self.mcp_server_version = os.getenv("MCP_SERVER_VERSION", "1.0.0")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # HTTP настройки
        self.http_timeout = int(os.getenv("HTTP_TIMEOUT", "30"))
        
        # Prometheus настройки
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://147.45.157.2:9090")
        
        # Loki настройки
        self.loki_url = os.getenv("LOKI_URL", "http://147.45.157.2:3100")
        
        # Ollama настройки
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        
        # Пороговые значения для мониторинга
        self.cpu_threshold = float(os.getenv("CPU_THRESHOLD", "80.0"))
        self.memory_threshold = float(os.getenv("MEMORY_THRESHOLD", "85.0"))
        
        # Валидация настроек
        self._validate()
    
    def _validate(self):
        """Проверка корректности настроек"""
        
        # Проверка URL
        if not self.prometheus_url.startswith(('http://', 'https://')):
            raise ValueError(f"Некорректный URL Prometheus: {self.prometheus_url}")
        
        if not self.loki_url.startswith(('http://', 'https://')):
            raise ValueError(f"Некорректный URL Loki: {self.loki_url}")
        
        if not self.ollama_host.startswith(('http://', 'https://')):
            raise ValueError(f"Некорректный URL Ollama: {self.ollama_host}")
        
        # Проверка пороговых значений
        if not (0 <= self.cpu_threshold <= 100):
            raise ValueError(f"Порог CPU должен быть от 0 до 100: {self.cpu_threshold}")
        
        if not (0 <= self.memory_threshold <= 100):
            raise ValueError(f"Порог памяти должен быть от 0 до 100: {self.memory_threshold}")
        
        # Проверка таймаутов
        if self.http_timeout <= 0:
            raise ValueError(f"HTTP таймаут должен быть положительным: {self.http_timeout}")
        
        if self.ollama_timeout <= 0:
            raise ValueError(f"Ollama таймаут должен быть положительным: {self.ollama_timeout}")


# Создание глобального экземпляра настроек
settings = Settings()


# Функция для получения информации о конфигурации
def get_config_info() -> str:
    """Получить информацию о текущей конфигурации"""
    
    return f"""
Конфигурация MCP сервера:
- Сервер: {settings.mcp_server_name} v{settings.mcp_server_version}
- Логирование: {settings.log_level}
- HTTP таймаут: {settings.http_timeout}с

Сервисы:
- Prometheus: {settings.prometheus_url}
- Loki: {settings.loki_url}
- Ollama: {settings.ollama_host} (модель: {settings.ollama_model})

Пороги:
- CPU: {settings.cpu_threshold}%
- Память: {settings.memory_threshold}%
"""


if __name__ == "__main__":
    # Вывод конфигурации при прямом запуске
    print(get_config_info())
