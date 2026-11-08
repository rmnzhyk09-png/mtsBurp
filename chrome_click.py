"""Клик по кнопке Продолжить через DevTools + скриншот через adb."""
import asyncio
import json
import sys
import os
import urllib.request

import websockets

BASE = os.path.dirname(os.path.abspath(__file__))


def api(path):
    with urllib.request.urlopen("http://127.0.0.1:9222" + path, timeout=15) as r:
        return json.loads(r.read().decode())


async def main():
    tabs = api("/json/list")
    page = next(t for t in tabs if t.get("type") == "page" and "mtsdengi" in t.get("url", ""))
    print("tab:", page.get("url", "")[:90], flush=True)
    async with websockets.connect(page["webSocketDebuggerUrl"], max_size=50_000_000) as ws:
        seq = [0]

        async def call(method, params=None):
            seq[0] += 1
            await ws.send(json.dumps({"id": seq[0], "method": method, "params": params or {}}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == seq[0]:
                    return msg.get("result", {})

        js = """(() => {
          const btns = [...document.querySelectorAll('button, a')];
          const b = btns.find(x => /продолжить/i.test(x.textContent));
          if (!b) return 'NOTFOUND:' + btns.map(x => x.textContent.trim().slice(0,30)).join('|');
          b.scrollIntoView(); b.click();
          return 'CLICKED:' + b.textContent.trim().slice(0,30);
        })()"""
        ev = await call("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print("click:", ev.get("result", {}).get("value"), flush=True)

asyncio.run(main())
print("DONE", flush=True)
