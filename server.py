#!/usr/bin/env python3
"""myHomePage 静态服务器 + 网站图标(favicon)代理缓存

用法:
    python3 server.py [端口]        # 默认 43210
特性:
    - 静态托管当前目录
    - GET /favicon/?u=<scheme://host>  代理抓取该站点的真实网页图标并缓存到
      ~/.cache/myhomepage-favicons/
    - 只允许抓取 index.html 中 APPS 数组里的站点（自动解析，防 SSRF）
"""
import re
import sys
import socket
import urllib.request
import urllib.parse
import urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = Path.home() / ".cache" / "myhomepage-favicons"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0 myHomePage-favicon/1.0"
TIMEOUT = 7


def load_allowlist():
    """从 index.html 的 APPS 数组解析允许抓图标的站点，避免开放代理。"""
    origins = set()
    html = (ROOT / "index.html").read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"url\s*:\s*'((?:https?://)[^']+)'", html):
        try:
            p = urllib.parse.urlparse(m.group(1))
            if p.scheme in ("http", "https") and p.netloc:
                origins.add(f"{p.scheme}://{p.netloc}")
        except Exception:
            pass
    return origins


ALLOWED = load_allowlist()


def sniff(data, fallback=""):
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return "image/webp"
    if data.startswith(b"\x00\x00\x01\x00"):
        return "image/x-icon"
    head = data[:300].lstrip().lower()
    if head.startswith(b"<svg") or b"<svg" in head:
        return "image/svg+xml"
    return fallback


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = r.read(1024 * 1024)
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
            return data, ctype
    except Exception:
        return None, None


def resolve_icon(scheme, host):
    """先试 /favicon.ico，失败再解析首页 HTML 里的 icon 链接。"""
    data, ctype = fetch(f"{scheme}://{host}/favicon.ico")
    if data and len(data) > 64:
        t = sniff(data, ctype)
        if t and (t.startswith("image/") or ctype.startswith("image/")):
            return data, t
    data, _ = fetch(f"{scheme}://{host}/")
    if data:
        try:
            html = data.decode("utf-8", "ignore")
        except Exception:
            html = ""
        for m in re.finditer(r"<link\b[^>]*>", html, re.I):
            tag = m.group(0)
            rel = re.search(r"rel\s*=\s*[\"']([^\"']*)[\"']", tag, re.I)
            if not rel or "icon" not in rel.group(1).lower():
                continue
            href = re.search(r"href\s*=\s*[\"']([^\"']+)[\"']", tag, re.I)
            if not href:
                continue
            href = href.group(1)
            if href.startswith("//"):
                url = scheme + ":" + href
            elif href.startswith("/"):
                url = f"{scheme}://{host}{href}"
            elif href.startswith(("http://", "https://")):
                url = href
            else:
                url = f"{scheme}://{host}/{href}"
            data, ctype = fetch(url)
            if data and len(data) > 64:
                t = sniff(data, ctype)
                if t and (t.startswith("image/") or ctype.startswith("image/")):
                    return data, t
    return None, None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/favicon/":
            qs = urllib.parse.parse_qs(parsed.query)
            u = (qs.get("u") or [""])[0]
            if u not in ALLOWED:
                self.send_error(400, "host not allowed")
                return
            p = urllib.parse.urlparse(u)
            key = re.sub(r"[^A-Za-z0-9._-]", "_", f"{p.scheme}_{p.netloc}")[:120]
            f = CACHE / key
            if not f.exists():
                data, ctype = resolve_icon(p.scheme, p.netloc)
                if not data:
                    self.send_error(404, "favicon not found")
                    return
                f.write_bytes(data)
            data = f.read_bytes()
            ctype = sniff(data, "image/x-icon")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=604800")
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        pass  # 静默日志


class HTTPServerV6(ThreadingHTTPServer):
    address_family = socket.AF_INET6


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 43210
    HTTPServerV6.allow_reuse_address = True
    srv = HTTPServerV6(("::", port), Handler)
    print(f"myHomePage: http://[::]:{port}/  (含 /favicon/ 图标代理，已缓存目录 {CACHE})", flush=True)
    srv.serve_forever()
