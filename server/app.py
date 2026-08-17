from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from dmc_crypto import decrypt_text, encrypt_text

HOST = os.getenv("DMC_HOST", "0.0.0.0")
PORT = int(os.getenv("DMC_PORT", "8000"))
BASE_URL = os.getenv("DMC_BASE_URL", f"http://127.0.0.1:{PORT}").rstrip("/")
SERVER_ID = int(os.getenv("DMC_SERVER_ID", "1"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("dmc-local")


def _login_response(_: dict) -> dict:
    return {
        "ListUserServer": [SERVER_ID],
        "ErrorCode": 1,
        "Token": "offline-token",
        "UserId": "offline-user",
        "SohaToken": "",
        "Servers": [
            {
                "ServerID": SERVER_ID,
                "Name": "Offline",
                "Url": BASE_URL,
                "Status": "online",
            }
        ],
        "ErrorMsg": "Offline",
        "UrlUpdateAndroid": "",
        "UrlIphoneAppstore": "",
        "UrlIphoneJb": "",
        "UrlWPJb": "",
        # Important: null skips remote config AssetBundle download in client.
        "LoginCfg": None,
    }


def _check_user_response(_: dict) -> dict:
    return {
        "LoginMessage": [],
        "EventAnGaLuotCount": 0,
        "ErrorCode": 1,
        "Aid": 1,
        "UserInfo": None,
        "ErrorMsg": "",
        "ServerID": SERVER_ID,
    }


def _get_user_info_response(_: dict) -> dict:
    # First milestone intentionally returns zero heroes so the client follows
    # its built-in "new account / choose starting character" branch.
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "Account": {
            "DisplayName": "Offline",
            "Level": 1,
        },
        "GiaTriThoiGian": {
            "TimeServer": now,
            "LatTheBai": 0,
        },
        "NhanVat": [],
    }


ROUTES = {
    "login": _login_response,
    "checkuser": _check_user_response,
    "getuserinfo": _get_user_info_response,
}


class DMCHandler(BaseHTTPRequestHandler):
    server_version = "DMCOffline/0.1"

    def log_message(self, fmt: str, *args) -> None:
        log.info("%s - %s", self.client_address[0], fmt % args)

    def _send_plain(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/")
        if path == "/health":
            self._send_plain(
                200,
                json.dumps(
                    {
                        "ok": True,
                        "service": "DaiMinhChu-Offline",
                        "base_url": BASE_URL,
                    },
                    ensure_ascii=False,
                ),
                "application/json; charset=utf-8",
            )
            return

        self._send_plain(404, "not found")

    def do_POST(self) -> None:
        parsed_path = urlparse(self.path).path.rstrip("/")
        route_name = parsed_path.rsplit("/", 1)[-1].lower()

        handler = ROUTES.get(route_name)
        if handler is None:
            self._send_plain(404, "not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(raw_body, keep_blank_values=True)
        encrypted = form.get("data", [None])[0]

        if not encrypted:
            log.warning("%s: missing data= field; raw=%r", parsed_path, raw_body[:500])
            self._send_plain(400, "missing data")
            return

        try:
            plaintext = decrypt_text(encrypted)
            request_obj = json.loads(plaintext)
        except Exception as exc:
            log.exception("%s: decrypt/JSON failed", parsed_path)
            self._send_plain(400, f"bad request: {exc}")
            return

        log.info("%s request: %s", parsed_path, json.dumps(request_obj, ensure_ascii=False))

        response_obj = handler(request_obj)
        response_json = json.dumps(response_obj, ensure_ascii=False, separators=(",", ":"))
        response_cipher = encrypt_text(response_json)

        log.info("%s response: %s", parsed_path, response_json)
        self._send_plain(200, response_cipher)


def main() -> None:
    log.info("Starting DaiMinhChu local compatibility server")
    log.info("Listen: http://%s:%s", HOST, PORT)
    log.info("Advertised lobby URL: %s", BASE_URL)
    ThreadingHTTPServer((HOST, PORT), DMCHandler).serve_forever()


if __name__ == "__main__":
    main()
