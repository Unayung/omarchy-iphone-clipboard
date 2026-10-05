#!/usr/bin/env python3
# iPhone ⇄ Omarchy 剪貼簿。iPhone 捷徑 POST 寫入、GET 取回，這裡用 wl-copy / wl-paste 對接。
# 只綁 Tailscale IP；token 第一次跑時產生在 ~/.config/iphone-clipboard/token，捷徑用 X-Token 或 ?t= 帶上。
#   clip-server.py         跑伺服器
#   clip-server.py url     印出安裝頁網址（面板拿去做 QR code）
import html, os, secrets, subprocess, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

HERE = Path(__file__).resolve().parent
CONF = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "iphone-clipboard"
PORT = int(os.environ.get("CLIP_PORT", 8766))
MAX = 50 << 20
SHORTCUTS = {"send": "傳到電腦.shortcut", "fetch": "從電腦拿.shortcut"}


def token():
    f = CONF / "token"
    if not f.exists():
        CONF.mkdir(parents=True, exist_ok=True)
        f.touch(mode=0o600)
        f.write_text(secrets.token_hex(16))
    return f.read_text().strip()


def tailscale_ip(wait):
    while True:  # 開機時 tailscaled 可能還沒好
        r = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.split()[0]
        if not wait:
            sys.exit("tailscale 沒有 IPv4 位址")
        time.sleep(10)


def run(*cmd, data=None):
    return subprocess.run(cmd, input=data, capture_output=True).stdout


class H(BaseHTTPRequestHandler):
    def log_request(self, code="-", size="-"):  # 不把 ?t=token 寫進 journal
        self.log_message('"%s %s" %s', self.command, urlparse(self.path).path, code)

    def authed(self):
        q = parse_qs(urlparse(self.path).query).get("t", [""])[0]
        return secrets.compare_digest(self.headers.get("X-Token") or q, TOKEN)

    def reply(self, code, body=b"", mime="text/plain; charset=utf-8", headers=()):
        self.send_response(code)
        for h in headers:
            self.send_header(*h)
        if body:
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # iPhone → 電腦
        n = int(self.headers.get("Content-Length") or 0)
        if not self.authed():
            return self.reply(403)
        if not 0 < n <= MAX:
            return self.reply(413 if n else 400)
        body = self.rfile.read(n)
        subprocess.run(["wl-copy"], input=body, check=True)
        is_text = run("wl-paste", "-l").decode().startswith("text/")
        preview = body.decode(errors="replace")[:80] if is_text else f"圖片／檔案 {n // 1024} KB"
        subprocess.run(["notify-send", "-a", "iPhone 剪貼簿", "已收到 iPhone 剪貼簿", preview])
        self.reply(204)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/shortcuts/"):  # 通用捷徑檔，不含任何機密
            name = SHORTCUTS.get(path.removeprefix("/shortcuts/"))
            if not name or not (HERE / "shortcuts" / name).exists():  # 還沒在 Mac 上簽名
                return self.reply(404)
            return self.reply(200, (HERE / "shortcuts" / name).read_bytes(), "application/octet-stream",
                              [("Content-Disposition", f"attachment; filename*=UTF-8''{quote(name)}")])
        if not self.authed():
            return self.reply(403)
        if path == "/install":
            return self.reply(200, install_page().encode(), "text/html; charset=utf-8")
        # 電腦 → iPhone：有圖給圖，沒圖給文字
        types = run("wl-paste", "-l").decode().split()
        mime = "image/png" if "image/png" in types else next((t for t in types if t.startswith("image/")), None)
        body = run("wl-paste", "-t", mime) if mime else (run("wl-paste", "-n") if types else b"")
        self.reply(200, body, mime or "text/plain; charset=utf-8") if body else self.reply(204)


def install_page():
    url = html.escape(f"http://{IP}:{PORT}/?t={TOKEN}")
    links = "".join(f'<a class="btn" href="/shortcuts/{k}">{html.escape(v.removesuffix(".shortcut"))}</a>'
                    for k, v in SHORTCUTS.items())
    return f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>iPhone 剪貼簿</title>
<style>body{{font:17px -apple-system,sans-serif;padding:20px;max-width:560px;margin:auto}}
.btn{{display:block;margin:12px 0;padding:16px;border-radius:12px;background:#0a84ff;color:#fff;text-decoration:none;text-align:center}}
input{{width:100%;box-sizing:border-box;font:15px ui-monospace,monospace;padding:12px;border-radius:10px;border:1px solid #888}}
button{{width:100%;margin-top:8px;padding:12px;border-radius:10px;border:0;background:#30d158;color:#fff;font-size:17px}}
ol{{padding-left:20px;line-height:1.6}}</style>
<h2>{html.escape(os.uname().nodename)}</h2>
<p>1. 先複製這台電腦的網址，匯入捷徑時會問：</p>
<input id="u" readonly value="{url}"><button onclick="u.select();document.execCommand('copy');this.textContent='已複製'">複製網址</button>
<p>2. 安裝兩個捷徑，匯入時貼上網址：</p>{links}
<ol start="3"><li>設定 → 輔助使用 → 觸控 → 背面輕點：點兩下選「傳到電腦」、點三下選「從電腦拿」</li>
<li>第一次執行時，允許讀取剪貼簿選「永遠允許」</li></ol>"""


TOKEN = token()
if __name__ == "__main__":
    IP = os.environ.get("CLIP_BIND") or tailscale_ip(wait=sys.argv[1:] != ["url"])
    if sys.argv[1:] == ["url"]:
        print(f"http://{IP}:{PORT}/install?t={TOKEN}")
    else:
        ThreadingHTTPServer((IP, PORT), H).serve_forever()
