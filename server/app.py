from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from crypto import decrypt_text, encrypt_text
from gm import gm_html, handle_gm_api
from state import START_HEROES, SaveStore

HOST = os.getenv("DMC_HOST", "0.0.0.0")
PORT = int(os.getenv("DMC_PORT", "8000"))
SERVER_ID = int(os.getenv("DMC_SERVER_ID", "1"))


def _normalize_user_url(value: str) -> str:
    value = value.rstrip("/")
    if value.lower().endswith("/server/webservice/user.asmx"):
        return value
    return f"{value}/Server/Webservice/User.asmx"


PUBLIC_USER_URL = _normalize_user_url(os.getenv("DMC_BASE_URL", f"http://10.0.2.2:{PORT}"))
PUBLIC_BATTLE_URL = PUBLIC_USER_URL.replace("User.asmx", "Battle.asmx")
DEFAULT_SAVE_FILE = Path(__file__).resolve().parent / "local_data" / "save.json"
STORE = SaveStore(os.getenv("DMC_SAVE_FILE", str(DEFAULT_SAVE_FILE)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("dmc-local")


def _battle_vogia(code: str, hp: int) -> dict:
    return {"Name": code, "Mau": hp, "NoiLuc": 0.0, "Buffs": [], "BuaChu": [], "BiThuat": []}


def _login_response(_: dict) -> dict:
    return {"ListUserServer": [SERVER_ID], "ErrorCode": 1, "Token": "offline-token", "UserId": "offline-user", "SohaToken": "",
            "Servers": [{"ServerID": SERVER_ID, "Name": "Offline", "Url": PUBLIC_USER_URL, "Status": "online"}],
            "ErrorMsg": STORE.account_payload().get("DisplayName", "Offline"), "LoginCfg": None}


def _check_user_response(_: dict) -> dict:
    return {"LoginMessage": [], "EventAnGaLuotCount": 0, "ErrorCode": 1, "Aid": 1, "UserInfo": None, "ErrorMsg": "", "ServerID": SERVER_ID}


def _get_user_info_response(_: dict) -> dict:
    return STORE.user_info_payload()


def _select_start_nhan_vat_response(request: dict) -> dict:
    try:
        STORE.choose_hero(str(request.get("NhanVatCode") or ""))
    except ValueError as exc:
        return {"ErrorCode": 0, "ErrorMsg": str(exc)}
    return {"ErrorCode": 1, "ErrorMsg": "", "NhanVat": STORE.all_heroes_payload(), "DoiHinh": {"Slot1": 1}}


def _system_highlight_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "SystemHighLightList": [], "SystemHighLight": []}


def _mini_boss_info_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "MiniBossInfo": None, "MiniBoss": None, "DanhSachMiniBoss": []}


def _pick_recruit_code() -> str:
    owned = {str(x.get("Name")) for x in STORE.all_heroes_payload() if isinstance(x, dict)}
    for code in START_HEROES:
        if code not in owned:
            return code
    return next(iter(START_HEROES))


def _lay_nhan_vat_response(_: dict) -> dict:
    # Runtime evidence: WaitForLayNhanVat passes a returned string into
    # BigNhanVatAvatar.SetByName; empty/invalid code caused KeyNotFoundException.
    code = _pick_recruit_code()
    owned = {str(x.get("Name")) for x in STORE.all_heroes_payload() if isinstance(x, dict)}
    if code not in owned:
        stats = START_HEROES[code]
        STORE.gm_add_hero({
            "Name": code, "Level": 1, "Exp": 0, "ExpMax": 100,
            "Mau": stats["Mau"], "Cong": stats["Cong"], "Thu": stats["Thu"],
            "Noicong": stats["Noicong"], "VoCong1Level": 1, "KyNgoCocLevel": 1,
        })
    return {
        "ErrorCode": 1,
        "ErrorMsg": code,
        "errorCode": 1,
        "errorMsg": code,
        "CodeName": code,
        "code_name": code,
        "NhanVatCode": code,
        "nhanVatCode": code,
        "TanHonCount": 0,
        "tanHonCount": 0,
        "tan_hon_count": 0,
        "ListEventHon": [],
        "listEventHon": [],
        "GetIdx": 0,
        "NhanVat": STORE.all_heroes_payload(),
        "Account": STORE.account_payload(),
        "UpdateUserInfo": STORE.user_info_payload(),
    }


def _empty_feature_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "errorCode": 1, "errorMsg": "",
            "List": [], "Items": [], "Data": [], "Result": []}


def _get_info_lien_minh_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "errorCode": 1, "errorMsg": "",
            "LienMinh": None, "InfoLienMinh": None, "ThanhVien": [],
            "DanhSachThanhVien": [], "Account": STORE.account_payload()}


def _chat_get_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "errorCode": 1, "errorMsg": "",
            "chatQuery": [], "Chat": [], "Chats": [], "Messages": [], "ListChat": []}


def _event_info_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "errorCode": 1, "errorMsg": "",
            "Info": None, "List": [], "Items": [], "Top": [], "Reward": []}


def _buy_user_info_response(_: dict) -> dict:
    return STORE.user_info_payload()


def _refresh_diem_luan_kiem_response(_: dict) -> dict:
    return {"DiemTichLuy": 0, "LastTimeGetDiem": 0, "ErrorCode": 1, "ErrorMsg": ""}


def _get_info_bang_chien_response(_: dict) -> dict:
    return {"timeBangChien": 0, "giaiBangChien": [], "boTranBangChien": [],
            "ErrorCode": 1, "ErrorMsg": ""}


def _find_lien_minh_response(_: dict) -> dict:
    return {"danhSachLM": [], "errorCode": 1, "errorMsg": "", "ErrorCode": 1, "ErrorMsg": ""}


def _get_thanh_vien_lien_minh_response(_: dict) -> dict:
    return {"danhSachThanhVien": [], "danhSachXinGiaNhap": [],
            "errorCode": 1, "errorMsg": "", "ErrorCode": 1, "ErrorMsg": ""}


def _giangho_enemy(chapter_idx: int, mission_idx: int, player_code: str) -> tuple[str, int]:
    """Use only embedded starter codes we know are valid, but vary by stage.

    This is still a compatibility fixture, not the original stage roster.
    """
    codes = list(START_HEROES)
    start = (chapter_idx * 7 + mission_idx) % len(codes)
    for offset in range(len(codes)):
        code = codes[(start + offset) % len(codes)]
        if code != player_code:
            return code, int(START_HEROES[code]["Mau"])
    code = codes[start]
    return code, int(START_HEROES[code]["Mau"])


def _giang_ho_response(request: dict) -> dict:
    giang_ho_idx = int(request.get("giangHoIdx", request.get("GiangHoIdx", 0)) or 0)
    nhiem_vu_idx = int(request.get("nhiemVuIdx", request.get("NhiemVuIdx", 0)) or 0)
    player_code = STORE.hero_code
    if not player_code or player_code not in START_HEROES:
        return {"ErrorCode": 0, "ErrorMsg": "No offline character selected"}

    enemy_code, enemy_hp = _giangho_enemy(giang_ho_idx, nhiem_vu_idx, player_code)
    player_hp = int(START_HEROES[player_code]["Mau"])
    star = 3

    # Reward now persists instead of being display-only. Values scale gently by
    # stage until original reward tables are reverse-mapped from config.
    reward_bac = 100 + giang_ho_idx * 25 + nhiem_vu_idx * 10
    reward_mon_phai_exp = 10 + giang_ho_idx + nhiem_vu_idx
    reward_hero_exp = 10 + giang_ho_idx + nhiem_vu_idx

    try:
        STORE.complete_giangho_battle(giang_ho_idx, nhiem_vu_idx, star)
        STORE.apply_giangho_reward(reward_bac, reward_mon_phai_exp, reward_hero_exp)
    except ValueError as exc:
        return {"ErrorCode": 0, "ErrorMsg": str(exc)}

    replay = {
        "BuaChuBiThuatMP1": [], "BuaChuBiThuatMP2": [], "DoiThang": 0,
        "Team1": {"Name": STORE.account_payload().get("DisplayName", "Offline"), "AccountID": "offline-user", "DanhVong": 0},
        "Team2": {"Name": f"Ải {giang_ho_idx + 1}-{nhiem_vu_idx + 1}", "AccountID": f"npc-{giang_ho_idx}-{nhiem_vu_idx}", "DanhVong": 0},
        "Hiep1": {
            "DoiHinh1": [_battle_vogia(player_code, player_hp)],
            "DoiHinh2": [_battle_vogia(enemy_code, enemy_hp)],
            "LuotDau": [{
                "DoiTanCong": 0,
                "NguoiTanCong": 0,
                "DanhSachThuongTon": [{"Value": enemy_hp, "TrangThaiThuongTon": []}],
                "VoCong": "",
            }],
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
            "ExpMonPhai": reward_mon_phai_exp,
            "ExpNhanVat": reward_hero_exp,
            "Items": [],
        },
        "UpdateUserInfo": STORE.user_info_payload(),
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

    # Runtime sweep 1.
    "getinfolienminh": _get_info_lien_minh_response,
    "createlienminh": _empty_feature_response,
    "chatget": _chat_get_response,
    "getanhhungbang": _event_info_response,
    "getdongnhaninfo": _event_info_response,
    "gethuyetchieninfo": _event_info_response,
    "getnienthuinfo": _event_info_response,
    "getvantieuinfo": _event_info_response,
    "ngunhacgetinfo": _event_info_response,
    "gettongkiminfo": _event_info_response,

    # Runtime sweep 2 from uploaded log 13:04-13:07.
    "buyvatphamtieuthu": _buy_user_info_response,
    "buylebao": _buy_user_info_response,
    "refreshdiemluankiem": _refresh_diem_luan_kiem_response,
    "getinfobangchien": _get_info_bang_chien_response,
    "findlienminh": _find_lien_minh_response,
    "getthanhvienlienminh": _get_thanh_vien_lien_minh_response,
}


class DMCHandler(BaseHTTPRequestHandler):
    server_version = "DMCOffline/0.8"

    def log_message(self, fmt: str, *args: object) -> None:
        log.info("%s - %s", self.client_address[0], fmt % args)

    def _gm_allowed(self) -> bool:
        return self.client_address[0] in {"127.0.0.1", "::1"}

    def _send_plain(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)

    def _send_json(self, status: int, obj: dict) -> None:
        self._send_plain(status, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/gm":
            if not self._gm_allowed():
                self._send_plain(403, "GM tool is localhost-only")
                return
            self._send_plain(200, gm_html(), "text/html; charset=utf-8")
            return
        if path == "/gm/api/state":
            if not self._gm_allowed():
                self._send_json(403, {"ok": False, "error": "GM tool is localhost-only"})
                return
            self._send_json(200, handle_gm_api(STORE, path))
            return
        if path in {"/", "/health"}:
            self._send_json(200, {
                "ok": True, "service": "DaiMinhChu-Offline", "user_url": PUBLIC_USER_URL,
                "battle_url": PUBLIC_BATTLE_URL, "save_file": str(STORE.path),
                "has_character": bool(STORE.hero_code), "gm_url": f"http://127.0.0.1:{PORT}/gm",
            })
            return
        self._send_plain(404, "not found")

    def do_POST(self) -> None:
        parsed_path = urlparse(self.path).path.rstrip("/")
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
        if parsed_path.startswith("/gm/api/"):
            if not self._gm_allowed():
                self._send_json(403, {"ok": False, "error": "GM tool is localhost-only"})
                return
            try:
                result = handle_gm_api(STORE, parsed_path, json.loads(raw_body or "{}"))
                self._send_json(200 if result.get("ok") else 404, result)
            except Exception as exc:
                log.exception("GM API failed: %s", parsed_path)
                self._send_json(400, {"ok": False, "error": str(exc)})
            return

        route_name = parsed_path.rsplit("/", 1)[-1].lower()
        handler = ROUTES.get(route_name)
        if handler is None:
            log.warning("Unhandled route: %s", parsed_path)
            self._send_plain(404, "not found")
            return

        form = parse_qs(raw_body, keep_blank_values=True)
        encrypted = form.get("data", [None])[0]
        if not encrypted:
            self._send_plain(400, "missing data")
            return
        try:
            request_obj = json.loads(decrypt_text(encrypted))
        except Exception as exc:
            log.exception("%s: decrypt/JSON failed", parsed_path)
            self._send_plain(400, f"bad request: {exc}")
            return

        log.info("%s request: %s", parsed_path, json.dumps(request_obj, ensure_ascii=False))
        response_obj = handler(request_obj)
        response_json = json.dumps(response_obj, ensure_ascii=False, separators=(",", ":"))
        log.info("%s response: %s", parsed_path, response_json)
        self._send_plain(200, encrypt_text(response_json))


def main() -> None:
    log.info("Starting Dai Minh Chu local compatibility server")
    log.info("Listen: http://%s:%s", HOST, PORT)
    log.info("GM Tool: http://127.0.0.1:%s/gm", PORT)
    log.info("Advertised User.asmx: %s", PUBLIC_USER_URL)
    log.info("Derived Battle.asmx: %s", PUBLIC_BATTLE_URL)
    log.info("Save file: %s", STORE.path)
    log.info("Registered game routes: %s", ", ".join(sorted(ROUTES)))
    ThreadingHTTPServer((HOST, PORT), DMCHandler).serve_forever()


if __name__ == "__main__":
    main()
