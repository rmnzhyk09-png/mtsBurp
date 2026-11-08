@echo off
chcp 65001 >nul
REM === Установка Burp CA в СИСТЕМНЫЕ серты Pixel_6 (android-33 google_apis) ===
REM Что нужно ДО запуска: Burp запущен, cacert.der лежит в ЭТОЙ папке, Pixel_6 полностью загружен (рабочий стол).
REM Экспорт серта: Burp -> Proxy -> Proxy settings -> Import/export CA certificate -> Export DER -> cacert.der сюда.

REM --- self-logging: весь вывод дублируется в install.log, окно не закрывается ---
if not defined MTSBURP_LOG (
  set MTSBURP_LOG=1
  call "%~f0" %* > "%~dp0install.log" 2>&1
  echo.
  echo ===== Хвост лога install.log: =====
  powershell -NoProfile -Command "Get-Content '%~dp0install.log' -Tail 30"
  echo ===== конец (полный лог: install.log) =====
  pause
  exit /b
)

set ADB=C:\Users\Hp\AppData\Local\Android\Sdk\platform-tools\adb.exe
set OPENSSL=C:\Program Files\Git\usr\bin\openssl.exe
cd /d "%~dp0"

if not exist cacert.der (
  echo [X] Нет cacert.der в папке %CD%
  echo     Сделай экспорт из Burp и положи файл сюда, потом повтори.
  exit /b 1
)
if not exist "%OPENSSL%" (
  echo [X] Не найден openssl: %OPENSSL%
  exit /b 1
)

echo [*] Жду эмулятор (adbd)...
"%ADB%" wait-for-device
"%ADB%" devices
for /f "tokens=*" %%M in ('"%ADB%" shell getprop ro.product.model 2^>nul') do set MODEL=%%M
echo [*] Модель устройства: [%MODEL%] (ждем Pixel 6; если Pixel 9 - запущен не тот эмулятор!)

echo [*] Жду ПОЛНОЙ загрузки Android (не только adbd)...
set TRIES=0
:bootwait
set BOOTED=0
for /f "tokens=*" %%B in ('"%ADB%" shell getprop sys.boot_completed 2^>nul') do set BOOTED=%%B
if "%BOOTED:~0,1%"=="1" goto bootdone
set /a TRIES+=1
if %TRIES% GEQ 40 (
  echo [X] 10 минут жду, а Android так и не загрузился. Чини эмулятор (вайп/перезапуск), потом повтори.
  exit /b 1
)
echo     ...еще грузится (попытка %TRIES%/40), жду 15 сек...
timeout /t 15 >nul
goto bootwait
:bootdone
echo [*] Android загружен полностью.

echo [*] Конвертирую DER -^> PEM и считаю hash...
"%OPENSSL%" x509 -inform DER -in cacert.der -out burp.pem
if errorlevel 1 ( echo [X] openssl не смог прочитать cacert.der & exit /b 1 )
for /f %%H in ('"%OPENSSL%" x509 -inform PEM -subject_hash_old -noout -in burp.pem') do set HASH=%%H
echo HASH=%HASH%
copy burp.pem %HASH%.0 >nul
echo [*] Готов файл %HASH%.0

echo.
echo [*] Получаю root...
"%ADB%" root
timeout /t 3 >nul
"%ADB%" wait-for-device
for /f "tokens=*" %%U in ('"%ADB%" shell whoami 2^>nul') do set WHO=%%U
echo [*] whoami: [%WHO%] (должен быть root; если shell - запущен PlayStore-образ без рута!)

echo [*] Отключаю verity (нужно 1 раз, потом будет ребут)...
"%ADB%" disable-verity
echo [*] Ребут для применения disable-verity...
"%ADB%" reboot
echo [*] Жду загрузку ~60 сек...
timeout /t 60 >nul
"%ADB%" wait-for-device
set TRIES2=0
:bootwait2
set BOOTED2=0
for /f "tokens=*" %%B in ('"%ADB%" shell getprop sys.boot_completed 2^>nul') do set BOOTED2=%%B
if "%BOOTED2:~0,1%"=="1" goto bootdone2
set /a TRIES2+=1
if %TRIES2% GEQ 24 ( echo [X] После disable-verity не грузится 6 минут. Смотри лог выше. & exit /b 1 )
timeout /t 15 >nul
goto bootwait2
:bootdone2
"%ADB%" root
timeout /t 3 >nul
"%ADB%" remount
if errorlevel 1 (
  echo [!] remount не удался с первого раза, пробую еще раз после root...
  timeout /t 3 >nul
  "%ADB%" root
  timeout /t 3 >nul
  "%ADB%" remount
)

echo [*] Кладу серт в систему...
"%ADB%" push %HASH%.0 /system/etc/security/cacerts/
"%ADB%" shell chmod 644 /system/etc/security/cacerts/%HASH%.0
"%ADB%" shell ls /system/etc/security/cacerts/ | findstr %HASH%

echo [*] Финальный ребут...
"%ADB%" reboot
echo [*] Жду загрузку ~60 сек...
timeout /t 60 >nul
"%ADB%" wait-for-device

echo.
echo [*] Возвращаю прокси-мост (слетает после ребута)...
"%ADB%" shell settings put global http_proxy 10.0.2.2:8080
"%ADB%" shell settings put global https_proxy 10.0.2.2:8080
"%ADB%" shell settings get global http_proxy

echo.
echo [OK] Готово. Проверка в эмуляторе:
echo   Settings -^> Security -^> Encryption ^& credentials -^> Trusted credentials -^> System
echo   Там должен быть PortSwigger CA.
echo   Затем: Chrome в эмуляторе -^> https://example.com -^> запрос виден в Burp расшифрованным.
echo   Если Chrome ОК, а приложение рвет TLS - это SSL Pinning, дальше frida-unpin.bat.
