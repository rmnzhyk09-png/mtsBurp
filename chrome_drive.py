"""Едем вкладкой Chrome: открыть URL, скриншот, HTML. Аргументы: URL [выходной_префикс]."""
import asyncio
import base64
import json
import sys
import os
import urllib.request

import websockets

BASE = os.path.dirname(os.path.abspath(__file__))
URL = sys.argv[1] if len(sys.argv) > 1 else "https://login.mts.ru/amserver/NUI/?client_id=My_MTS"
PREFIX = sys.argv[2] if len(sys.argv) > 2 else "qrator_page"


def api(path, data=None):
    req = urllib.request.Request(
        "http://127.0.0.1:9222" + path,
        data=json.dumps(data).encode() if data is not None else None,
        method="PUT" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


async def main():
    tabs = api("/json/list")
    page = next(t for t in tabs if t.get("type") == "page")
    ws_url = page["webSocketDebuggerUrl"]
    print("tab:", page.get("url", "")[:80], flush=True)
    async with websockets.connect(ws_url, max_size=50_000_000) as ws:
        seq = [0]

        async def call(method, params=None):
            seq[0] += 1
            await ws.send(json.dumps({"id": seq[0], "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == seq[0]:
                    return msg.get("result", {})

        await call("Page.navigate", {"url": URL})
        await asyncio.sleep(12)
        shot = await call("Page.captureScreenshot", {"format": "png"})
        open(f"{BASE}\\{PREFIX}.png", "wb").write(base64.b64decode(shot["data"]))
        print("screenshot saved", flush=True)
        ev = await call("Runtime.evaluate", {
            "expression": "document.title + ' ||| ' + document.documentElement.outerHTML.length",
            "returnByValue": True})
        print("title+len:", ev.get("result", {}).get("value"), flush=True)
        html = await call("Runtime.evaluate", {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True})
        open(f"{BASE}\\{PREFIX}.html", "w", encoding="utf-8").write(
            html.get("result", {}).get("value", ""))
        print("html saved", flush=True)
        srcs = await call("Runtime.evaluate", {
            "expression": "[...document.scripts].map(s=>s.src).filter(Boolean).join('\\n')",
            "returnByValue": True})
        scripts = (srcs.get("result", {}).get("value", "") or "").split("\n")
        open(f"{BASE}\\{PREFIX}_scripts.txt", "w", encoding="utf-8").write("\n".join(scripts))
        print(f"scripts: {len(scripts)}", flush=True)
        for s in scripts[:20]:
            print("  JS:", s[:130], flush=True)

asyncio.run(main())
print("DONE", flush=True)
