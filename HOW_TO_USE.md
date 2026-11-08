# Как пользоваться БЕЗ меня — шпаргалка (5 минут)

Порядок кнопок всегда один. Делай сверху вниз.

## Первый раз (один раз)

1. `start-pixel6-root.bat` — запускает Pixel_6 (жди минуту полной загрузки)
2. Запусти Burp → листенер `8080 / All interfaces / Running`, `Intercept OFF`
3. Экспорт серта: Burp → Proxy settings → Import/export CA → Export DER → сохрани как
   `cacert.der` ПРЯМО В ЭТУ ПАПКУ (рядом с bat-файлами)
4. `install-burp-cert-system.bat` — кладет серт в систему (2 ребута, ~3 мин, прокси вернет сам)
5. `check-cert.bat` — должно быть: прокси `10.0.2.2:8080`, серт `9a5ba575.0` в списке, Burp отвечает
6. Chrome в эмуляторе → `https://example.com` → в Burp виден расшифрованный запрос = мост работает

## Каждый день (обычный запуск)

1. `start-pixel6-root.bat` (или Play в Android Studio)
2. Burp 8080 Running, Intercept OFF
3. `START_ALL.bat` — сам включит прокси и запустит софт
   - введи номер → дождись SMS → введи код руками → смотри итог
   - только СВОЙ номер, код из СВОЕЙ sms

## Поставить приложение

- Правильно: Play Store в эмуляторе → найди «Мой МТС» → Install. Или официальный APK с mts.ru.
- НЕ качай банковский APK с apkpure и подобных — туда могут подмешать вредоносный код, а ты потом вводишь туда свой номер и код из SMS.
- Если APK уже есть файлом: перетащи `app.apk` мышкой НА файл `install-apk.bat` → `adb install -r`
- или просто перетащи APK на окно эмулятора
- холодный рестарт приложения после включения прокси (свайп-закрыть → открыть)
- пакет называется `ru.mts.mymts` (проверить: `adb shell pm list packages | findstr mts`)

## Если приложение рвет HTTPS (SSL Pinning) — обход через Frida

Предусловия: Pixel_6 запущен, прокси включен, системный серт стоит, `frida-server` уже лежит в папке.

1. `push-frida.bat` — зальет `frida-server 17.19.0` в `/data/local/tmp` и запустит (проверка: `frida-ps -U` покажет процессы)
2. `frida-unpin.bat` — запустит Мой МТС через `soft/frida_unpin.js` (TrustManager + SSLContext + OkHttp3 + WebView)
   - альтернатива там же: `objection ... explore --startup-command "android sslpinning disable"`
3. Тыкайся в приложении → трафик появится в Burp расшифрованным → дальше `curl_import.py` → `endpoints.yaml` как обычно

## Если сломалось — таблица

| Симптом | Что нажать |
|---|---|
| Нет запросов в Burp, интернет есть | `proxy-on.bat`, перезапусти приложение |
| Нет интернета вообще | проверь Burp запущен + Intercept OFF + фаервол 8080 |
| HTTP есть, HTTPS нет | серт не в системе → `install-burp-cert-system.bat` заново |
| Chrome ОК, приложение рвет TLS | SSL Pinning — Burp-серта мало, нужен Frida (отдельный этап) |
| `adbd cannot run as root` | ты запустил Pixel_9 PlayStore вместо Pixel_6 — переключись |
| Софт пишет `send_code не ок` | сверь URL/тело с Burp, формат номера, `soft/logs/*_send_code.txt` |
| Софт пишет `токен не найден` | открой `logs/*_verify_code.txt`, поправь `token_path` в `endpoints.yaml` |
| Софт пишет `issue 401/403` | токен протух или нужен `X-Device-Id` из Burp в `endpoints.yaml` |
| Новых карт нет, но issue 200 | карта едет асинхронно → подожди 2 мин → `python check_cards.py` в папке soft |

## Логи: где лежат и как передавать/получать

- Все запросы/ответы: `soft/logs/2026..._send_code.txt`, `..._verify_code.txt` и т.д.
- Последний ответ выпуска: `soft/last_issue_response.json`
- Список карт: `soft/last_cards.json`
- Токен: `soft/session.json` — НИКОМУ НЕ ОТПРАВЛЯЙ, это доступ к твоему аккаунту

Отправить логи мне/другу:
1. Запусти `collect-logs.bat` → создастся `mts_logs_ДАТА.zip` (logs + endpoints + итоги, БЕЗ токена)
2. Отправь этот zip + скрин ошибки из консоли + скрин Burp HTTP history
3. Получить обратно: распакуй чужой zip ВРЕМЕННО в отдельную папку, сравни `endpoints.yaml` и логи, свои `session.json`/`logs` не затирай

## Файлы — что зачем

- `START_ALL.bat` — главная кнопка: прокси + проверка Burp + запуск софта
- `start-pixel6-root.bat` — запуск Pixel_6 с writable-system
- `proxy-on.bat` / `proxy-off.bat` — вкл/выкл моста вручную
- `install-burp-cert-system.bat` — серт Burp в систему (нужен cacert.der)
- `check-cert.bat` — проверка моста за 5 сек
- `install-apk.bat` — кинь на него APK
- `collect-logs.bat` — запаковать логи для отправки
- `soft/run.bat` — запуск только софта без проверок
- `check-stack.bat` — проверка всего стека одним кликом (Python, frida, adb, AVD, Burp, серт, APK)
- `push-frida.bat` — залить и запустить frida-server на эмуляторе
- `frida-unpin.bat` — запуск Мой МТС с обходом SSL Pinning
- `frida-server`, `frida-server-17.19.0-android-x86_64(.xz)` — сервер под Pixel_6, версия = frida-tools 14.10.4 / frida-py 17.19.0 (должны совпадать!)

## Установка Burp (единственное что ставится руками)

Burp нельзя поставить скриптом (лицензия + ~500 МБ): качай с portswigger.net/burp/communitydownload (бери 2023.x или новее),
установщик сам принесет нужную Java. После установки — листенер `8080 / All interfaces / Running`, `Intercept OFF`.
