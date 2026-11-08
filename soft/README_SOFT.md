# MTS Burp Replay — софт: номер -> код -> виртуалка МТС Деньги -> проверка

Работает методом **API-реплея**: повторяет 4 запроса приложения «Мой МТС»,
которые ты один раз подсмотришь в Burp. Код вводишь вручную в консоль.

```
soft/
  main.py              — главный сценарий (запуск)
  check_cards.py       — перепроверить список карт позже (без выпуска)
  mts_api.py           — HTTP-клиент, подстановки, логи
  endpoints.yaml       — 4 запроса из Burp (ЗАПОЛНИТЬ!)
  curl_import.py       — конвертер "Copy as curl" -> YAML
  requirements.txt
  run.bat              — запуск в одно нажатие
  logs/                — сюда пишутся все запросы/ответы
  session.json         — сохранится токен (после verify)
  last_cards.json      — последний список карт
```

## 0. Важно про твой эмулятор

У тебя `Pixel_9 / Pixel_9a` — образ **PlayStore**. На нем:

- `adb root` не работает («adbd cannot run as root in production builds»),
- Burp CA нельзя положить в системные серты,
- «Мой МТС» (как почти все банковские приложения, Android 7+) **не примет**
  пользовательский серт и/или упадет на SSL-pinning.

Итог: на текущем эмуляторе ты увидишь в Burp только Chrome/HTTP,
а запросы Мой МТС — нет. Для реплея нужен один раз снять трафик:

**Вариант А (рекомендую для снятия):** создать второй AVD без Play Store:

1. Android Studio -> Device Manager -> Create Device -> Pixel 6
2. Image: API 30/31/33 **`google_apis` x86_64 БЕЗ надписи Play Store**
3. Запуск: `emulator -avd <имя> -writable-system`
4. `adb root && adb remount`, положи Burp CA в
   `/system/etc/security/cacerts/` (см. корневой README.md п.3)
5. Если все равно `SSLHandshakeException / Trust anchor / Pinning` —
   нужен Frida: `frida-server` на эмулятор + скрипт обхода pinning
   (`frida --codeshare` поищи `ssl-pinning-bypass`). Могу расписать отдельно.

**Вариант Б (если pinning не пробивается):** скажи — перепишу софт на
UI-автомат через `adb + uiautomator2` (тыкает кнопки в приложении,
Burp вообще не нужен, работает на твоем Pixel_9).

## 1. Установка

```bat
cd soft
pip install -r requirements.txt
```

`requests` и `pyyaml` у тебя уже стоят — команда просто проверит.

## 2. Заполнение endpoints.yaml из Burp (10 минут)

Burp запущен, прокси `10.0.2.2:8080` включен (`proxy-on.bat`), серт стоит,
приложение «Мой МТС» ходит через Burp, Intercept OFF.

Нужно поймать **4 запроса** (каждый: правый клик -> Copy as cURL):

| # | Действие в приложении | Что искать в Burp HTTP history |
|---|-----------------------|-------------------------------|
| 1 | Ввод номера -> «Получить код» | POST с номером (`msisdn`, `phone`, `login`...) |
| 2 | Ввод кода из SMS -> «Войти» | POST с кодом (`code`, `otp`...), в ответе токен |
| 3 | МТС Деньги -> «Выпустить виртуальную карту» | POST `.../cards.../issue`, `.../virtual...`, `.../emission...` |
| 4 | Экран «Мои карты» | GET `.../cards`, `.../products...` (список карт) |

Для каждого запроса:

```bat
python curl_import.py
:: вставь curl, нажми Ctrl+Z Enter
:: скопируй вывод в endpoints.yaml в нужную секцию
```

Затем в `endpoints.yaml` замени конкретику на плейсхолдеры:

- свой номер -> `{{phone}}`
- код `1234` -> `{{code}}`
- токен `eyJhbGci...` -> `{{token}}` (в headers `Authorization: Bearer {{token}}`)

И поправь три пути под реальный JSON:

- `verify_code.token_path` — где токен в ответе (напр. `data.accessToken`)
- `list_cards.card_list_path` — где массив карт (напр. `data.cards`)
- `card_id_field / card_mask_field / card_status_field`

`phone_format` выбери как в Burp: `79XXXXXXXXX` | `+79XXXXXXXXX` | `9XXXXXXXXX`.

## 3. Запуск

```bat
run.bat
:: или: python main.py
```

Сценарий:

1. Вводишь номер -> уходит `send_code`
2. Вводишь код из SMS вручную -> уходит `verify_code`, токен в `session.json`
3. Снимается список карт ДО
4. Уходит `issue_card`
5. Снимается список карт ПОСЛЕ, новые (которых не было в ДО) печатаются:

```
===== КАРТА СОЗДАЛАСЬ =====
id=123456 mask=2200••••1234 status=ACTIVE
```

Если карта выпускается асинхронно (успех, но в списке пока нет) —
подожди 1-2 мин и запусти:

```bat
python check_cards.py
```

## 4. Отладка

- Все запросы/ответы: `soft/logs/2026..._send_code.txt` и т.д.
- Параллельно смотри тот же трафик в Burp (если `use_burp_proxy: true`),
  поле `verify` при этом выключено специально.
- `send_code` не 2xx -> неверный URL/тело/headers, капча, rate-limit.
- `verify_code` ок, но «токен не найден» -> открой лог, поправь `token_path`.
- `issue_card` 401/403 -> токен протух или нужен дополнительный header
  (`X-Device-Id`, `X-Session-Id` — подсмотри в Burp и добавь в секцию).
- `list_cards` 0 новых -> проверь `card_list_path`, либо карта еще
  выпускается — повтори `check_cards.py` позже.

## 5. Честность

Софт повторяет **твои собственные** действия со **своим** номером.
Не используй для чужих номеров, массовых выпусков и обхода лимитов МТС —
это нарушение правил МТС и может быть нарушением закона.
