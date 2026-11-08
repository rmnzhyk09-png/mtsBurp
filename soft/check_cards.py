"""Повторная проверка: показать список карт без повторного выпуска."""
import json
from pathlib import Path
from mts_api import MTSClient, get_by_path

BASE = Path(__file__).parent

sess = json.loads((BASE / "session.json").read_text(encoding="utf-8"))
token = sess["token"]
client = MTSClient(endpoints_path=str(BASE / "endpoints.yaml"), log_dir=str(BASE / "logs"))
r = client.call("list_cards", {"phone": sess["phone"], "code": "", "token": token})
j = client.as_json(r)
print(f"HTTP {r.status_code}")
cfg = client.cfg.get("list_cards", {})
cards = get_by_path(j, cfg.get("card_list_path", "data.cards"), []) or []
id_f = cfg.get("card_id_field", "id")
mask_f = cfg.get("card_mask_field", "maskedPan")
st_f = cfg.get("card_status_field", "status")
print(f"Всего карт: {len(cards)}")
for c in cards:
    print(f"  id={get_by_path(c, id_f)} mask={get_by_path(c, mask_f)} status={get_by_path(c, st_f)}")
