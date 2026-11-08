"""Точка входа: номер -> код (вручную) -> выпуск виртуалки -> проверка."""
import json
import sys
import uuid
from pathlib import Path

import yaml

from mts_api import MTSClient, get_by_path

BASE = Path(__file__).parent


def ask(prompt: str) -> str:
    return input(prompt).strip()


def main():
    print("=" * 60)
    print("  MTS Burp Replay — выпуск виртуальной МТС Деньги карты")
    print("=" * 60)
    print("Только для СВОЕГО номера. Весь трафик логируется в logs/.\n")

    # Проверка что endpoints.yaml заполнен (а не пример)
    raw = (BASE / "endpoints.yaml").read_text(encoding="utf-8")
    if "api.mts.ru/auth/v1/sendCode" in raw:
        print("[!] endpoints.yaml еще НЕ заполнен из Burp (там примерные URL).")
        print("    Открой soft/README_SOFT.md раздел 2 и вставь 4 реальных запроса.")
        ans = ask("Продолжить с примерными URL для проверки механики? (y/N): ")
        if ans.lower() not in ("y", "yes", "д", "да"):
            sys.exit(0)

    client = MTSClient(endpoints_path=str(BASE / "endpoints.yaml"),
                       log_dir=str(BASE / "logs"))

    # ---- 1. Номер ----
    phone_raw = ask("Введи номер телефона (например 9151234567): ")
    fmt = client.cfg.get("send_code", {}).get("phone_format", "79XXXXXXXXX")
    try:
        phone = client.normalize_phone(phone_raw, fmt)
    except ValueError as e:
        print(f"[X] {e}")
        sys.exit(1)
    print(f"[*] Нормализованный номер: {phone}")

    # ---- 2. Отправка кода ----
    print("\n[1/4] Запрашиваю SMS-код...")
    r1 = client.call("send_code", {"phone": phone})
    j1 = client.as_json(r1)
    print(f"    HTTP {r1.status_code}")
    print(f"    Ответ: {json.dumps(j1, ensure_ascii=False)[:500]}")
    if r1.status_code not in (200, 201, 202, 204):
        print("[X] send_code не ок. Смотри logs/*_send_code.txt и сверь с Burp.")
        print("    Частые причины: неверный URL/тело, нужен другой phone_format,")
        print("    капча/rate-limit, неверные common_headers.")
        sys.exit(1)

    # ---- 3. Код вручную ----
    code = ask("\nВведи код из SMS (4-6 цифр): ")
    if not code.isdigit():
        print("[X] Код должен быть цифрами.")
        sys.exit(1)

    print("\n[2/4] Проверяю код, получаю токен...")
    r2 = client.call("verify_code", {"phone": phone, "code": code})
    j2 = client.as_json(r2)
    print(f"    HTTP {r2.status_code}")
    print(f"    Ответ: {json.dumps(j2, ensure_ascii=False)[:800]}")
    token_path = client.cfg.get("verify_code", {}).get("token_path", "data.accessToken")
    token = get_by_path(j2, token_path)
    if not token:
        print(f"[X] Токен не найден по пути '{token_path}'.")
        print("    Открой logs/*_verify_code.txt, найди токен в JSON")
        print("    и поправь token_path в endpoints.yaml.")
        sys.exit(1)
    print("    [OK] Токен получен.")
    (BASE / "session.json").write_text(
        json.dumps({"phone": phone, "token": token}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # ---- Снимок карт ДО выпуска (чтобы доказать что карта новая) ----
    print("\n[3/5] Снимаю список карт ДО выпуска...")
    list_cfg = client.cfg.get("list_cards", {})
    r3 = client.call("list_cards", {"phone": phone, "code": code, "token": token})
    j3 = client.as_json(r3)
    before_ids = set()
    if r3.status_code == 200:
        cards = get_by_path(j3, list_cfg.get("card_list_path", "data.cards"), []) or []
        before_ids = {str(get_by_path(c, list_cfg.get("card_id_field", "id"))) for c in cards}
        print(f"    Карт до выпуска: {len(before_ids)}")
    else:
        print(f"    [!] list_cards ДО вернул {r3.status_code}, продолжу все равно.")

    # ---- Черновик заявки (согласия) ----
    process_id = str(uuid.uuid4())
    print(f"\n[4/5] Создаю черновик заявки (processId={process_id})...")
    ctx = {"phone": phone, "code": code, "token": token, "processId": process_id}
    rd = client.call("draft", ctx)
    print(f"    HTTP {rd.status_code}")
    if rd.status_code not in (200, 201, 202, 204):
        print("[X] draft не ок. Смотри logs/*_draft.txt.")
        sys.exit(1)

    # ---- 4. Выпуск ----
    print("\n[5/5] Выпускаю виртуальную карту...")
    r4 = client.call("issue_card", ctx)
    j4 = client.as_json(r4)
    print(f"    HTTP {r4.status_code}")
    print(f"    Ответ: {json.dumps(j4, ensure_ascii=False)[:1000]}")
    (BASE / "last_issue_response.json").write_text(
        json.dumps(j4, ensure_ascii=False, indent=2), encoding="utf-8")
    if r4.status_code not in (200, 201, 202):
        print("[X] issue_card не ок. Смотри logs/*_issue_card.txt.")
        sys.exit(1)

    # ---- 5. Проверка что создалась ----
    print("\n[6/5] Проверяю что карта создалась (список ПОСЛЕ)...")
    r5 = client.call("list_cards", {"phone": phone, "code": code, "token": token})
    j5 = client.as_json(r5)
    print(f"    HTTP {r5.status_code}")
    if r5.status_code != 200:
        print("[X] list_cards ПОСЛЕ не ок. Ответ сохранен в logs/.")
        sys.exit(1)
    cards = get_by_path(j5, list_cfg.get("card_list_path", "data.cards"), []) or []
    id_f = list_cfg.get("card_id_field", "id")
    mask_f = list_cfg.get("card_mask_field", "maskedPan")
    st_f = list_cfg.get("card_status_field", "status")
    new_cards = [c for c in cards if str(get_by_path(c, id_f)) not in before_ids]

    print(f"    Всего карт: {len(cards)}, новых: {len(new_cards)}")
    (BASE / "last_cards.json").write_text(
        json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")

    if new_cards:
        print("\n    ===== КАРТА СОЗДАЛАСЬ =====")
        for c in new_cards:
            print(f"    id={get_by_path(c, id_f)} mask={get_by_path(c, mask_f)} "
                  f"status={get_by_path(c, st_f)}")
        print("    Детали: soft/last_cards.json, soft/last_issue_response.json")
    else:
        if cards and not before_ids:
            # до выпуска список снять не удалось — просто показать все
            print("\n    [?] Сравнить не с чем (список ДО не снялся), вот все карты:")
            for c in cards:
                print(f"    id={get_by_path(c, id_f)} mask={get_by_path(c, mask_f)} "
                      f"status={get_by_path(c, st_f)}")
        else:
            print("\n    [X] Новых карт НЕ найдено. Возможные причины:")
            print("    - issue_card вернул успех, но карта выпускается асинхронно "
                  "(подожди 1-2 мин и запусти check_cards.py)")
            print("    - card_list_path/card_id_field неверные в endpoints.yaml")


if __name__ == "__main__":
    main()
