@echo off
REM === MTS Burp Bridge: выключить прокси ===
set ADB=C:\Users\Hp\AppData\Local\Android\Sdk\platform-tools\adb.exe
"%ADB%" wait-for-device
"%ADB%" shell settings put global http_proxy :0
"%ADB%" shell settings put global https_proxy :0
"%ADB%" shell settings delete global http_proxy 2>nul
"%ADB%" shell settings delete global https_proxy 2>nul
echo [OK] Прокси снят, прямой интернет.
pause
