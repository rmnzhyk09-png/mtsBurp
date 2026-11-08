@echo off
REM === MTS Burp Bridge: включить прокси на эмуляторе ===
REM Эмулятор обращается к хосту через 10.0.2.2 (это твой 127.0.0.1)
set ADB=%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe
set BURP_HOST=10.0.2.2
set BURP_PORT=8080

echo [*] Жду устройство...
"%ADB%" wait-for-device
echo [*] Ставлю прокси %BURP_HOST%:%BURP_PORT%
"%ADB%" shell settings put global http_proxy %BURP_HOST%:%BURP_PORT%
"%ADB%" shell settings put global https_proxy %BURP_HOST%:%BURP_PORT%
echo [*] Проверка:
"%ADB%" shell settings get global http_proxy
echo.
echo [OK] Прокси включен. В Burp должен быть Listener 127.0.0.1:8080 Running.
echo Если интернета нет - проверь что Burp запущен и Intercept OFF.
pause
