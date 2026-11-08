"""MTS Burp Replay — HTTP-клиент с подстановками {{phone}}, {{code}}, {{token}}."""
import copy
import json
import re
from datetime import datetime
from pathlib import Path

import requests
import yaml


def get_by_path(obj, path, default=None):
    """Достать значение из dict по пути 'data.accessToken'."""
    if not path:
        return default
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        else:
            return default
    return cur


def render_template(obj, ctx: dict):
    """Рекурсивно заменить {{key}} в строках dict/list."""
    if isinstance(obj, str):
        out = obj
        for k, v in ctx.items():
            out = out.replace("{{" + k + "}}", str(v if v is not None else ""))
        return out
    if isinstance(obj, dict):
        return {k: render_template(v, ctx) for k, v in obj.items()}
    if isinstance(obj, list):
        return [render_template(v, ctx) for v in obj]
    return obj


class MTSClient:
    def __init__(self, endpoints_path="endpoints.yaml", log_dir="logs"):
        self.cfg_path = Path(endpoints_path)
        with open(self.cfg_path, encoding="utf-8") as f:
            self.cfg = yaml.safe_load(f)

        self.session = requests.Session()
        common = self.cfg.get("common_headers") or {}
        self.session.headers.update(common)

        self.use_proxy = bool(self.cfg.get("use_burp_proxy"))
        self.proxies = (
            {"http": self.cfg.get("burp_proxy"), "https": self.cfg.get("burp_proxy")}
            if self.use_proxy
            else {}
        )
        # verify=False только когда идем через Burp (там свой CA)
        self.verify = (not self.use_proxy) or self.cfg.get("verify_tls_when_no_proxy", True)
        if self.use_proxy:
            self.verify = False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    # ---------- helpers ----------

    @staticmethod
    def normalize_phone(raw: str, phone_format: str = "79XXXXXXXXX") -> str:
        """Привести к формату из Burp. По умолчанию 79XXXXXXXXX (11 цифр)."""
        digits = re.sub(r"\D", "", raw or "")
        if digits.startswith("8") and len(digits) == 11:
            digits = "7" + digits[1:]
        if len(digits) == 10:
            digits = "7" + digits
        if not (len(digits) == 11 and digits.startswith("7")):
            raise ValueError(f"Непохож на российский номер: {raw!r} -> {digits!r}")
        if phone_format.startswith("+"):
            return "+" + digits
        if phone_format == "9XXXXXXXXX":
            return digits[1:]
        return digits  # 79XXXXXXXXX

    def _log(self, name, req_data, resp):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            body = resp.text[:8000]
            try:
                body_json = resp.json()
                body = json.dumps(body_json, ensure_ascii=False, indent=2)[:8000]
            except Exception:
                pass
            (self.log_dir / f"{ts}_{name}.txt").write_text(
                f"=== REQUEST {name} ===\n{json.dumps(req_data, ensure_ascii=False, indent=2)}\n\n"
                f"=== STATUS {resp.status_code} ===\n{body}\n",
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[!] не смог записать лог: {e}")

    def call(self, name: str, ctx: dict):
        """Выполнить запрос из endpoints.yaml по имени секции."""
        spec = self.cfg.get(name)
        if not spec:
            raise KeyError(f"В endpoints.yaml нет секции '{name}'")
        spec = copy.deepcopy(spec)
        method = spec.get("method", "GET").upper()
        url = render_template(spec.get("url"), ctx)
        headers = render_template(spec.get("headers") or {}, ctx)
        json_body = render_template(spec.get("json_body"), ctx) if spec.get("json_body") else None
        params = render_template(spec.get("params"), ctx) if spec.get("params") else None

        req_data = {"method": method, "url": url, "headers": headers,
                    "json": json_body, "params": params}
        resp = self.session.request(
            method, url, headers=headers or None, json=json_body,
            params=params, proxies=self.proxies or None,
            verify=self.verify, timeout=30,
        )
        self._log(name, req_data, resp)
        return resp

    @staticmethod
    def as_json(resp):
        try:
            return resp.json()
        except Exception:
            return {"_raw": resp.text[:2000], "_status": resp.status_code}
