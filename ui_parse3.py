"""Ищем кнопку Продолжить и поля ввода по тексту/классу."""
import xml.etree.ElementTree as ET
import os
import re

f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.xml")
root = ET.parse(f).getroot()
for node in root.iter("node"):
    text = node.get("text", "") or ""
    desc = node.get("content-desc", "") or ""
    cls = (node.get("class", "") or "").split(".")[-1]
    check = (node.get("checkable", "") == "true")
    edit = "EditText" in cls
    hit = ("родолжен" in text or "родолжить" in desc or check or edit
           or "телефон" in text.lower() or "phone" in text.lower()
           or "номер" in text.lower())
    if not hit:
        continue
    b = node.get("bounds", "")
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
    cx = cy = "?"
    if m:
        x1, y1, x2, y2 = map(int, m.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    print(f"{cls} text={text[:40]!r} desc={desc[:40]!r} tap {cx} {cy}")
print("DONE")
