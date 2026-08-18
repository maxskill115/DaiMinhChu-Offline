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
from static_endpoints import STATIC_ENDPOINTS_LOWER

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

_ZERO_TIME = "2000-01-01T00:00:00"
_LOWER_OK = 0
_LOWER_ERROR = 1


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
    # Lower-case HTTP_ERROR_CODE family: runtime evidence shows default 0 entered success callbacks.
    return {"highLightQuery": [], "errorCode": _LOWER_OK, "errorMsg": ""}


def _mini_boss_info_response(_: dict) -> dict:
    return {
        "QueueHits": [], "NextTime": _ZERO_TIME,
        "MauBoss": 0, "MauBossOrig": 0,
        "TopHits1": None, "TopHits2": None, "TopHits3": None,
        "lastTop10": [], "LastMiniBoss": _ZERO_TIME, "BossName": "",
        "ServerTime": _ZERO_TIME, "HitCount": 0, "TotalThuongTon": 0,
        "ErrorCode": 1, "ErrorMsg": "",
    }


def _pick_recruit_code() -> str:
    owned = {str(x.get("Name")) for x in STORE.all_heroes_payload() if isinstance(x, dict)}
    for code in START_HEROES:
        if code not in owned:
            return code
    return next(iter(START_HEROES))


def _lay_nhan_vat_response(_: dict) -> dict:
    # HTTPLayNhanVatRespone exact fields:
    # errorCode, errorMsg, ListEventHon, GetIdx, UpdateUserInfo.
    # CONFIRMED RUNTIME before 0.10: when lower-case errorCode was absent it
    # defaulted to 0 and WaitForLayNhanVat entered the success callback, then
    # crashed because errorMsg/code_name was empty. Therefore 0 is success for
    # this lower-case enum family; 0.10 incorrectly returned 1 and silently took
    # the non-success path.
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
        "errorCode": _LOWER_OK,
        "errorMsg": code,
        "ListEventHon": [],
        "GetIdx": 0,
        "UpdateUserInfo": STORE.user_info_payload(),
    }


def _unsupported_static_response(_: dict) -> dict:
    # Two legacy error-code conventions coexist in this client:
    #   ErrorCode  : 1=success, 0=failure
    #   errorCode  : 0=success, non-zero=failure
    # Return failure in BOTH conventions so a statically-known but unreversed
    # endpoint never accidentally enters a success callback and dereferences
    # missing DTO data.
    message = "Offline backend: endpoint recognised but DTO/gameplay is not reconstructed yet"
    return {"ErrorCode": 0, "ErrorMsg": message, "errorCode": _LOWER_ERROR, "errorMsg": message}


def _get_info_lien_minh_response(_: dict) -> dict:
    return {"errorCode": _LOWER_OK, "errorMsg": "", "lienMinhInfo": None}


def _create_lien_minh_response(_: dict) -> dict:
    return {"lienMinh": None, "lienMinhAccount": None, "info": None,
            "errorCode": _LOWER_ERROR, "errorMsg": "Liên minh offline chưa được tạo dữ liệu"}


def _chat_get_response(_: dict) -> dict:
    return {"chatQuery": [], "errorCode": _LOWER_OK, "errorMsg": ""}


def _get_anh_hung_bang_response(_: dict) -> dict:
    return {
        "AnhHungBang": [], "ThuHang": 0, "DiemTichLuy": 0, "LuotLuanKiem": 0,
        "lastTimeGetDiem": _ZERO_TIME,
        "GetRewardTop1000": 0, "GetRewardTop500": 0, "GetRewardTop200": 0,
        "GetRewardTop100": 0, "GetRewardTop50": 0, "GetRewardTop10": 0, "GetRewardTop1": 0,
        "NPC1": {"CodeName": "NV_PhongThanhDuong", "DiemThuongCanDoi": 0, "BoiDuongDan": 0},
        "NPC2": {"CodeName": "NV_LenhHoXung", "DiemThuongCanDoi": 0, "BoiDuongDan": 0},
        "ErrorCode": 1, "ErrorMsg": "",
    }


def _get_dong_nhan_info_response(_: dict) -> dict:
    return {
        "QueueHits": [], "LastTime": _ZERO_TIME,
        "LevelDongNhan": 1, "MauDongNhan": 1, "MauDongNhanOrig": 1,
        "TopHits": None, "TimeStartDongNhan": _ZERO_TIME, "lastTop10": [],
        "ServerTime": _ZERO_TIME, "LuotDanh": 0, "TotalThuongTon": 0,
        "CostRespawn": {}, "DurationLastBattle": 0,
        "ErrorCode": 1, "ErrorMsg": "",
    }


def _empty_huyet_chien_opponent() -> dict:
    return {"NpcTeam": "", "Reward": "", "NumWarriors": 0, "NumOpWarriors": 0}


def _get_huyet_chien_info_response(_: dict) -> dict:
    profile = {
        "AId": 1, "LastSao": 0, "Luot": 0, "Level": 1, "Sao": 0, "SaoThua": 0,
        "BestLevel": 0, "BestLevelSao": 0, "BestSao": 0, "SaoRecords": {}, "SaoTrongAi": 0,
        "TangMau": 0, "TangCong": 0, "TangThu": 0, "TangNoiLuc": 0,
        "DoiThuKho": _empty_huyet_chien_opponent(),
        "DoiThuBt": _empty_huyet_chien_opponent(),
        "DoiThuDe": _empty_huyet_chien_opponent(),
        "LastDate": _ZERO_TIME, "NumWarrior": 0, "TangThuocTinh": False, "NhanThuong": False,
        "TangThuocTinh1": 0, "TangThuocTinh2": 0, "TangThuocTinh3": 0,
        "RecordInTop": 0, "DuDoan": 0,
    }
    phan_thuong = {"errorCode": _LOWER_OK, "errorMsg": "", "PhanThuongList": [],
                   "UpdateUserInfo": STORE.user_info_payload()}
    return {"Profile": profile, "Top": 0, "PhanThuong": phan_thuong, "ErrorCode": 1, "ErrorMsg": ""}


def _get_nien_thu_info_response(_: dict) -> dict:
    return {
        "QueueHits": [], "LastTime": _ZERO_TIME, "LevelNienThu": 1,
        "MauLong": 1, "MauLan": 1, "MauQuy": 1, "MauPhung": 1,
        "MauOrigLong": 1, "MauOrigLan": 1, "MauOrigQuy": 1, "MauOrigPhung": 1,
        "TopHits": None, "TimeStartNienThu": _ZERO_TIME, "lastTop10": [],
        "ServerTime": _ZERO_TIME, "LuotDanh": 0, "TotalThuongTon": 0,
        "CostRespawn": {}, "DurationLastBattle": 0,
        "ErrorCode": 1, "ErrorMsg": "",
    }


def _get_van_tieu_info_response(_: dict) -> dict:
    return {"maxVanTieu": 0, "thoiGian": "", "soLuotMienPhi": 0, "knb": 0,
            "vanTieu": [], "cuopTieuLog": [], "errorCode": _LOWER_OK, "errorMsg": ""}


def _ngu_nhac_get_info_response(_: dict) -> dict:
    return {
        "errorCode": _LOWER_OK, "errorMsg": "",
        "kiemTranInfo": {"aidF": [], "NguNhacIndex": 0, "SoLuot": 0, "SoLuotMua": 0},
        "knbVuotNhanh": 0,
        "biBaoShopInfo": {"BiBaoShop": [], "PTNguNhac1": [], "PTNguNhac2": [],
                           "PTNguNhac3": [], "PTNguNhac4": [], "PTNguNhac5": []},
        "huongDan": "",
    }


def _get_tong_kim_info_response(_: dict) -> dict:
    return {"huongDan": "", "listBoss": []}


def _buy_user_info_response(_: dict) -> dict:
    return STORE.user_info_payload()


def _refresh_diem_luan_kiem_response(_: dict) -> dict:
    return {"DiemTichLuy": 0, "LastTimeGetDiem": _ZERO_TIME, "ErrorCode": 1, "ErrorMsg": ""}


def _get_info_bang_chien_response(_: dict) -> dict:
    return {"timeBangChien": 0, "giaiBangChien": [], "boTranBangChien": [],
            "ErrorCode": 1, "ErrorMsg": ""}


def _find_lien_minh_response(_: dict) -> dict:
    return {"danhSachLM": [], "errorCode": _LOWER_OK, "errorMsg": ""}


def _get_thanh_vien_lien_minh_response(_: dict) -> dict:
    return {"danhSachThanhVien": [], "danhSachXinGiaNhap": [], "errorCode": _LOWER_OK, "errorMsg": ""}


def _giangho_enemy(chapter_idx: int, mission_idx: int, player_code: str) -> tuple[str, int]:
    codes = list(START_HEROES)
    start = (chapter_idx * 7 + mission_idx) % len(codes)
    for offset in range(len(codes)):
        code = codes[(start + offset) % len(codes)]
        if code != player_code:
            return code, int(START_HEROES[code]["Mau"])
    code = codes[start]
    return code, int(START_HEROES[code]["Mau"])


def _reward_values(giang_ho_idx: int, nhiem_vu_idx: int) -> tuple[int, int, int]:
    return (100 + giang_ho_idx * 25 + nhiem_vu_idx * 10,
            10 + giang_ho_idx + nhiem_vu_idx,
            10 + giang_ho_idx + nhiem_vu_idx)


def _giang_ho_response(request: dict) -> dict:
    giang_ho_idx = int(request.get("giangHoIdx", request.get("GiangHoIdx", 0)) or 0)
    nhiem_vu_idx = int(request.get("nhiemVuIdx", request.get("NhiemVuIdx", 0)) or 0)
    player_code = STORE.hero_code
    if not player_code or player_code not in START_HEROES:
        return {"ErrorCode": 0, "ErrorMsg": "No offline character selected"}

    enemy_code, enemy_hp = _giangho_enemy(giang_ho_idx, nhiem_vu_idx, player_code)
    player_hp = int(START_HEROES[player_code]["Mau"])
    star = 3
    reward_bac, reward_mon_phai_exp, reward_hero_exp = _reward_values(giang_ho_idx, nhiem_vu_idx)

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
            "LuotDau": [{"DoiTanCong": 0, "NguoiTanCong": 0,
                         "DanhSachThuongTon": [{"Value": enemy_hp, "TrangThaiThuongTon": []}], "VoCong": ""}],
        },
        "Hiep2": None, "Hiep3": None,
    }
    return {
        "giangHoIdx": giang_ho_idx, "nhiemVuIdx": nhiem_vu_idx, "star": star,
        "BattleReplay": replay,
        "Reward": {"Bac": reward_bac, "Vang": 0, "ExpMonPhai": reward_mon_phai_exp,
                   "ExpNhanVat": reward_hero_exp, "Items": []},
        "UpdateUserInfo": STORE.user_info_payload(), "ErrorCode": 1, "ErrorMsg": "",
    }


def _danh_nhanh_giang_ho_response(request: dict) -> dict:
    giang_ho_idx = int(request.get("giangHoIdx", request.get("GiangHoIdx", 0)) or 0)
    nhiem_vu_idx = int(request.get("nhiemVuIdx", request.get("NhiemVuIdx", 0)) or 0)
    count = int(request.get("Count", request.get("count", request.get("SoLan", 10))) or 10)
    count = max(1, min(count, 10))
    reward_bac, reward_account_exp, reward_hero_exp = _reward_values(giang_ho_idx, nhiem_vu_idx)
    results = []
    try:
        for _ in range(count):
            STORE.complete_giangho_battle(giang_ho_idx, nhiem_vu_idx, 3)
            STORE.apply_giangho_reward(reward_bac, reward_account_exp, reward_hero_exp)
            results.append({"Bac": reward_bac, "Vang": 0, "ExpMonPhai": reward_account_exp,
                            "ExpNhanVat": reward_hero_exp, "Items": []})
    except ValueError as exc:
        return {"ErrorCode": 0, "ErrorMsg": str(exc)}
    return {
        "Rewards": results,
        "GiangHoIdx": giang_ho_idx,
        "NhiemVuIdx": nhiem_vu_idx,
        "UpdateUserInfo": STORE.user_info_payload(),
        "ErrorCode": 1,
        "ErrorMsg": "",
    }


def _reset_turn_nhiem_vu_gh_response(_: dict) -> dict:
    return {"ErrorCode": 1, "ErrorMsg": "", "UpdateUserInfo": STORE.user_info_payload()}


ROUTES = {
    "login": _login_response,
    "checkuser": _check_user_response,
    "getuserinfo": _get_user_info_response,
    "selectstartnhanvat": _select_start_nhan_vat_response,
    "getsystemhighlight": _system_highlight_response,
    "getminibossinfo": _mini_boss_info_response,
    "laynhanvat": _lay_nhan_vat_response,
    "giangho": _giang_ho_response,
    "danhnhanhgiangho": _danh_nhanh_giang_ho_response,
    "resetturnnhiemvugh": _reset_turn_nhiem_vu_gh_response,
    "getinfolienminh": _get_info_lien_minh_response,
    "createlienminh": _create_lien_minh_response,
    "chatget": _chat_get_response,
    "getanhhungbang": _get_anh_hung_bang_response,
    "getdongnhaninfo": _get_dong_nhan_info_response,
    "gethuyetchieninfo": _get_huyet_chien_info_response,
    "getnienthuinfo": _get_nien_thu_info_response,
    "getvantieuinfo": _get_van_tieu_info_response,
    "ngunhacgetinfo": _ngu_nhac_get_info_response,
    "gettongkiminfo": _get_tong_kim_info_response,
    "buyvatphamtieuthu": _buy_user_info_response,
    "buylebao": _buy_user_info_response,
    "refreshdiemluankiem": _refresh_diem_luan_kiem_response,
    "getinfobangchien": _get_info_bang_chien_response,
    "findlienminh": _find_lien_minh_response,
    "getthanhvienlienminh": _get_thanh_vien_lien_minh_response,
}


def _handler_for_path(path: str):
    route_name = path.rstrip("/").rsplit("/", 1)[-1].lower()
    handler = ROUTES.get(route_name)
    is_static_stub = False
    if handler is None and route_name in STATIC_ENDPOINTS_LOWER:
        handler = _unsupported_static_response
        is_static_stub = True
    return route_name, handler, is_static_stub


class DMCHandler(BaseHTTPRequestHandler):
    server_version = "DMCOffline/0.11"

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

    def _serve_game_get(self, parsed) -> bool:
        route_name, handler, is_static_stub = _handler_for_path(parsed.path)
        if handler is None:
            return False

        query = parse_qs(parsed.query, keep_blank_values=True)
        encrypted = query.get("data", [None])[0]
        if encrypted:
            try:
                request_obj = json.loads(decrypt_text(encrypted))
            except Exception as exc:
                log.exception("GET %s: decrypt/JSON failed", parsed.path)
                self._send_plain(400, f"bad request: {exc}")
                return True
        else:
            # Several legacy read APIs (ChatGet is runtime-confirmed) use WWW GET
            # with no encrypted form body. Preserve query args if any.
            request_obj = {k: (v[0] if len(v) == 1 else v) for k, v in query.items()}

        if is_static_stub:
            log.warning("STATIC-KNOWN UNSUPPORTED GET %s request: %s", parsed.path,
                        json.dumps(request_obj, ensure_ascii=False))
        else:
            log.info("GET %s request: %s", parsed.path, json.dumps(request_obj, ensure_ascii=False))
        response_obj = handler(request_obj)
        response_json = json.dumps(response_obj, ensure_ascii=False, separators=(",", ":"))
        log.info("GET %s response: %s", parsed.path, response_json)
        self._send_plain(200, encrypt_text(response_json))
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/gm":
            if not self._gm_allowed():
                self._send_plain(403, "GM tool is localhost-only"); return
            self._send_plain(200, gm_html(), "text/html; charset=utf-8"); return
        if path == "/gm/api/state":
            if not self._gm_allowed():
                self._send_json(403, {"ok": False, "error": "GM tool is localhost-only"}); return
            self._send_json(200, handle_gm_api(STORE, path)); return
        if path in {"/", "/health"}:
            self._send_json(200, {"ok": True, "service": "DaiMinhChu-Offline", "server_version": self.server_version,
                "user_url": PUBLIC_USER_URL, "battle_url": PUBLIC_BATTLE_URL, "save_file": str(STORE.path),
                "has_character": bool(STORE.hero_code), "gm_url": f"http://127.0.0.1:{PORT}/gm",
                "static_endpoint_count": len(STATIC_ENDPOINTS_LOWER), "exact_route_count": len(ROUTES)})
            return
        if self._serve_game_get(parsed):
            return
        self._send_plain(404, "not found")

    def do_POST(self) -> None:
        parsed_path = urlparse(self.path).path.rstrip("/")
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw_body = self.rfile.read(length).decode("utf-8", errors="replace")
        if parsed_path.startswith("/gm/api/"):
            if not self._gm_allowed():
                self._send_json(403, {"ok": False, "error": "GM tool is localhost-only"}); return
            try:
                result = handle_gm_api(STORE, parsed_path, json.loads(raw_body or "{}"))
                self._send_json(200 if result.get("ok") else 404, result)
            except Exception as exc:
                log.exception("GM API failed: %s", parsed_path)
                self._send_json(400, {"ok": False, "error": str(exc)})
            return

        route_name, handler, is_static_stub = _handler_for_path(parsed_path)
        if handler is None:
            log.warning("UNHANDLED UNKNOWN route: %s", parsed_path)
            self._send_plain(404, "not found")
            return

        form = parse_qs(raw_body, keep_blank_values=True)
        encrypted = form.get("data", [None])[0]
        if not encrypted:
            self._send_plain(400, "missing data"); return
        try:
            request_obj = json.loads(decrypt_text(encrypted))
        except Exception as exc:
            log.exception("%s: decrypt/JSON failed", parsed_path)
            self._send_plain(400, f"bad request: {exc}"); return

        if is_static_stub:
            log.warning("STATIC-KNOWN UNSUPPORTED %s request: %s", parsed_path, json.dumps(request_obj, ensure_ascii=False))
        else:
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
    log.info("Exact routes: %d; static client endpoints covered: %d", len(ROUTES), len(STATIC_ENDPOINTS_LOWER))
    ThreadingHTTPServer((HOST, PORT), DMCHandler).serve_forever()


if __name__ == "__main__":
    main()
