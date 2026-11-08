@echo off
chcp 65001 >nul
REM === Собрать логи для отправки (без токена по умолчанию) ===
REM Создает mts_logs_ДАТА.zip: logs/ + endpoints.yaml + инфо о системе
REM session.json (токен) НЕ кладется специально — не свети токен.
set PROJ=%~dp0
cd /d "%PROJ%"
for /f %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%D
set OUT=%PROJ%mts_logs_%TS%.zip

echo [*] Собираю логи в %OUT%
powershell -NoProfile -Command ^
  "$files = @('soft\logs', 'soft\endpoints.yaml', 'soft\last_cards.json', 'soft\last_issue_response.json') | Where-Object { Test-Path $_ }; " ^
  "if ($files.Count -eq 0) { Write-Host '[X] Нечего паковать: нет logs/ и endpoints.yaml'; exit 1 }; " ^
  "Compress-Archive -Path $files -DestinationPath '%OUT%' -Force; " ^
  "Write-Host ('[OK] Запаковано: %OUT%')"
if errorlevel 1 ( pause & exit /b 1 )
echo.
echo [OK] Отправь файл mts_logs_%TS%.zip.
echo [!] В нем НЕТ session.json (токена). Если просят повторить ошибку —
echo     приложи скрин Burp HTTP history + текст ошибки из консоли.
echo [!] Никому не отправляй soft\session.json — там твой токен доступа.
pause
