@echo off
chcp 65001 >nul
REM === Frida-server 17.19.0 на Pixel_6 (x86_64) ===
REM Запускать при ВКЛЮЧЕННОМ эмуляторе. Сервер нужен для обхода SSL Pinning.
set ADB=%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe
cd /d "%~dp0"
if not exist frida-server ( echo [X] Нет файла frida-server & pause & exit /b 1 )

echo [*] Жду эмулятор...
"%ADB%" wait-for-device
"%ADB%" root
timeout /t 2 >nul
echo [*] Заливаю frida-server...
"%ADB%" push frida-server /data/local/tmp/frida-server
"%ADB%" shell chmod 755 /data/local/tmp/frida-server
"%ADB%" shell "pkill -f frida-server 2>/dev/null; /data/local/tmp/frida-server &"
timeout /t 2 >nul
echo [*] Проверка USB-моста Frida:
frida-ps -U
echo.
echo [OK] Если выше список процессов эмулятора — frida-server работает.
echo Дальше: frida-unpin.bat (Мой МТС) или objection.
pause
