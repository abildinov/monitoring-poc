# Скрипт инициализации Git репозитория и первого коммита
# Использование: .\scripts\init_git.ps1

Write-Host "=== Инициализация Git репозитория ===" -ForegroundColor Green
Write-Host ""

# Проверка, находимся ли в корне проекта
if (-not (Test-Path "mcp-server")) {
    Write-Host "[!] Ошибка: Запустите скрипт из корня monitoring-poc" -ForegroundColor Red
    exit 1
}

# Создание .gitignore если его нет
if (-not (Test-Path ".gitignore")) {
    Write-Host "[+] Создание .gitignore..." -ForegroundColor Yellow
    
    @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Environments
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
mcp-server/venv/
loki-data/
*.log

# Jupyter
.ipynb_checkpoints/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
*.egg-info/
dist/
build/
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8
    
    Write-Host "[+] .gitignore создан" -ForegroundColor Green
}

# Инициализация Git если не инициализирован
if (-not (Test-Path ".git")) {
    Write-Host "[+] Инициализация Git..." -ForegroundColor Yellow
    git init
    Write-Host "[+] Git инициализирован" -ForegroundColor Green
} else {
    Write-Host "[i] Git уже инициализирован" -ForegroundColor Cyan
}

# Проверка статуса
Write-Host ""
Write-Host "[+] Статус Git:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "=== Следующие шаги ===" -ForegroundColor Green
Write-Host ""
Write-Host "1. Добавить файлы в staging:"
Write-Host "   git add ."
Write-Host ""
Write-Host "2. Создать первый коммит:"
Write-Host "   git commit -m ""Initial commit: MCP Server Prototype"""
Write-Host ""
Write-Host "3. Добавить удаленный репозиторий:"
Write-Host "   git remote add origin https://github.com/ваш-username/ваш-репозиторий.git"
Write-Host ""
Write-Host "4. Отправить в репозиторий:"
Write-Host "   git branch -M main"
Write-Host "   git push -u origin main"
Write-Host ""
Write-Host "Или если репозиторий уже существует:"
Write-Host "   git remote add origin <URL>"
Write-Host "   git pull origin main --allow-unrelated-histories"
Write-Host "   git push -u origin main"
Write-Host ""

