# Стресс-тест CPU и памяти на Windows
Write-Host "Starting stress test..."

# Количество потоков = число логических процессоров
$threads = [Environment]::ProcessorCount
Write-Host "Using $threads threads"

$scriptBlock = {
    while ($true) {
        1..10000 | ForEach-Object { [math]::Sqrt($_) }  # нагружаем CPU
    }
}

# Запуск потоков
$jobs = @()
for ($i = 0; $i -lt $threads; $i++) {
    $jobs += Start-Job -ScriptBlock $scriptBlock
}

# Память (создаём массив на ~500MB)
$mem = New-Object byte[] (500MB)
[void][System.Random]::new().NextBytes($mem)

# Ждём 60 секунд
Start-Sleep -Seconds 60

# Останавливаем потоки
$jobs | ForEach-Object { Stop-Job $_; Remove-Job $_ }

Write-Host "Stress test finished!"
