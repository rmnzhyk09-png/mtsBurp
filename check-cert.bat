@echo off
chcp 65001 >nul
REM === Проверка: прокси + системный серт Burp на месте? ===
set ADB=%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe
"%ADB%" wait-for-device
echo --- 1. Прокси ---
"%ADB%" shell settings get global http_proxy
echo     (должно быть 10.0.2.2:8080)
echo.
echo --- 2. Системные серты PortSwigger ---
"%ADB%" shell ls /system/etc/security/cacerts/ ^| findstr /I "9a5ba575"
echo     (если пусто — серт не стоит; hash может отличаться, тогда смотри весь список:)
"%ADB%" shell ls /system/etc/security/cacerts/ ^| find /c ".0"
echo     (число файлов .0 — обычно 130+)
echo.
echo --- 3. Burp слушает? ---
python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8080)); print('[OK] Burp отвечает на 8080')" 2>nul
if errorlevel 1 ( echo [X] Burp НЕ отвечает на 127.0.0.1:8080 — запусти Burp ) else ( echo [OK] Мост доступен )
echo.
echo --- 4. Эмулятор ---
"%ADB%" devices
pause
