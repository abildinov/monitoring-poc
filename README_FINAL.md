# Система мониторинга с MCP и Telegram ботом

## Описание проекта

Полнофункциональная система мониторинга с интеграцией:
- **MCP Server** - единый бэкенд для всех интерфейсов
- **Telegram Bot** - интерфейс для мобильных уведомлений
- **Claude Desktop** - интеграция с AI ассистентом
- **Prometheus** - сбор метрик
- **Loki** - сбор логов
- **Ollama** - локальный LLM для анализа

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │  Claude Desktop │    │   Web Interface │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      MCP Server          │
                    │   (HTTP API + stdio)     │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐          ┌─────▼─────┐          ┌─────▼─────┐
    │Prometheus │          │   Loki    │          │  Ollama   │
    │(метрики)  │          │ (логи)    │          │   (LLM)   │
    └───────────┘          └───────────┘          └───────────┘
```

## Быстрый старт

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
cd mcp-server
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка Ollama

```bash
# Установка Ollama (https://ollama.ai)
# Запуск Ollama
ollama serve

# Установка модели (выберите одну)
ollama pull llama3.2:1b    # Быстрая, легкая
ollama pull qwen2.5:3b     # Средняя, качественная
ollama pull llama3.1:8b    # Медленная, качественная
```

### 3. Настройка Telegram бота

```bash
# Создание бота через @BotFather
# Получение токена и Chat ID

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл
```

### 4. Запуск системы

**Вариант 1: Полная система (MCP + Telegram)**
```bash
python scripts/start_all.py
```

**Вариант 2: Только Telegram бот (без LLM)**
```bash
python scripts/start_telegram_bot_simple.py
```

**Вариант 3: Только MCP сервер**
```bash
python mcp-server/server.py --transport http
```

## Команды Telegram бота

- `/start` - Приветствие и меню
- `/analyze` - Полный анализ системы с LLM
- `/status` - Быстрый статус метрик
- `/health` - Проверка здоровья сервисов
- `/alerts` - Активные алерты
- `/chat` - Чат с LLM
- `/menu` - Показать меню
- `/help` - Справка

## Настройка Claude Desktop

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "monitoring": {
      "command": "python",
      "args": ["C:/path/to/monitoring-poc/mcp-server/server.py"],
      "cwd": "C:/path/to/monitoring-poc"
    }
  }
}
```

## Структура проекта

```
monitoring-poc/
├── mcp-server/           # MCP сервер
│   ├── server.py         # Основной сервер
│   ├── config.py         # Конфигурация
│   ├── clients/          # Клиенты для Prometheus/Loki
│   ├── llm/              # LLM интеграция
│   ├── alerts/           # Система алертов
│   └── requirements.txt  # Зависимости
├── scripts/              # Скрипты запуска
│   ├── start_all.py      # Запуск всей системы
│   ├── telegram_monitoring_bot.py  # Telegram бот
│   └── mcp_client.py     # MCP клиент
├── dashboards/           # Grafana дашборды
├── prometheus/           # Конфигурация Prometheus
├── loki/                 # Конфигурация Loki
└── promtail/             # Конфигурация Promtail
```

## Переменные окружения

Создайте файл `.env`:

```env
# Telegram
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TIMEOUT=300

# Prometheus
PROMETHEUS_URL=http://localhost:9090

# Loki
LOKI_URL=http://localhost:3100

# Пороги
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0
```

## Возможности системы

### MCP Tools
- `get_cpu_usage` - Загрузка CPU
- `get_memory_status` - Статус памяти
- `get_network_status` - Сетевые метрики
- `get_top_processes` - Топ процессов
- `search_error_logs` - Поиск ошибок в логах
- `get_active_alerts` - Активные алерты

### LLM Анализ
- Автоматический анализ метрик
- Рекомендации по оптимизации
- Прогнозирование проблем
- Объяснение технических данных

### Telegram интеграция
- Reply клавиатура для быстрого доступа
- Inline кнопки для команд
- Уведомления об алертах
- Интерактивный чат с LLM

## Устранение неполадок

### Проблемы с производительностью
1. Используйте легкую модель LLM (`llama3.2:1b`)
2. Запускайте без LLM анализа (`start_telegram_bot_simple.py`)
3. Увеличьте таймауты в конфигурации

### Проблемы с Telegram
1. Проверьте токен бота
2. Убедитесь, что Chat ID правильный
3. Проверьте интернет соединение

### Проблемы с MCP
1. Проверьте, что порт 3000 свободен
2. Убедитесь, что все зависимости установлены
3. Проверьте логи сервера

## Лицензия

MIT License

## Автор

Система мониторинга с MCP интеграцией
