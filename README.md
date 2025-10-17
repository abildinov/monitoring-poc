# Система мониторинга серверной инфраструктуры

Комплексная система мониторинга с интеграцией LLM для анализа метрик и автоматических рекомендаций.

## 🚀 Возможности

### Мониторинг
- **CPU, память, диски** - базовые метрики системы
- **Сетевые метрики** - трафик, соединения, ошибки
- **Процессы** - топ процессов по ресурсам
- **Логи** - анализ ошибок через Loki

### Анализ через LLM
- **Интерактивный чат** - вопросы на естественном языке
- **Структурированный анализ** - приоритизация проблем по критичности
- **Детекция аномалий** - автоматическое обнаружение с учетом трендов
- **Комплексная оценка** - анализ здоровья всей системы
- **Конкретные рекомендации** - что делать прямо сейчас
- **Ответы на русском** - понятные объяснения с прогнозами

### Алерты
- **Telegram уведомления** - мгновенные оповещения
- **6 правил по умолчанию** - CPU, память, диск, сеть
- **Уровни критичности** - critical, warning, info
- **Cooldown** - предотвращение спама

### Интерфейсы
- **Интерактивный чат** - командная строка с LLM
- **MCP для Claude Desktop** - интеграция с Claude (6 инструментов)
- **Telegram бот** - мобильный доступ с кнопками и MCP интеграцией

## 📁 Структура проекта

```
monitoring-poc/
├── mcp-server/                 # MCP сервер и интерактивный чат
│   ├── alerts/                 # Система алертов
│   │   ├── alert_manager.py    # Менеджер алертов
│   │   └── telegram_notifier.py # Telegram уведомления
│   ├── clients/                # HTTP клиенты
│   │   ├── prometheus_client.py # Prometheus API
│   │   └── loki_client.py      # Loki API
│   ├── llm/                    # LLM интеграция
│   │   └── ollama_client.py    # Ollama клиент
│   ├── server.py               # MCP сервер
│   ├── chat_with_ollama.py     # Интерактивный чат
│   └── config.py               # Конфигурация
├── scripts/                    # Утилиты
│   ├── setup_telegram_bot.py  # Настройка Telegram
│   ├── start_telegram_bot.py  # Запуск Telegram бота
│   ├── start_all.py           # Единый запуск системы
│   └── mcp_client.py          # MCP клиент для Telegram
│   └── telegram_monitoring_bot.py # Код бота
├── docs/                       # Документация
│   ├── ALERTS_SETUP_GUIDE.md  # Система алертов
│   ├── TELEGRAM_BOT_GUIDE.md  # Telegram бот (общее)
│   ├── interactive_chat.md    # Интерактивный чат
│   └── git_setup.md           # Настройка Git
├── TELEGRAM_DEMO_SIMPLE.md    # Демонстрация для защиты
└── README.md                  # Этот файл
```

## 🛠 Установка

### 1. Клонирование и настройка

```bash
git clone <repository>
cd monitoring-poc
```

### 2. Настройка MCP сервера

```bash
cd mcp-server
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Конфигурация

Создайте `.env` файл в `mcp-server/`:

```env
# Серверы мониторинга
PROMETHEUS_URL=http://147.45.157.2:9090
LOKI_URL=http://147.45.157.2:3100

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=true

# Пороги
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
DISK_THRESHOLD=90.0
```

## 🚀 Запуск

### Единая система (РЕКОМЕНДУЕТСЯ)

```bash
cd monitoring-poc
python scripts/start_all.py
```

**Запускает:**
- MCP сервер в SSE режиме (http://localhost:3000)
- Telegram бот с MCP интеграцией
- Claude Desktop использует существующую конфигурацию

### Раздельный запуск

#### Интерактивный чат
```bash
cd mcp-server
venv\Scripts\activate
python chat_with_ollama.py
```

#### MCP сервер для Claude Desktop
```bash
cd mcp-server
venv\Scripts\activate
python server.py --transport stdio
```

#### MCP сервер для Telegram (SSE)
```bash
cd mcp-server
venv\Scripts\activate
python server.py --transport sse
```

#### Telegram бот
```bash
cd monitoring-poc
python scripts/start_telegram_bot.py
```

## 💬 Использование

### Интерактивный чат

```
Доступные команды:
  /cpu       - Показать загрузку CPU
  /memory    - Показать использование памяти
  /disk      - Показать использование дисков
  /logs      - Показать последние ошибки
  /network   - Показать статус сети
  /processes - Показать топ процессов
  /alerts    - Показать активные алерты
  /status    - Полный статус системы
  /help      - Эта справка
  /exit      - Выход

Или задайте вопрос на естественном языке:
"Какая нагрузка на сервере?"
"Есть ли проблемы?"
"Что происходит с памятью?"
```

### MCP Tools для Claude Desktop

После настройки в Claude Desktop доступны 6 инструментов:

1. **get_cpu_usage** - загрузка CPU с анализом
2. **get_memory_status** - состояние памяти с рекомендациями
3. **search_error_logs** - поиск ошибок в логах
4. **get_network_status** - статус сети и трафик
5. **get_top_processes** - топ процессов по ресурсам
6. **get_active_alerts** - активные алерты системы

## 🏗 Единая MCP архитектура

### Принципы архитектуры

**Единый бэкенд для всех интерфейсов:**
- MCP сервер работает в двойном режиме (stdio для Claude Desktop, SSE для Telegram)
- Все интерфейсы используют одни и те же MCP tools
- Единый источник истины для инструментов мониторинга
- Стандартизированные API для всех клиентов

**Преимущества:**
- ✅ Переиспользуемая логика мониторинга
- ✅ Консистентность между интерфейсами
- ✅ Легкое добавление новых клиентов
- ✅ Централизованное управление tools
- ✅ Масштабируемая архитектура

### Архитектурная схема

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   Claude Desktop│    │  Other Clients  │
│                 │    │                 │    │                 │
│ • HTTP/SSE      │    │ • stdio         │    │ • HTTP/SSE      │
│ • MCP Client    │    │ • MCP Protocol  │    │ • MCP Client    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Server    │
                    │                 │
                    │ • SSE Transport │
                    │ • stdio Transport│
                    │ • Unified Tools │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Shared Clients│
                    │                 │
                    │ • Prometheus    │
                    │ • Loki          │
                    │ • Ollama        │
                    └─────────────────┘
```

### Улучшенный LLM анализ

Система использует усовершенствованные промпты для детального анализа:

**Структура ответов:**
- **СТАТУС**: Общая оценка (КРИТИЧНО/ВНИМАНИЕ/НОРМА)
- **ПРОБЛЕМЫ**: Приоритизированный список с уровнями критичности
- **РЕКОМЕНДАЦИИ**: Конкретные действия прямо сейчас
- **ПРОГНОЗ**: Что произойдет, если не действовать

**Уровни критичности:**
- 🔴 КРИТИЧНО (>95%) - требует немедленных действий
- 🟡 ВНИМАНИЕ (>80%) - требует внимания в ближайшее время
- 🟢 НОРМА (<80%) - все в порядке

**Детекция аномалий:**
- Анализ трендов (растет/падает/стабильно)
- Сравнение с историческими данными
- Учет контекста и времени суток
- Прогнозирование развития ситуации

## 🔔 Настройка Telegram

### Автоматическая настройка

```bash
cd scripts
python setup_telegram_bot.py
```

### Ручная настройка

1. Создайте бота через @BotFather
2. Получите токен и chat_id
3. Добавьте в `.env` файл
4. Перезапустите серверы

Подробная инструкция: [docs/TELEGRAM_BOT_GUIDE.md](docs/TELEGRAM_BOT_GUIDE.md)

## 🧪 Тестирование

### MCP сервер

```bash
cd mcp-server
python final_test.py
```

### Интерактивный чат

```bash
cd mcp-server
python chat_with_ollama.py
# Тестируйте команды: /status, /cpu, /memory, /network, /processes, /alerts
```

### Полная интеграция

```bash
cd scripts
python test_full_integration.py
# Проверка всех компонентов: Prometheus, Loki, Ollama, AlertManager, Telegram
```

### Telegram демонстрация (для защиты диплома)

**Запуск единой системы:**
```bash
cd monitoring-poc
python scripts/start_all.py
```

**Команды в Telegram:**
- `/start` - приветствие с кнопками
- `/analyze` - полный анализ через MCP tools
- `/status` - статус системы
- `/health` - здоровье компонентов
- `/alerts` - активные алерты
- `/chat <вопрос>` - вопрос к LLM

**Кнопки в Telegram:**
- 🎓 Анализ LLM - полный анализ системы
- 📊 Статус системы - текущие метрики
- 🏥 Здоровье - проверка компонентов
- 🚨 Алерты - активные предупреждения
- 💬 Чат с LLM - интерактивный чат
- 📋 Меню - показать меню снова

**Подробно:** см. [TELEGRAM_DEMO_SIMPLE.md](TELEGRAM_DEMO_SIMPLE.md)

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PROMETHEUS_URL` | URL Prometheus | `http://147.45.157.2:9090` |
| `LOKI_URL` | URL Loki | `http://147.45.157.2:3100` |
| `OLLAMA_HOST` | URL Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | Модель LLM | `qwen2.5:3b` |
| `CPU_THRESHOLD` | Порог CPU | `80.0` |
| `MEMORY_THRESHOLD` | Порог памяти | `85.0` |
| `DISK_THRESHOLD` | Порог дисков | `90.0` |
| `TELEGRAM_ENABLED` | Включить Telegram | `false` |

### Пороги алертов

- **CPU**: 80% warning, 95% critical
- **Память**: 85% warning, 95% critical
- **Диски**: 90% warning, 95% critical
- **Сеть**: 100 ошибок warning, 500 critical

## 🐛 Устранение неполадок

### MCP сервер не запускается

```bash
# Проверьте зависимости
pip install -r requirements.txt

# Проверьте доступность серверов
curl http://147.45.157.2:9090/-/healthy
curl http://147.45.157.2:3100/ready
```

### Ollama не отвечает

```bash
# Запустите Ollama сервер
ollama serve

# Проверьте модели
ollama list
```

### Telegram не работает

```bash
# Проверьте настройки
python scripts/setup_telegram_bot.py

# Проверьте токен
curl https://api.telegram.org/bot<TOKEN>/getMe
```

## 🧹 Очистка проекта

Проект содержит `.gitignore` для автоматического исключения временных файлов:
- `__pycache__/` - Python кэш
- `venv/` - виртуальное окружение
- `loki-data/` - данные Loki (регенерируются)
- `node_modules/` - Node.js зависимости

Эти папки не должны попадать в Git и могут быть безопасно удалены.

## 📈 Производительность

### Оптимизация

- **Асинхронные** HTTP запросы к Prometheus/Loki
- **Кэширование** результатов LLM анализа
- **Cooldown** для алертов (предотвращение спама)
- **Эффективная обработка** метрик в реальном времени

## 🔒 Безопасность

### Рекомендации

- Используйте VPN для удаленного доступа к серверам
- Ограничьте доступ к Prometheus/Loki
- Храните токены Telegram в `.env` файле (не в Git)
- Используйте приватность данных с локальной LLM (Ollama)

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE

## 📞 Поддержка

- **Issues**: GitHub Issues
- **Документация**: [docs/](docs/)
- **Примеры**: [examples/](examples/)

---

**Система мониторинга v1.0.0** - Комплексное решение для мониторинга серверной инфраструктуры с интеграцией LLM.