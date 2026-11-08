"""Координаты кликабельных элементов из uiautomator-дампа."""
import xml.etree.ElementTree as ET
import os
import re

f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.xml")
root = ET.parse(f).getroot()
for node in root.iter("node"):
    text = node.get("text", "") or ""
    desc = node.get("content-desc", "") or ""
    clickable = node.get("clickable") == "true"
    if clickable and (text.strip() or desc.strip()):
        b = node.get("bounds", "")
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            print(f"{(text or desc)[:50]!r} -> tap {(x1+x2)//2} {(y1+y2)//2}")
print("DONE")
