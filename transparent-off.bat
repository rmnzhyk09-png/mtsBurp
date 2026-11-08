@echo off
chcp 65001 >nul
REM === Выключить невидимый мост (вернуть прямой интернет) ===
set ADB=C:\Users\Hp\AppData\Local\Android\Sdk\platform-tools\adb.exe
"%ADB%" wait-for-device
"%ADB%" shell iptables -t nat -D OUTPUT -p tcp --dport 80 -j DNAT --to-destination 10.0.2.2:8080 2>nul
"%ADB%" shell iptables -t nat -D OUTPUT -p tcp --dport 443 -j DNAT --to-destination 10.0.2.2:8080 2>nul
echo [OK] Редирект снят, интернет прямой.
pause
