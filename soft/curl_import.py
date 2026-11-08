"""Помощник: вставь 'Copy as cURL (bash)' из Burp -> получи YAML-кусок для endpoints.yaml.

Использование:
  python curl_import.py curl.txt
  # или просто запусти и вставь curl в консоль (Ctrl+Z Enter для конца)
"""
import re
import shlex
import sys
import json


def parse_curl(s: str):
    tokens = shlex.split(s, posix=True)
    method = "GET"
    url = ""
    headers = {}
    data = None
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "curl":
            pass
        elif t in ("-X", "--request") and i + 1 < len(tokens):
            method = tokens[i + 1].upper()
            i += 1
        elif t in ("-H", "--header") and i + 1 < len(tokens):
            h = tokens[i + 1]
            if ":" in h:
                k, v = h.split(":", 1)
                headers[k.strip()] = v.strip()
            i += 1
        elif t in ("--data", "--data-raw", "--data-binary", "-d",
                   "--data-urlencode", "--json") and i + 1 < len(tokens):
            data = tokens[i + 1]
            if method == "GET":
                method = "POST"
            i += 1
        elif t.startswith("http"):
            url = t.strip("'\"")
        i += 1
    return method, url, headers, data


def main():
    if len(sys.argv) > 1:
        s = open(sys.argv[1], encoding="utf-8").read()
    else:
        print("Вставь curl из Burp, затем Ctrl+Z + Enter:")
        s = sys.stdin.read()
    s = " ".join(s.split())
    method, url, headers, data = parse_curl(s)
    print("\n# --- вставь в endpoints.yaml ---")
    print(f'method: "{method}"')
    print(f'url: "{url}"')
    if headers:
        print("headers:")
        for k, v in headers.items():
            if k.lower() in ("content-length", "host", "connection",
                             "content-type", "accept-encoding"):
                continue
            print(f'  {k}: "{v}"')
    else:
        print("headers: {}")
    if data:
        try:
            body = json.loads(data)
            print("json_body:")
            print(json.dumps(body, ensure_ascii=False, indent=2))
        except Exception:
            print(f"# raw body (не JSON): {data[:300]}")
    print("# --- конец ---\n")
    print("Подсказка: замени реальные номер/код/токен на {{phone}}/{{code}}/{{token}}.")


if __name__ == "__main__":
    main()
