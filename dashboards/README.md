# Дашборды системы мониторинга

Эта папка содержит экспортированные дашборды из Grafana для системы мониторинга серверной инфраструктуры.

## Структура дашбордов

### 1. System Monitoring (Node Exporter)
**Файл:** `system-monitoring-node-exporter.json`
**UID:** `node-monitor`
**Описание:** Базовый мониторинг системных метрик сервера
**Метрики:**
- CPU Load (нагрузка процессора)
- Memory Usage (использование памяти)
- Disk Usage (использование диска)
- System Health Status (статус сервисов)

### 2. Enhanced System Monitoring
**Файл:** `enhanced-system-monitoring.json`
**UID:** `enhanced-system-monitor`
**Описание:** Расширенный мониторинг системных метрик
**Метрики:**
- CPU Load Average (1м, 5м, 15м)
- CPU Usage по режимам (User, System, I/O Wait)
- Memory Usage (Active, Used, Available)
- System Processes (Running, Blocked)
- Disk Usage по точкам монтирования

### 3. Docker Monitoring (cAdvisor)
**Файл:** `docker-monitoring-cadvisor.json`
**UID:** `docker-cadvisor`
**Описание:** Мониторинг Docker контейнеров
**Метрики:**
- Container CPU Usage (по контейнерам)
- Container Memory Usage (по контейнерам)
- Network I/O (Receive/Transmit по контейнерам)

### 4. System Metrics Dashboard
**Файл:** `system-metrics-dashboard.json`
**UID:** `docker-logs`
**Описание:** Обзор состояния стека мониторинга
**Метрики:**
- Container CPU Usage (Grafana, Prometheus, Loki)
- Container Memory Usage (Grafana, Prometheus, Loki)
- Service Status (Prometheus, Node Exporter, cAdvisor)

## Импорт дашбордов

Для импорта дашбордов в Grafana используйте API:

```bash
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @dashboards/exported/FILENAME.json
```

## Особенности

- Все дашборды имеют русские подписи
- Настроены правильные единицы измерения
- Используются цветовые пороги для предупреждений
- Оптимизированы для Docker окружения
