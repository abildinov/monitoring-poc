# Быстрый скрипт для коммита и пуша изменений
# Использование: .\scripts\git_push.ps1 "описание изменений"

param(
    [Parameter(Mandatory=$false)]
    [string]$Message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

Write-Host "=== Git Push ===" -ForegroundColor Green
Write-Host ""

# Проверка наличия изменений
$status = git status --porcelain

if (-not $status) {
    Write-Host "[i] Нет изменений для коммита" -ForegroundColor Cyan
    exit 0
}

# Показываем изменения
Write-Host "[+] Измененные файлы:" -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "[?] Добавить все изменения и закоммитить? (Y/n): " -NoNewline -ForegroundColor Yellow
$confirm = Read-Host

if ($confirm -eq "" -or $confirm -eq "Y" -or $confirm -eq "y") {
    
    # Добавляем все изменения
    Write-Host "[+] Добавление файлов..." -ForegroundColor Yellow
    git add .
    
    # Коммитим
    Write-Host "[+] Создание коммита: $Message" -ForegroundColor Yellow
    git commit -m "$Message"
    
    # Пушим
    Write-Host "[+] Отправка в репозиторий..." -ForegroundColor Yellow
    git push
    
    Write-Host ""
    Write-Host "[SUCCESS] Изменения отправлены в репозиторий!" -ForegroundColor Green
    
} else {
    Write-Host "[!] Отменено" -ForegroundColor Red
}

Write-Host ""

