# Quick Start Guide - Новые возможности

## 🎯 Что нового?

1. **Интерактивный чат с Ollama** - общайся с системой мониторинга на русском языке
2. **Git интеграция** - сохраняй и синхронизируй работу между компьютерами

## 💬 Интерактивный чат

### Запуск

```powershell
cd monitoring-poc\mcp-server
.\venv\Scripts\Activate.ps1
python chat_with_ollama.py
```

### Примеры использования

**Быстрые команды:**
```
Вы> /status          # Полный статус системы
Вы> /cpu             # Загрузка CPU
Вы> /memory          # Использование памяти
Вы> /logs            # Последние ошибки
```

**Вопросы на естественном языке:**
```
Вы> Какая нагрузка на сервере?
Вы> Есть ли проблемы?
Вы> Хватает ли памяти?
Вы> Что случилось с сервером?
Вы> Всё ли в порядке?
```

**Анализ и рекомендации:**
```
Вы> Что делать с высокой нагрузкой CPU?
Вы> Нужно ли добавлять память?
Вы> Как оптимизировать работу?
```

### Как это работает

1. Ты задаешь вопрос
2. Система собирает метрики с сервера (Prometheus + Loki)
3. Данные отправляются в локальную LLM (Ollama)
4. LLM анализирует и отвечает с учетом реальных данных

⚠️ **Важно:** Первый запрос может занять 30-60 секунд (модель загружается в память)

## 🔄 Работа с Git

### Первый раз (настройка)

```powershell
cd monitoring-poc

# 1. Инициализация
.\scripts\init_git.ps1

# 2. Первый коммит
git add .
git commit -m "Initial commit: MCP Server Prototype"

# 3. Подключение к своему репозиторию на GitHub
git remote add origin https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git
git branch -M main
git push -u origin main
```

### Ежедневная работа

**На работе (перед уходом домой):**
```powershell
cd monitoring-poc
.\scripts\git_push.ps1 "Добавлен новый MCP tool для CPU"
```

**Дома (начало работы):**
```powershell
# Если проект еще не клонирован
git clone https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ.git
cd ВАШ_РЕПОЗИТОРИЙ/monitoring-poc

# Настроить окружение
cd mcp-server
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# ВАЖНО: Создать .env файл вручную!
notepad .env
# Скопируй туда конфигурацию с рабочего компьютера
```

**Дома (перед работой):**
```powershell
cd monitoring-poc
git pull origin main
```

**Дома (после работы):**
```powershell
.\scripts\git_push.ps1 "Описание изменений"
```

### Что НЕ попадает в Git

❌ Файл `.env` (содержит пароли и URL) - создавай вручную на каждом компьютере
❌ Папка `venv/` (виртуальное окружение) - создавай заново на каждом компьютере
❌ Папка `loki-data/` (данные Loki) - слишком большая

✅ Весь код Python
✅ Конфигурации Docker
✅ Документация
✅ Скрипты

## 🎬 Демо для диплома

### Сценарий 1: Интерактивный чат

```powershell
# 1. Запустить чат
python chat_with_ollama.py

# 2. Показать статус
Вы> /status

# 3. Задать вопрос
Вы> Всё ли в порядке с сервером?

# 4. Проверить детали
Вы> /cpu
Вы> /memory
Вы> /logs

# 5. Попросить рекомендацию
Вы> Что делать, если CPU загружен на 90%?
```

### Сценарий 2: MCP Tools

```powershell
# Запустить тестирование всех tools
python test_server.py

# Показать результаты:
# [OK] get_cpu_usage
# [OK] get_memory_status
# [OK] search_error_logs
```

## 📚 Полная документация

- **Интерактивный чат:** [docs/interactive_chat.md](docs/interactive_chat.md)
- **Git интеграция:** [docs/git_setup.md](docs/git_setup.md)
- **Прототип:** [docs/prototype_demo.md](docs/prototype_demo.md)

## ❓ Частые вопросы

**Q: Ollama не отвечает / долго думает**
```powershell
# Проверь, запущен ли Ollama
ollama list

# Если не запущен
ollama serve
```

**Q: Не подключается к серверу (Prometheus/Loki)**
- Проверь интернет
- Проверь `.env` файл
- Попробуй открыть в браузере: http://147.45.157.2:9090

**Q: Git говорит "remote origin already exists"**
```powershell
git remote remove origin
git remote add origin НОВЫЙ_URL
```

**Q: Как посмотреть, что изменилось?**
```powershell
git status
git diff
```

## 🚀 Следующие шаги

1. ✅ Протестировать интерактивный чат
2. ✅ Настроить Git и сделать первый push
3. ⏳ Добавить больше MCP tools (7-10 штук)
4. ⏳ Интегрировать с Claude Desktop
5. ⏳ Написать тесты
6. ⏳ Подготовить демонстрацию для диплома

---

**Нужна помощь?** Посмотри полную документацию в папке `docs/`

