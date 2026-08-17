from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from crypto import decrypt_text, encrypt_text

HOST = os.getenv("DMC_HOST", "0.0.0.0")
PORT = int(os.getenv("DMC_PORT", "8000"))
SERVER_ID = int(os.getenv("DMC_SERVER_ID", "1"))


def _normalize_user_url(value: str) -> str:
    value = value.rstrip("/")
    if value.lower().endswith("/server/webservice/user.asmx"):
        return value
    return f"{value}/Server/Webservice/User.asmx"


# Android Emulator normally reaches the host PC through 10.0.2.2.
# Override this with the PC LAN IP for a real phone/tablet.
PUBLIC_USER_URL = _normalize_user_url(
    os.getenv("DMC_BASE_URL", f"http://10.0.2.2:{PORT}")
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dmc-local")

START_HEROES = {
    # Base stats are CONFIRMED from the embedded ConfigFile/NhanVat TextAsset.
    "NV_PhongThanhDuong": {"Mau": 260, "Cong": 284, "Thu": 155, "Noicong": 234},
    "NV_LenhHoXung": {"Mau": 180, "Cong": 180, "Thu": 60, "Noicong": 300},
    "NV_SoLuuHuong": {"Mau": 250, "Cong": 150, "Thu": 160, "Noicong": 305},
}


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
                "Url": PUBLIC_USER_URL,
                "Status": "online",
            }
        ],
        "ErrorMsg": "Offline Player",
        # null makes GameManager.DownloadConfigAndCache() skip remote config
        # download. Core configs were already loaded from Resources in Awake().
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
    # Milestone flow deliberately starts with zero heroes. This routes the
    # client to BeginCutsceneForm (Form index 13) and its built-in choice of
    # three starting characters.
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "Account": {
            "DisplayName": "Offline",
            "Level": 1,
            "Exp": 0,
            "ExpMax": 100,
            "Bac": 10000,
            "Vang": 100,
            "Vip": 0,
        },
        "GiaTriThoiGian": {
            "LuotNV": 20,
            "LuotNVMax": 20,
            "LuotTD": 10,
            "LuotTDMax": 10,
            "LatTheBai": 0,
        },
        "NhanVat": [],
    }


def _select_start_nhan_vat_response(request: dict) -> dict:
    code = str(request.get("NhanVatCode") or "")
    stats = START_HEROES.get(code)
    if stats is None:
        return {
            "ErrorCode": 0,
            "ErrorMsg": f"Unsupported start character: {code}",
        }

    hero = {
        "Id": 1,
        "Name": code,
        "Level": 1,
        "Exp": 0,
        "ExpMax": 100,
        "Mau": stats["Mau"],
        "Cong": stats["Cong"],
        "Thu": stats["Thu"],
        "Noicong": stats["Noicong"],
        "VoCong1Level": 1,
        "KyNgoCocLevel": 1,
    }

    # WaitForSelectStartNhanVat deserializes this as HTTPGetUserInfoResponse,
    # then HTTPUserInfo.UpdateData() replaces NhanVat when Count > 0 and DoiHinh
    # when Slot1 > -1. HomeForm can therefore resolve the selected hero by ID.
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "NhanVat": [hero],
        "DoiHinh": {"Slot1": 1},
    }


ROUTES = {
    "login": _login_response,
    "checkuser": _check_user_response,
    "getuserinfo": _get_user_info_response,
    "selectstartnhanvat": _select_start_nhan_vat_response,
}


class DMCHandler(BaseHTTPRequestHandler):
    server_version = "DMCOffline/0.2"

    def log_message(self, fmt: str, *args: object) -> None:
        log.info("%s - %s", self.client_address[0], fmt % args)

    def _send_plain(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlparse(self.path).path.rstrip("/")
        if path in {"", "/health"}:
            self._send_plain(
                200,
                json.dumps(
                    {
                        "ok": True,
                        "service": "DaiMinhChu-Offline",
                        "user_url": PUBLIC_USER_URL,
                    },
                    ensure_ascii=False,
                ),
                "application/json; charset=utf-8",
            )
            return
        self._send_plain(404, "not found")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed_path = urlparse(self.path).path.rstrip("/")
        route_name = parsed_path.rsplit("/", 1)[-1].lower()
        handler = ROUTES.get(route_name)
        if handler is None:
            self._send_plain(404, "not found")
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
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
    log.info("Advertised User.asmx: %s", PUBLIC_USER_URL)
    log.info("Routes: Login, CheckUser, GetUserInfo, SelectStartNhanVat")
    ThreadingHTTPServer((HOST, PORT), DMCHandler).serve_forever()


if __name__ == "__main__":
    main()
