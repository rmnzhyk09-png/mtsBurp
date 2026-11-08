# MTS Burp Bridge — прокси-мост Эмулятор → Burp

> **Репозиторий очищен перед публикацией.** Сырые Burp-логи с токенами,
> `.pfx`-сертификат, сессии и `frida-server` (116 МБ) исключены.
> Что именно убрано и как восстановить локально — см. [SECURITY.md](SECURITY.md).

Твой текущий сетап (проверил):
- `adb` есть: `%USERPROFILE%\AppData\Local\Android\Sdk\platform-tools\adb.exe`
- Эмуляторы есть: `Pixel_9`, `Pixel_9a` (образ `android-36.1 google_apis_playstore`, Android 16)
- Burp НЕ найден — сначала поставь его
- Твой IP в LAN: `<LAN-IP>`, а для эмулятора хост — это всегда `10.0.2.2`

> Важно: твой образ **PlayStore нельзя зарутить** и нормально положить Burp CA в системные сертификаты.
> Итог: Chrome со вставленным юзер-сертом заведется, а 90% приложений (МТС и др.) на Android 7+ будут рвать HTTPS с ошибкой pinning / Trust anchor.
> Для полноценного сниффера создай второй AVD **без Play Store** (см. пункт 0).

## 0. Burp — установка и листенер

1. Скачай Burp Suite Community (или Pro): https://portswigger.net/burp/communitydownload
2. Запусти, создай временный проект → `Proxy → Proxy settings → Proxy listeners`:
   - `Bind to port: 8080`
   - `Bind to address: All interfaces` (или `127.0.0.1` — хватит, т.к. эмулятор ходит через `10.0.2.2 → 127.0.0.1`)
   - `Running: ☑`
3. `Proxy → Intercept → Intercept is off` (иначе интернет "встанет").
4. Проверка с ПК: открой в браузере `http://127.0.0.1:8080` — Burp должен ответить (или в `Proxy → HTTP history` появится трафик после настройки браузера на прокси).

Фаервол Windows: разреши `Java / Burp` входящие на 8080, иначе эмулятор не достучится.

## 1. Правильный эмулятор для сниффинга (рекомендую)

Android Studio → `Device Manager → Create Device`:
- Device: Pixel 6 / 9, RAM 2048+
- Image: **API 30 / 31 / 33, `google_apis`, x86_64, БЕЗ надписи Play Store**
  - НЕ бери `Google Play`, бери `Google APIs`
- AVD Name например: `Pixel_API30_root`

Почему: `google_apis` дает `adb root` + `-writable-system`, можно положить серт в `/system/etc/security/cacerts/`.

Свой текущий `Pixel_9 (API 36 PlayStore)` оставь для теста, но знай ограничение выше.

Запуск:
```
emulator -avd Pixel_API30_root -writable-system
```
или через Device Manager кнопкой Play.

## 2. Мост: пустить трафик эмулятора в Burp (2 способа)

### Способ А — скриптом (проще, уже лежит в папке)
1. Запусти Burp (листенер 8080 Running, Intercept OFF)
2. Запусти эмулятор
3. Запусти `proxy-on.bat` → проверит `settings get global http_proxy` → должен показать `10.0.2.2:8080`
4. Открой Chrome в эмуляторе → зайди на `http://example.com` → в Burp `HTTP history` должен появиться запрос.
5. Выключить: `proxy-off.bat`

Что делает скрипт:
```
adb shell settings put global http_proxy 10.0.2.2:8080
```

### Способ Б — вручную через WiFi (то же самое, но руками)
В эмуляторе: `Settings → Network → Internet → AndroidWifi → ✏️ → Advanced → Proxy: Manual`:
- `Hostname: 10.0.2.2`
- `Port: 8080` → Save

### Способ В — флагом запуска
`start-emulator-with-proxy.bat`:
```
emulator -avd Pixel_9 -http-proxy 127.0.0.1:8080 -writable-system
```

## 3. HTTPS: сертификат Burp (иначе будет только HTTP)

1. В Burp: `Proxy → Proxy settings → Import / export CA certificate → Export → Certificate in DER format → cacert.der`
2. Положи `cacert.der` в эту папку `mtsBurp`.
3. В эмуляторе открой Chrome → `http://10.0.2.2:8080` (Burp отдает серт) или:
   `Settings → Security → Encryption & credentials → Install a certificate → CA certificate` → выбери файл → Install anyway.
4. Проверка: зайди на `https://example.com` в Chrome эмулятора → в Burp должен быть расшифрованный запрос.

Для приложений этого МАЛО (Android 7+ игнорит user-серты). Нужно в систему:

**Только для root-образа `google_apis` (не PlayStore):**
```bat
REM на ПК: конверт DER → PEM + hash
openssl x509 -inform DER -in cacert.der -out cacert.pem
set HASH=[первые 8 символов из openssl x509 -inform PEM -subject_hash_old -in cacert.pem]
ren cacert.pem %HASH%.0

adb root
adb remount
adb push %HASH%.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/%HASH%.0
adb reboot
```
После ребута: `Settings → Security → Trusted credentials → System` — твой PortSwigger CA должен быть там.
Прокси после ребута накати заново `proxy-on.bat`.

Если `adb root` пишет `adbd cannot run as root in production builds` — у тебя PlayStore-образ, иди в пункт 1 и пересоздай AVD.

## 4. Твоя часть: подключение приложения (инструкция)

Ты сказал "приложения я сам подключу" — вот как:

1. APK скачай на ПК.
2. Поставь: перетащи `app.apk` на `install-apk.bat` (или `adb install -r app.apk`, или просто drag&drop APK на окно эмулятора).
3. Прокси уже включен (`proxy-on.bat`), серт уже в системе (п.3).
4. Холодный старт приложения (свайпом закрой и открой заново), потыкайся в нем 1-2 мин.
5. В Burp: `Proxy → HTTP history → Filter by Host / Method` — ищи домены приложения.
6. Полезное:
   - `Proxy → Intercept` включай только точечно, иначе всё зависнет.
   - Правой кнопкой на запросе → `Send to Repeater` для повторов.
   - Если приложение не видит сеть: `proxy-off.bat` → проверь без Burp, потом снова `proxy-on.bat`.
   - Если HTTPS рвется / `SSLHandshakeException / Trust anchor / Pinning`: это SSL Pinning — Burp-серта мало, нужен Frida + `frida-server` на эмуляторе + скрипт обхода (`frida --codeshare ... ssl-pinning-bypass`). Скажи — распишу второй этап.

## 5. Диагностика если не работает

```bat
adb devices                          :: эмулятор виден? emulator-5554 device
adb shell settings get global http_proxy  :: должен быть 10.0.2.2:8080
adb shell ping -c 2 10.0.2.2         :: хост доступен?
curl -x http://127.0.0.1:8080 http://example.com -v  :: слушает ли Burp?
```

- Нет запросов в Burp, но интернет есть → прокси не применился (перезапусти приложение, проверь WiFi Manual proxy).
- Нет интернета вообще → Burp не запущен / Intercept ON / фаервол блочит 8080.
- HTTP есть, HTTPS нет → не стоит серт (п.3).
- Chrome работает, приложение нет → user-серта мало, нужен system-серт (п.3) или pinning.

---
Файлы в папке:
- `proxy-on.bat` — включить мост 10.0.2.2:8080
- `proxy-off.bat` — выключить
- `start-emulator-with-proxy.bat` — запуск с флагом -http-proxy
- `install-apk.bat` — установка APK (перетащи APK на bat)
