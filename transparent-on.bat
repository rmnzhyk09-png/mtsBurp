@echo off
chcp 65001 >nul
REM === Невидимый мост: трафик 80/443 -> Burp БЕЗ записи в настройках прокси ===
REM Приложение не видит прокси (settings пустые), защита от детекта прокси обходится.
REM В BURP ОБЯЗАТЕЛЬНО: Proxy -> Proxy settings -> Listener 8080 -> Edit -> [x] Support invisible proxying
set ADB=C:\Users\Hp\AppData\Local\Android\Sdk\platform-tools\adb.exe
"%ADB%" wait-for-device
"%ADB%" shell settings delete global http_proxy 2>nul
"%ADB%" shell settings delete global https_proxy 2>nul
"%ADB%" root >nul
timeout /t 3 >nul
"%ADB%" shell iptables -t nat -D OUTPUT -p tcp --dport 80 -j DNAT --to-destination 10.0.2.2:8080 2>nul
"%ADB%" shell iptables -t nat -D OUTPUT -p tcp --dport 443 -j DNAT --to-destination 10.0.2.2:8080 2>nul
"%ADB%" shell iptables -t nat -A OUTPUT -p tcp --dport 80 -j DNAT --to-destination 10.0.2.2:8080
"%ADB%" shell iptables -t nat -A OUTPUT -p tcp --dport 443 -j DNAT --to-destination 10.0.2.2:8080
"%ADB%" shell iptables -t nat -L OUTPUT -n -v | findstr DNAT
echo.
echo [OK] Невидимый редирект включен. Не забудь invisible-галочку в Burp!
pause
