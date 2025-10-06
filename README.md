# Система мониторинга серверной инфраструктуры с поддержкой MCP и LLM

Дипломный проект по разработке интеллектуальной системы мониторинга с интеграцией больших языковых моделей.

## 🎯 Описание проекта

Система мониторинга серверной инфраструктуры с поддержкой MCP (Model Context Protocol) и больших языковых моделей для автоматизированного анализа метрик, логов и генерации рекомендаций.

## 🏗️ Архитектура системы

### Компоненты мониторинга:
- **Prometheus** - сбор и хранение метрик
- **Grafana** - визуализация и дашборды
- **Loki** - сбор и хранение логов
- **Node Exporter** - системные метрики сервера
- **cAdvisor** - метрики Docker контейнеров
- **Promtail** - сбор логов Docker контейнеров

### Дашборды:
- **System Monitoring (Node Exporter)** - базовый мониторинг системных метрик
- **Enhanced System Monitoring** - расширенный мониторинг с Load Average
- **Docker Monitoring (cAdvisor)** - мониторинг Docker контейнеров
- **System Metrics Dashboard** - обзор состояния стека мониторинга

## 🚀 Быстрый старт

### Запуск системы:

```bash
# Клонируем репозиторий
git clone https://github.com/abildinov/monitoring-poc.git
cd monitoring-poc

# Запускаем систему мониторинга
docker-compose up -d

# Проверяем статус сервисов
docker ps
```

### Доступ к сервисам:

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Loki:** http://localhost:3100
- **cAdvisor:** http://localhost:8080

## 📊 Дашборды

Все дашборды экспортированы в папке `dashboards/exported/`:

- `system-monitoring-node-exporter.json` - системные метрики
- `enhanced-system-monitoring.json` - расширенные системные метрики
- `docker-monitoring-cadvisor.json` - метрики контейнеров
- `system-metrics-dashboard.json` - обзор стека мониторинга

### Импорт дашбордов:

```bash
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @dashboards/exported/FILENAME.json
```

## 🔧 Конфигурация

### Prometheus (`prometheus/prometheus.yml`):
- Сбор метрик с Node Exporter
- Сбор метрик с cAdvisor
- Собственные метрики Prometheus

### Loki (`loki/local-config.yaml`):
- Файловое хранение логов
- Retention: 7 дней
- Схема индексации: v13

### Promtail (`promtail/config-fixed.yml`):
- Сбор логов Docker контейнеров
- Фильтрация по Docker Compose сервисам
- Парсинг уровней логов

## 📈 Метрики

### Системные метрики (Node Exporter):
- CPU Load Average (1м, 5м, 15м)
- CPU Usage (User, System, I/O Wait)
- Memory Usage (Active, Used, Available)
- Disk Usage (Used, Available)
- System Processes (Running, Blocked)
- Network I/O

### Метрики контейнеров (cAdvisor):
- Container CPU Usage
- Container Memory Usage
- Container Network I/O
- Container Disk I/O

## 🔍 Логирование

### Централизованный сбор логов:
- Логи всех Docker контейнеров
- Парсинг уровней логов (info, warn, error)
- Поиск по контейнерам и временным диапазонам
- Обнаружение ошибок

## 🎯 Особенности

- ✅ Русские подписи и единицы измерения
- ✅ Цветовые пороги для предупреждений
- ✅ Оптимизация для Docker окружения
- ✅ Исправленные метрики дисков
- ✅ Статус здоровья сервисов
- ✅ Готовность к интеграции с MCP и LLM

## 🔮 Планы развития

- [ ] MCP-инструменты для интеграции с LLM
- [ ] Автоматический анализ аномалий
- [ ] Генерация отчетов и рекомендаций
- [ ] RCA (Root Cause Analysis) с помощью LLM
- [ ] Диалоговый поиск по метрикам и логам

## 📚 Технологии

- **Docker & Docker Compose** - контейнеризация
- **Prometheus** - сбор метрик
- **Grafana** - визуализация
- **Loki** - сбор логов
- **Node Exporter** - системные метрики
- **cAdvisor** - метрики контейнеров
- **Promtail** - сбор логов
- **Python** - MCP-инструменты (в разработке)
- **LLM Integration** - большие языковые модели (в разработке)

## 👨‍💻 Автор

**Абильдинов Алексей** - студент магистратуры
Дипломная работа: "Разработка системы мониторинга серверной инфраструктуры с поддержкой MCP и больших языковых моделей"

## 📄 Лицензия

MIT License
