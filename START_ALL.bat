@echo off
chcp 65001 >nul
REM === MTS Burp Bridge + Soft: ОДИН ЗАПУСК ВСЕГО ===
REM 1. Проверяет Pixel_6, ставит прокси 10.0.2.2:8080
REM 2. Проверяет Burp на 127.0.0.1:8080
REM 3. Запускает soft/main.py
set ADB=%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe
set SOFTDIR=%~dp0soft

echo ===== [1/3] Проверка эмулятора =====
"%ADB%" devices | findstr /R "emulator-.*device" >nul
if errorlevel 1 (
  echo [!] Эмулятор не запущен.
  echo     Запусти: start-pixel6-root.bat  (или через Android Studio Device Manager - Pixel_6)
  echo     Дождись загрузки и запусти этот файл снова.
  pause
  exit /b 1
)
echo [OK] Эмулятор на месте.

echo.
echo ===== [2/3] Включаю прокси-мост 10.0.2.2:8080 =====
"%ADB%" shell settings put global http_proxy 10.0.2.2:8080
"%ADB%" shell settings put global https_proxy 10.0.2.2:8080
"%ADB%" shell settings get global http_proxy

echo.
echo Проверка Burp (должен слушать 127.0.0.1:8080, Intercept OFF)...
python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8080)); print('[OK] Burp слушает 8080')" 2>nul
if errorlevel 1 (
  echo [!] Burp НЕ отвечает на 127.0.0.1:8080.
  echo     Запусти Burp с листенером 8080 и повтори. Софт все равно запущу,
  echo     но отладка через Burp не пойдет.
) else (
  echo [OK] Мост до Burp есть. Chrome в эмуляторе -^> example.com должен попасть в HTTP history.
)

echo.
echo ===== [3/3] Запуск софта =====
cd /d "%SOFTDIR%"
python main.py
pause
