"""Direct CSS injection into a Diamonda-managed Chromium profile via CDP.

This avoids relying on an unpacked browser extension. It only controls the
separate browser profile launched by Diamonda and only injects user-selected
local CSS into supported website tabs.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import websocket

APP_URLS = {
    "youtube": "https://www.youtube.com/",
    "facebook": "https://www.facebook.com/",
    "discord": "https://discord.com/app",
    "spotify": "https://open.spotify.com/",
}
APP_HOSTS = {
    "youtube": ("youtube.com",),
    "facebook": ("facebook.com",),
    "discord": ("discord.com", "discordapp.com"),
    "spotify": ("spotify.com",),
}
STYLE_ID = "diamonda-live-pack"
DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 47832


def _windows_candidates():
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    program = Path(os.environ.get("PROGRAMFILES", r"C:\\Program Files"))
    program_x86 = Path(os.environ.get("PROGRAMFILES(X86)", r"C:\\Program Files (x86)"))
    return [
        ("Google Chrome", local / "Google/Chrome/Application/chrome.exe"),
        ("Google Chrome", program / "Google/Chrome/Application/chrome.exe"),
        ("Google Chrome", program_x86 / "Google/Chrome/Application/chrome.exe"),
        ("Microsoft Edge", local / "Microsoft/Edge/Application/msedge.exe"),
        ("Microsoft Edge", program / "Microsoft/Edge/Application/msedge.exe"),
        ("Microsoft Edge", program_x86 / "Microsoft/Edge/Application/msedge.exe"),
    ]


def find_browser():
    for command, label in (("chrome", "Google Chrome"), ("msedge", "Microsoft Edge"), ("chromium", "Chromium")):
        found = shutil.which(command)
        if found:
            return label, Path(found)
    if os.name == "nt":
        for label, candidate in _windows_candidates():
            if candidate.is_file():
                return label, candidate
    return None, None


class BrowserInjector:
    def __init__(self, base_dir: Path, status_callback=None):
        self.base_dir = Path(base_dir)
        self.profile_dir = self.base_dir / "data" / "browser_profile_cdp"
        self.status_callback = status_callback or (lambda _message: None)
        self.app = None
        self.css = ""
        self.js_scripts = []
        self.pack_id = None
        self.browser_name = None
        self.executable = None
        self.process = None
        self.last_error = None

    @property
    def debug_url(self):
        return f"http://{DEBUG_HOST}:{DEBUG_PORT}"

    def _get_json(self, path, timeout=1.0):
        request = urllib.request.Request(self.debug_url + path, headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _debug_ready(self):
        try:
            self._get_json("/json/version")
            return True
        except Exception:
            return False

    def _wait_debugger(self, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._debug_ready():
                return
            if self.process and self.process.poll() is not None:
                raise RuntimeError("Trình duyệt đã thoát trước khi bật cổng điều khiển CDP.")
            time.sleep(0.25)
        raise RuntimeError(
            "Không kết nối được Chrome DevTools Protocol. Hãy đóng cửa sổ trình duyệt Diamonda cũ "
            "rồi thử lại. Nếu vẫn lỗi, kiểm tra ứng dụng bảo mật/firewall với cổng 47832."
        )

    def _launch(self, url):
        label, executable = find_browser()
        if not executable:
            raise RuntimeError("Không tìm thấy Google Chrome hoặc Microsoft Edge.")
        self.browser_name, self.executable = label, executable
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        args = [
            str(executable),
            f"--user-data-dir={self.profile_dir.resolve()}",
            f"--remote-debugging-address={DEBUG_HOST}",
            f"--remote-debugging-port={DEBUG_PORT}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "--new-window",
            url,
        ]
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        self.process = subprocess.Popen(args, close_fds=True, creationflags=flags)
        self._wait_debugger()

    def _ensure_browser(self, app):
        url = APP_URLS.get(app)
        if not url:
            raise RuntimeError(f"Chưa hỗ trợ website: {app}")
        if not self._debug_ready():
            self._launch(url)
        else:
            self._open_tab(url)
        return url

    def _command(self, ws_url, method, params=None, command_id=1, timeout=4):
        ws = websocket.create_connection(ws_url, timeout=timeout, origin="http://127.0.0.1")
        try:
            ws.send(json.dumps({"id": command_id, "method": method, "params": params or {}}))
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                message = json.loads(ws.recv())
                if message.get("id") == command_id:
                    if "error" in message:
                        raise RuntimeError(message["error"].get("message", "CDP command failed"))
                    return message.get("result", {})
            raise TimeoutError(f"Hết thời gian chờ CDP: {method}")
        finally:
            ws.close()

    def _open_tab(self, url):
        version = self._get_json("/json/version")
        ws_url = version.get("webSocketDebuggerUrl")
        if not ws_url:
            raise RuntimeError("Chrome không cung cấp Browser WebSocket endpoint.")
        self._command(ws_url, "Target.createTarget", {"url": url}, command_id=71)

    @staticmethod
    def _matches(tab_url, app):
        try:
            host = (urlparse(tab_url).hostname or "").lower()
            return any(host == domain or host.endswith("." + domain) for domain in APP_HOSTS.get(app, ()))
        except Exception:
            return False

    @staticmethod
    def _expression(css):
        css_json = json.dumps(css, ensure_ascii=False)
        style_json = json.dumps(STYLE_ID)
        return (
            "(() => {"
            f"const id={style_json};"
            "let el=document.getElementById(id);"
            "if(!el){el=document.createElement('style');el.id=id;(document.head||document.documentElement).appendChild(el);}"
            f"el.textContent={css_json};"
            "return {ok:true,styleId:id};"
            "})()"
        )

    @staticmethod
    def _script_expression(pack_id, script_name, script_text):
        # Scripts are explicitly user-selected local pack assets. Each script must
        # register an optional cleanup callback for safe Unapply.
        key = f"{pack_id}:{script_name}"
        return (
            "(() => {"
            "window.__diamondaMods = window.__diamondaMods || {};"
            f"const key={json.dumps(key)};"
            "if(window.__diamondaMods[key]) return {ok:true,already:true};"
            "window.__diamondaMods[key]=true;"
            "try {"
            f"{script_text}\n"
            "return {ok:true};"
            "} catch(error) { delete window.__diamondaMods[key]; "
            "return {ok:false,error:String(error)}; }"
            "})()"
        )

    def _inject_tab(self, tab, css, js_scripts=None, pack_id=None):
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            return False
        result = self._command(
            ws_url, "Runtime.evaluate",
            {"expression": self._expression(css), "returnByValue": True, "awaitPromise": True},
            command_id=72,
        )
        remote = result.get("result", {})
        if remote.get("subtype") == "error" or remote.get("className") == "Error":
            raise RuntimeError(remote.get("description", "Không thể inject CSS vào tab."))
        if js_scripts and pack_id:
            for script_name, script_text in js_scripts:
                script_result = self._command(
                    ws_url, "Runtime.evaluate",
                    {"expression": self._script_expression(pack_id, script_name, script_text),
                     "returnByValue": True, "awaitPromise": True},
                    command_id=74,
                )
                value = script_result.get("result", {}).get("value", {})
                if isinstance(value, dict) and not value.get("ok", True):
                    raise RuntimeError(f"Lỗi mod {script_name}: {value.get('error', 'không rõ')}")
        return True

    def _remove_tab(self, tab):
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            return False
        expression = (
            "(() => {"
            "const mods=window.__diamondaMods||{};"
            "for(const key of Object.keys(mods)){"
            "if(key.startsWith(" + json.dumps(str(self.pack_id) + ":") + ")){"
            "try{const fn=window.__diamondaCleanup&&window.__diamondaCleanup[key];if(fn)fn();}catch(e){}"
            "delete mods[key];"
            "}}"
            f"const el=document.getElementById({json.dumps(STYLE_ID)});if(el)el.remove();"
            "return true;})()"
        )
        self._command(ws_url, "Runtime.evaluate", {"expression": expression, "returnByValue": True}, command_id=73)
        return True

    def tabs(self):
        return self._get_json("/json/list")

    def sync_once(self):
        if not self.css or not self.app or not self._debug_ready():
            return 0
        count = 0
        errors = []
        for tab in self.tabs():
            if tab.get("type") != "page" or not self._matches(tab.get("url", ""), self.app):
                continue
            try:
                if self._inject_tab(tab, self.css, self.js_scripts, self.pack_id):
                    count += 1
            except Exception as exc:
                errors.append(str(exc))
        if count:
            self.status_callback(f"Đã inject {self.pack_id} vào {count} tab.")
            self.last_error = None
        elif errors:
            self.last_error = errors[0]
            self.status_callback(f"Chưa inject được: {self.last_error}")
        else:
            self.status_callback("Đang chờ tab website tải xong để inject…")
        return count

    def apply(self, app, pack_id, css, js_scripts=None):
        js_scripts = list(js_scripts or [])
        if not css.strip() and not js_scripts:
            raise ValueError("Pack không có CSS hoặc JavaScript để inject.")
        if self.pack_id:
            self.unapply()
        self.app, self.pack_id, self.css = app, pack_id, css or "/* Diamonda functional mod */"
        self.js_scripts = js_scripts
        url = self._ensure_browser(app)
        count = self.sync_once()
        if count:
            return url, count
        self.status_callback("Đã mở website; Diamonda đang chờ trang tải xong để inject.")
        return url, 0

    def unapply(self):
        removed = 0
        if self._debug_ready():
            for tab in self.tabs():
                if tab.get("type") == "page" and self._matches(tab.get("url", ""), self.app):
                    try:
                        if self._remove_tab(tab):
                            removed += 1
                    except Exception:
                        pass
        self.app, self.pack_id, self.css, self.js_scripts = None, None, "", []
        self.status_callback(f"Đã gỡ CSS khỏi {removed} tab.")
        return removed
