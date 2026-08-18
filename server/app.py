from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from crypto import decrypt_text, encrypt_text
from state import START_HEROES, SaveStore

HOST = os.getenv("DMC_HOST", "0.0.0.0")
PORT = int(os.getenv("DMC_PORT", "8000"))
SERVER_ID = int(os.getenv("DMC_SERVER_ID", "1"))


def _normalize_user_url(value: str) -> str:
    value = value.rstrip("/")
    if value.lower().endswith("/server/webservice/user.asmx"):
        return value
    return f"{value}/Server/Webservice/User.asmx"


PUBLIC_USER_URL = _normalize_user_url(
    os.getenv("DMC_BASE_URL", f"http://10.0.2.2:{PORT}")
)
PUBLIC_BATTLE_URL = PUBLIC_USER_URL.replace("User.asmx", "Battle.asmx")
DEFAULT_SAVE_FILE = Path(__file__).resolve().parent / "local_data" / "save.json"
STORE = SaveStore(os.getenv("DMC_SAVE_FILE", str(DEFAULT_SAVE_FILE)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dmc-local")


def _battle_vogia(code: str, hp: int) -> dict:
    return {
        "Name": code,
        "Mau": hp,
        "NoiLuc": 0.0,
        "Buffs": [],
        "BuaChu": [],
        "BiThuat": [],
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
        "ErrorMsg": STORE.account_payload().get("DisplayName", "Offline"),
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
    return STORE.user_info_payload()


def _select_start_nhan_vat_response(request: dict) -> dict:
    code = str(request.get("NhanVatCode") or "")
    try:
        STORE.choose_hero(code)
    except ValueError as exc:
        return {"ErrorCode": 0, "ErrorMsg": str(exc)}

    hero = STORE.hero_payload()
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "NhanVat": [hero],
        "DoiHinh": {"Slot1": 1},
    }


def _system_highlight_response(_: dict) -> dict:
    """Compatibility response for HomeForm's runtime highlight request.

    CONFIRMED RUNTIME: HomeForm calls User.asmx/GetSystemHighLight immediately
    after entering Home. The original server is gone, so for offline mode we
    deliberately expose an empty list instead of allowing HTTP 404 to bubble
    into Unity as java.io.FileNotFoundException.

    `SystemHighLightList` is a confirmed client-side symbol. `SystemHighLight`
    is also included as a conservative legacy alias; LitJson ignores fields the
    target DTO does not define.
    """
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "SystemHighLightList": [],
        "SystemHighLight": [],
    }


def _mini_boss_info_response(_: dict) -> dict:
    """Offline-safe empty MiniBoss snapshot.

    CONFIRMED RUNTIME: LuyenCongForm calls Battle.asmx/GetMiniBossInfo. We do
    not fabricate an active event/boss yet; an empty response removes the 404
    while keeping this feature explicitly in compatibility-stub state.
    """
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "MiniBossInfo": None,
        "MiniBoss": None,
        "DanhSachMiniBoss": [],
    }


def _lay_nhan_vat_response(_: dict) -> dict:
    """Minimal deterministic recruit compatibility response.

    The runtime Store/Chợ screen calls User.asmx/LayNhanVat. Full recruit
    tables/cost/randomness are not reconstructed yet. Return the current local
    hero and account snapshot so the client receives a structurally useful
    success payload rather than HTTP 404. No currency is consumed and no new
    character is persisted at this stage.
    """
    hero = STORE.hero_payload()
    nhan_vat = [hero] if hero else []
    return {
        "ErrorCode": 1,
        "ErrorMsg": "",
        "NhanVat": nhan_vat,
        "Account": STORE.account_payload(),
        "UpdateUserInfo": {
            "Account": STORE.account_payload(),
            "NhanVat": nhan_vat,
        },
    }


def _giang_ho_response(request: dict) -> dict:
    giang_ho_idx = int(request.get("giangHoIdx", request.get("GiangHoIdx", 0)) or 0)
    nhiem_vu_idx = int(request.get("nhiemVuIdx", request.get("NhiemVuIdx", 0)) or 0)

    player_code = STORE.hero_code
    if not player_code or player_code not in START_HEROES:
        return {"ErrorCode": 0, "ErrorMsg": "No offline character selected"}

    enemy_code = (
        "NV_PhongThanhDuong"
        if player_code != "NV_PhongThanhDuong"
        else "NV_LenhHoXung"
    )
    player_hp = START_HEROES[player_code]["Mau"]
    enemy_hp = 100
    star = 3
    reward_bac = 100

    try:
        STORE.complete_giangho_battle(giang_ho_idx, nhiem_vu_idx, star)
        STORE.add_bac(reward_bac)
        STORE.save()
    except ValueError as exc:
        return {"ErrorCode": 0, "ErrorMsg": str(exc)}

    replay = {
        "BuaChuBiThuatMP1": [],
        "BuaChuBiThuatMP2": [],
        "DoiThang": 0,
        "Team1": {
            "Name": STORE.account_payload().get("DisplayName", "Offline"),
            "AccountID": "offline-user",
            "DanhVong": 0,
        },
        "Team2": {"Name": "Đối thủ", "AccountID": "npc", "DanhVong": 0},
        "Hiep1": {
            "DoiHinh1": [_battle_vogia(player_code, player_hp)],
            "DoiHinh2": [_battle_vogia(enemy_code, enemy_hp)],
            "LuotDau": [
                {
                    "DoiTanCong": 0,
                    "NguoiTanCong": 0,
                    "DanhSachThuongTon": [
                        {"Value": enemy_hp, "TrangThaiThuongTon": []}
                    ],
                    "VoCong": "",
                }
            ],
        },
        "Hiep2": None,
        "Hiep3": None,
    }

    return {
        "giangHoIdx": giang_ho_idx,
        "nhiemVuIdx": nhiem_vu_idx,
        "star": star,
        "BattleReplay": replay,
        "Reward": {
            "Bac": reward_bac,
            "Vang": 0,
            "ExpMonPhai": 10,
            "ExpNhanVat": 10,
            "Items": [],
        },
        "UpdateUserInfo": {
            "Account": STORE.account_payload(),
            "NhanVat": [STORE.hero_payload()],
            "GiangHo": STORE.giangho_payload(),
        },
        "ErrorCode": 1,
        "ErrorMsg": "",
    }


ROUTES = {
    "login": _login_response,
    "checkuser": _check_user_response,
    "getuserinfo": _get_user_info_response,
    "selectstartnhanvat": _select_start_nhan_vat_response,
    "getsystemhighlight": _system_highlight_response,
    "getminibossinfo": _mini_boss_info_response,
    "laynhanvat": _lay_nhan_vat_response,
    "giangho": _giang_ho_response,
}


class DMCHandler(BaseHTTPRequestHandler):
    server_version = "DMCOffline/0.5"

    def log_message(self, fmt: str, *args: object) -> None:
        log.info("%s - %s", self.client_address[0], fmt % args)

    def _send_plain(
        self,
        status: int,
        body: str,
        content_type: str = "text/plain; charset=utf-8",
    ) -> None:
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/")
        if path in {"", "/health"}:
            self._send_plain(
                200,
                json.dumps(
                    {
                        "ok": True,
                        "service": "DaiMinhChu-Offline",
                        "user_url": PUBLIC_USER_URL,
                        "battle_url": PUBLIC_BATTLE_URL,
                        "save_file": str(STORE.path),
                        "has_character": bool(STORE.hero_code),
                    },
                    ensure_ascii=False,
                ),
                "application/json; charset=utf-8",
            )
            return
        self._send_plain(404, "not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed_path = urlparse(self.path).path.rstrip("/")
        route_name = parsed_path.rsplit("/", 1)[-1].lower()
        handler = ROUTES.get(route_name)
        if handler is None:
            log.warning("Unhandled route: %s", parsed_path)
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
        response_json = json.dumps(
            response_obj, ensure_ascii=False, separators=(",", ":")
        )
        response_cipher = encrypt_text(response_json)
        log.info("%s response: %s", parsed_path, response_json)
        self._send_plain(200, response_cipher)


def main() -> None:
    log.info("Starting Dai Minh Chu local compatibility server")
    log.info("Listen: http://%s:%s", HOST, PORT)
    log.info("Advertised User.asmx: %s", PUBLIC_USER_URL)
    log.info("Derived Battle.asmx: %s", PUBLIC_BATTLE_URL)
    log.info("Save file: %s", STORE.path)
    log.info(
        "Routes: Login, CheckUser, GetUserInfo, SelectStartNhanVat, "
        "GetSystemHighLight, GetMiniBossInfo, LayNhanVat, GiangHo"
    )
    ThreadingHTTPServer((HOST, PORT), DMCHandler).serve_forever()


if __name__ == "__main__":
    main()
