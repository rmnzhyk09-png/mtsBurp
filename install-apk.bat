@echo off
REM === Установка APK на эмулятор (drag&drop замена) ===
REM Использование: install-apk.bat путь\к\app.apk
set ADB=C:\Users\Hp\AppData\Local\Android\Sdk\platform-tools\adb.exe
if "%~1"=="" (
  echo Перетащи APK на этот bat-файл.
  echo Пример: install-apk.bat C:\Downloads\app.apk
  pause
  exit /b 1
)
"%ADB%" wait-for-device
"%ADB%" install -r "%~1"
echo [OK] Готово.
pause
