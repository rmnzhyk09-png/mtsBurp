"""Клик Продолжить + диагностика: URL и текст после."""
import asyncio
import json
import urllib.request

import websockets


def api(path):
    with urllib.request.urlopen("http://127.0.0.1:9222" + path, timeout=15) as r:
        return json.loads(r.read().decode())


async def main():
    tabs = api("/json/list")
    page = next(t for t in tabs if t.get("type") == "page" and "mtsdengi" in t.get("url", ""))
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
          if (!b) return 'NOBTN';
          const r = b.getBoundingClientRect();
          const info = 'btn rect=' + JSON.stringify({x:r.x,y:r.y,w:r.width,h:r.height}) +
            ' disabled=' + b.disabled + ' href=' + (b.href||'-');
          b.scrollIntoView({block:'center'});
          b.click();
          return info;
        })()"""
        ev = await call("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print("click:", ev.get("result", {}).get("value"), flush=True)
        await asyncio.sleep(8)
        ev2 = await call("Runtime.evaluate", {
            "expression": "location.href + ' ||| ' + document.title + ' ||| ' + document.body.innerText.slice(0,200)",
            "returnByValue": True})
        print("after:", ev2.get("result", {}).get("value"), flush=True)

asyncio.run(main())
print("DONE", flush=True)
