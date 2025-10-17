# Руководство по развертыванию

## Подготовка к развертыванию

### 1. Очистка проекта

Удалите следующие папки и файлы:
- `loki-data/` (вся папка)
- `mcp-server/venv/` (вся папка)
- Все папки `__pycache__/`
- Все файлы `test_*.py`
- `stress_test_report.txt`

### 2. Создание .env файла

Создайте файл `.env` в корне проекта:

```env
# Telegram Bot
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Ollama LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TIMEOUT=300

# Prometheus
PROMETHEUS_URL=http://localhost:9090

# Loki
LOKI_URL=http://localhost:3100

# Пороги мониторинга
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0

# HTTP настройки
HTTP_TIMEOUT=30
```

## Развертывание на новом компьютере

### 1. Клонирование репозитория

```bash
git clone <your-repo-url>
cd monitoring-poc
```

### 2. Установка Python зависимостей

```bash
cd mcp-server
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Установка Ollama

1. Скачайте с https://ollama.ai
2. Установите и запустите: `ollama serve`
3. Установите модель: `ollama pull llama3.2:1b`

### 4. Настройка Telegram бота

1. Создайте бота через @BotFather
2. Получите токен и Chat ID
3. Обновите `.env` файл

### 5. Запуск системы

```bash
# Полная система
python scripts/start_all.py

# Или только бот (без LLM)
python scripts/start_telegram_bot_simple.py
```

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

## Проверка работы

1. **Telegram бот**: Отправьте `/start`
2. **MCP сервер**: Проверьте http://localhost:3000
3. **Claude Desktop**: Спросите "Покажи загрузку CPU"

## Оптимизация производительности

### Для слабых компьютеров:
1. Используйте `llama3.2:1b` модель
2. Запускайте `start_telegram_bot_simple.py`
3. Увеличьте таймауты в `.env`

### Для мощных компьютеров:
1. Используйте `qwen2.5:3b` или `llama3.1:8b`
2. Запускайте полную систему
3. Включите все функции

## Структура файлов после развертывания

```
monitoring-poc/
├── .env                    # Переменные окружения
├── .gitignore             # Исключения Git
├── README_FINAL.md        # Документация
├── DEPLOYMENT_GUIDE.md    # Это руководство
├── mcp-server/            # MCP сервер
│   ├── venv/              # Виртуальное окружение
│   ├── server.py          # Основной сервер
│   ├── config.py          # Конфигурация
│   └── requirements.txt   # Зависимости
├── scripts/               # Скрипты запуска
└── dashboards/            # Grafana дашборды
```

## Поддержка

При проблемах:
1. Проверьте логи в консоли
2. Убедитесь, что все сервисы запущены
3. Проверьте настройки в `.env`
4. Перезапустите систему
