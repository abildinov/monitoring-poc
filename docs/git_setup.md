# Настройка Git для проекта

Этот документ описывает, как настроить Git репозиторий для проекта мониторинга.

## Быстрый старт

### 1. Инициализация Git

Запустите скрипт для инициализации:

```powershell
cd monitoring-poc
.\scripts\init_git.ps1
```

Скрипт автоматически:
- Создаст `.gitignore` с правильными настройками
- Инициализирует Git репозиторий
- Покажет текущий статус файлов

### 2. Первый коммит

```powershell
# Добавить все файлы
git add .

# Создать коммит
git commit -m "Initial commit: MCP Server Prototype"
```

### 3. Подключение к существующему репозиторию

#### Если репозиторий пустой:

```powershell
git remote add origin https://github.com/ваш-username/ваш-репозиторий.git
git branch -M main
git push -u origin main
```

#### Если в репозитории уже есть файлы:

```powershell
git remote add origin https://github.com/ваш-username/ваш-репозиторий.git
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 4. Быстрые коммиты с помощью скрипта

Для быстрого сохранения изменений:

```powershell
# С автоматическим сообщением (дата и время)
.\scripts\git_push.ps1

# Или с вашим сообщением
.\scripts\git_push.ps1 "Добавлен новый MCP tool для анализа логов"
```

Скрипт:
1. Покажет список измененных файлов
2. Попросит подтверждение
3. Добавит все изменения
4. Создаст коммит
5. Отправит в репозиторий

## Работа из дома

### Клонирование проекта

```powershell
# На домашнем компьютере
git clone https://github.com/ваш-username/ваш-репозиторий.git
cd ваш-репозиторий/monitoring-poc
```

### Настройка окружения

```powershell
# Создать виртуальное окружение
cd mcp-server
python -m venv venv
.\venv\Scripts\Activate.ps1

# Установить зависимости
pip install -r requirements.txt
```

### Синхронизация изменений

**Перед началом работы:**
```powershell
git pull origin main
```

**После работы:**
```powershell
.\scripts\git_push.ps1 "Описание изменений"
```

## Что НЕ попадает в Git

`.gitignore` настроен так, чтобы исключить:

- **Виртуальное окружение** (`venv/`)
- **Данные Loki** (`loki-data/`)
- **Конфигурационные файлы** (`.env`) - содержат пароли и URL
- **Кэш Python** (`__pycache__/`, `*.pyc`)
- **IDE настройки** (`.vscode/`, `.idea/`)
- **Логи** (`*.log`)

## Важно!

⚠️ **Файл `.env` не должен попадать в Git!** Он содержит URL сервера и другие чувствительные данные.

На домашнем компьютере создайте `.env` вручную:

```powershell
cd mcp-server
notepad .env
```

И скопируйте туда конфигурацию с рабочего компьютера.

## Советы

1. **Коммитьте часто** - лучше много маленьких коммитов, чем один большой
2. **Пишите понятные сообщения** - "Добавлен tool для CPU" лучше, чем "Update"
3. **Проверяйте статус** - `git status` перед коммитом
4. **Тестируйте перед push** - запустите тесты перед отправкой в репозиторий

## Примеры сообщений коммитов

Хорошие примеры:
```
✅ feat: Добавлен MCP tool для мониторинга CPU
✅ fix: Исправлена ошибка в LokiClient при пустых логах
✅ docs: Обновлена документация для chat_with_ollama.py
✅ test: Добавлены тесты для PrometheusClient
```

Плохие примеры:
```
❌ update
❌ fix
❌ changes
```

## Troubleshooting

### Ошибка: "fatal: remote origin already exists"

```powershell
git remote remove origin
git remote add origin <новый_URL>
```

### Конфликты при pull

```powershell
# Сохраните ваши изменения
git stash

# Получите изменения
git pull origin main

# Верните ваши изменения
git stash pop

# Если есть конфликты - исправьте их вручную
```

### Случайно закоммитили .env

```powershell
# Удалить из Git, но оставить локально
git rm --cached mcp-server/.env
git commit -m "Remove .env from repository"
git push
```

