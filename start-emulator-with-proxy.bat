@echo off
REM === Запуск эмулятора Pixel_9 с прокси-флагом (альтернатива proxy-on.bat) ===
REM Использование: сначала запусти Burp с листенером 8080, потом этот bat
set EMU=C:\Users\Hp\AppData\Local\Android\Sdk\emulator\emulator.exe
set AVD=Pixel_9
set BURP_PORT=8080

echo [*] Запускаю %AVD% с -http-proxy 127.0.0.1:%BURP_PORT%
echo [!] Burp уже должен слушать 127.0.0.1:%BURP_PORT%
"%EMU%" -avd %AVD% -http-proxy 127.0.0.1:%BURP_PORT% -writable-system
pause
