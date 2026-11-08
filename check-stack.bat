@echo off
chcp 65001 >nul
REM === Проверка всего стека одним кликом ===
echo ===== СТЕК ПРОВЕРКИ =====
echo.
echo [1] Python:
python --version 2>&1
echo [2] Библиотеки:
python -c "import requests, yaml, frida; print('  requests', requests.__version__, '| yaml OK | frida-py', frida.__version__)" 2>&1
frida --version 2>&1 | findstr /R "[0-9]" >nul && (echo|set /p="  frida-tools: " & frida --version) || echo "  frida-tools: НЕТ"
objection version 2>&1 | findstr /I "objection" || echo "  objection: НЕТ"
echo [3] ADB:
"%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe" version 2>&1 | findstr /I "Version"
"%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe" devices 2>&1
echo [4] Эмуляторы (AVD):
dir /b "%USERPROFILE%\.android\avd\*.ini" 2>&1
echo [5] Burp на 8080:
python -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('127.0.0.1',8080)); print('  Burp СЛУШАЕТ 8080')" 2>nul || echo "  Burp НЕ отвечает (запусти Burp с листенером 8080)"
echo [6] Frida-server файл:
if exist "%~dp0frida-server" (echo   frida-server ЕСТЬ) else (echo   frida-server НЕТ)
if exist "%~dp0cacert.der" (echo   cacert.der ЕСТЬ) else (echo   cacert.der НЕТ - экспортируй из Burp)
echo [7] APK Мой МТС в папке:
dir /b "%~dp0*.apk" 2>&1 | findstr /I apk || echo "  APK нет (поставь из Play Store в эмуляторе)"
echo.
pause
