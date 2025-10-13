# Система мониторинга серверной инфраструктуры с поддержкой MCP и LLM

Дипломный проект по разработке интеллектуальной системы мониторинга с интеграцией больших языковых моделей.

## 🎯 Описание проекта

Система мониторинга серверной инфраструктуры с поддержкой MCP (Model Context Protocol) и локальных LLM для автоматизированного анализа метрик, логов и генерации рекомендаций.

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────┐
│  Удаленный сервер (147.45.157.2)    │
│  ├─ Prometheus :9090                │
│  ├─ Loki :3100                      │
│  └─ Grafana :3000                   │
└─────────────────────────────────────┘
              ↕ HTTP
┌─────────────────────────────────────┐
│  Локальный компьютер                │
│  ┌───────────────────────────────┐  │
│  │  MCP Server (Python)          │  │
│  │  ├─ PrometheusClient           │  │
│  │  ├─ LokiClient                │  │
│  │  └─ MCP Tools (10+)           │  │
│  └───────────────────────────────┘  │
│              ↕                      │
│  ┌───────────────────────────────┐  │
│  │  Ollama (локальная LLM)       │  │
│  │  ├─ llama3                    │  │
│  │  └─ deepseek-r1:8b            │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```powershell
# Создать виртуальное окружение
cd monitoring-poc\mcp-server
python -m venv venv

# Активировать
.\venv\Scripts\Activate.ps1

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Отредактировать `mcp-server/.env`:

```env
# URL серверов мониторинга
PROMETHEUS_URL=http://147.45.157.2:9090
LOKI_URL=http://147.45.157.2:3100

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

### 3. Проверка компонентов

```powershell
# Тест всех клиентов
python ..\scripts\test_clients.py
```

Должны быть зеленые галочки для всех компонентов:
- ✅ Prometheus
- ✅ Loki  
- ✅ Ollama

## 📁 Структура проекта

```
monitoring-poc/
├── server-infrastructure/    # Инфраструктура на сервере
│   ├── docker-compose.yml
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
│
├── mcp-server/               # MCP сервер (локально)
│   ├── server.py            # Главный файл
│   ├── config.py            # Конфигурация
│   ├── requirements.txt
│   │
│   ├── clients/             # HTTP клиенты
│   │   ├── prometheus_client.py
│   │   └── loki_client.py
│   │
│   ├── tools/               # MCP Tools
│   │   └── (в разработке)
│   │
│   ├── llm/                 # LLM интеграция
│   │   ├── ollama_client.py
│   │   └── prompts/
│   │
│   └── analytics/           # Аналитика
│       └── (в разработке)
│
├── tests/                   # Тесты
├── docs/                    # Документация
└── scripts/                 # Утилиты
    └── test_clients.py
```

## 🔧 Компоненты

### Реализовано ✅

1. **Инфраструктура мониторинга** (удаленный сервер)
   - Prometheus для сбора метрик
   - Loki для сбора логов
   - Grafana для визуализации
   - 4 готовых дашборда

2. **HTTP Клиенты** (локально)
   - `PrometheusClient` - получение метрик
   - `LokiClient` - получение логов
   - `OllamaClient` - работа с локальной LLM

3. **Ollama Integration**
   - Модели: llama3, deepseek-r1:8b
   - Анализ метрик
   - Анализ логов
   - Детекция аномалий

4. **MCP Server** ✅ WORKING PROTOTYPE
   - Базовый сервер с stdio transport
   - 3 рабочих MCP tools
   - Интеграция Prometheus + Loki + Ollama
   - Локальное тестирование

5. **MCP Tools** (3 базовых)
   - ✅ `get_cpu_usage` - загрузка CPU с анализом LLM
   - ✅ `get_memory_status` - состояние RAM с анализом
   - ✅ `search_error_logs` - поиск ошибок в логах

### В разработке 🚧

1. **Интеграция с Claude Desktop**
   - Конфигурация MCP сервера
   - Тестирование через UI

2. **Дополнительные MCP Tools** (7-10 штук)
   - get_disk_usage
   - get_network_io
   - get_container_stats
   - get_system_summary
   - analyze_timerange
   - и др.

3. **Analytics**
   - Статистическая детекция аномалий
   - Baseline calculation
   - Pattern analysis

## 📊 Использование

### Быстрый старт прототипа

```powershell
# Перейти в директорию MCP сервера
cd monitoring-poc/mcp-server

# Активировать виртуальное окружение
.\venv\Scripts\Activate.ps1

# Запустить локальное тестирование всех tools
python test_server.py
```

**Ожидаемый результат**:
```
TEST 1: GET_CPU_USAGE          [OK]
TEST 2: GET_MEMORY_STATUS      [OK]
TEST 3: SEARCH_ERROR_LOGS      [OK]

[SUCCESS] ВСЕ ТЕСТЫ ПРОЙДЕНЫ!
```

### Запуск MCP сервера

```powershell
# Запуск для Claude Desktop
python server.py
```

### Тест клиентов

```python
# Prometheus
from clients.prometheus_client import PrometheusClient

client = PrometheusClient("http://147.45.157.2:9090")
cpu = await client.get_current_cpu()
print(f"CPU: {cpu}%")
```

```python
# Loki
from clients.loki_client import LokiClient

client = LokiClient("http://147.45.157.2:3100")
errors = await client.get_error_logs(hours=24)
print(f"Errors: {len(errors)}")
```

```python
# Ollama
from llm.ollama_client import OllamaClient

client = OllamaClient(model="llama3")
analysis = await client.analyze_metrics({"cpu": 85, "memory": 78})
print(analysis)
```

### Интерактивный чат с Ollama

Общайся с системой мониторинга на естественном языке:

```powershell
# Запустить интерактивный чат
python chat_with_ollama.py
```

**Доступные команды:**
- `/cpu` - Загрузка CPU
- `/memory` - Использование памяти
- `/disk` - Использование дисков
- `/logs` - Последние ошибки
- `/status` - Полный статус системы
- `/help` - Справка

**Или задавай вопросы:**
```
Вы> Какая нагрузка на сервере?
Вы> Есть ли ошибки в логах?
Вы> Всё ли в порядке?
```

📖 Подробнее: [docs/interactive_chat.md](docs/interactive_chat.md)

## 🔄 Работа с Git

### Первоначальная настройка

```powershell
# Инициализация репозитория
.\scripts\init_git.ps1

# Первый коммит
git add .
git commit -m "Initial commit: MCP Server Prototype"

# Подключение к GitHub
git remote add origin https://github.com/username/repository.git
git push -u origin main
```

### Быстрое сохранение изменений

```powershell
# Автоматический коммит и push
.\scripts\git_push.ps1 "Описание изменений"
```

### Работа дома

```powershell
# Клонировать проект
git clone https://github.com/username/repository.git

# Перед работой - получить изменения
git pull origin main

# После работы - отправить изменения
.\scripts\git_push.ps1 "Описание работы"
```

📖 Подробнее: [docs/git_setup.md](docs/git_setup.md)

## 🎓 Дипломная работа

**Тема:** "Разработка системы мониторинга серверной инфраструктуры с поддержкой MCP и больших языковых моделей"

**Автор:** Абильдинов Алексей

**Научная новизна:**
- Архитектура интеграции LLM с системами мониторинга через MCP
- Набор специализированных MCP tools для анализа метрик и логов
- Гибридный подход к детекции аномалий (статистика + LLM)

**Практическая ценность:**
- Автоматический анализ инцидентов
- Генерация рекомендаций по устранению
- Снижение времени реакции на проблемы
- Работа без облачных сервисов (приватность данных)

## 🔗 Полезные ссылки

- **Prometheus:** http://147.45.157.2:9090
- **Grafana:** http://147.45.157.2:3000
- **Loki:** http://147.45.157.2:3100
- **Ollama:** http://localhost:11434

## 📄 Лицензия

MIT License
