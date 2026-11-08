"""Все кликабельные узлы с координатами (без фильтра по тексту)."""
import xml.etree.ElementTree as ET
import re

f = r"C:\Users\Hp\OneDrive\Desktop\GYM\mtsBurp\ui.xml"
root = ET.parse(f).getroot()
for node in root.iter("node"):
    if node.get("clickable") != "true":
        continue
    text = (node.get("text", "") or "")[:40]
    desc = (node.get("content-desc", "") or "")[:40]
    cls = (node.get("class", "") or "").split(".")[-1]
    b = node.get("bounds", "")
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
    if not m:
        continue
    x1, y1, x2, y2 = map(int, m.groups())
    w, h = x2 - x1, y2 - y1
    if w * h < 20000:
        continue
    print(f"{cls} text={text!r} desc={desc!r} tap {(x1+x2)//2} {(y1+y2)//2} size={w}x{h}")
print("DONE")
