@echo off
REM === Запуск Pixel_6 google_apis (root-образ для Burp CA) ===
set EMU=%USERPROFILE%\AppData\Local\Android\Sdk\emulator\emulator.exe
set AVD=Pixel_6
echo [*] Запускаю %AVD% с -writable-system (нужно для системного серта Burp)...
echo [*] Первая загрузка долгая (5-10 мин), жди рабочий стол, потом proxy-on.bat
"%EMU%" -avd %AVD% -writable-system -no-snapshot-load -no-snapshot-save
pause
