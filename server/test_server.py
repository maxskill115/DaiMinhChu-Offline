import json
import os
import tempfile
import unittest
from pathlib import Path

_TEST_DIR = tempfile.TemporaryDirectory()
os.environ["DMC_SAVE_FILE"] = str(Path(_TEST_DIR.name) / "save.json")

from app import (  # noqa: E402
    PUBLIC_BATTLE_URL,
    PUBLIC_USER_URL,
    ROUTES,
    STORE,
    _get_user_info_response,
    _giang_ho_response,
    _lay_nhan_vat_response,
    _login_response,
    _mini_boss_info_response,
    _select_start_nhan_vat_response,
    _system_highlight_response,
)
from crypto import decrypt_text, encrypt_text  # noqa: E402
from gm import handle_gm_api  # noqa: E402
from state import CHAPTER_MISSION_COUNTS, START_HEROES, SaveStore  # noqa: E402


class CryptoTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        for text in ["{}", '{"User":"test","Pass":"123"}', "Đại Minh Chủ offline"]:
            self.assertEqual(decrypt_text(encrypt_text(text)), text)


class FixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        STORE.reset()

    def test_login_advertises_full_user_and_battle_urls(self) -> None:
        url = _login_response({})["Servers"][0]["Url"]
        self.assertEqual(url, PUBLIC_USER_URL)
        self.assertTrue(url.endswith("/Server/Webservice/User.asmx"))
        self.assertTrue(PUBLIC_BATTLE_URL.endswith("/Server/Webservice/Battle.asmx"))

    def test_new_account_routes_to_first_character(self) -> None:
        info = _get_user_info_response({})
        self.assertEqual(info["NhanVat"], [])
        self.assertEqual(info["GiangHo"], [])
        self.assertNotIn("DoiHinh", info)

    def test_all_three_start_heroes_persist(self) -> None:
        for code in START_HEROES:
            STORE.reset()
            response = _select_start_nhan_vat_response({"NhanVatCode": code})
            self.assertEqual(response["ErrorCode"], 1)
            self.assertEqual(response["NhanVat"][0]["Name"], code)
            self.assertEqual(response["DoiHinh"]["Slot1"], 1)
            self.assertEqual(SaveStore(STORE.path).hero_code, code)

    def test_unknown_start_hero_rejected(self) -> None:
        self.assertEqual(_select_start_nhan_vat_response({"NhanVatCode": "NV_Unknown"})["ErrorCode"], 0)

    def test_existing_save_skips_character_creation(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_SoLuuHuong"})
        info = _get_user_info_response({})
        self.assertEqual(info["NhanVat"][0]["Name"], "NV_SoLuuHuong")
        self.assertEqual(info["DoiHinh"]["Slot1"], 1)

    def test_runtime_discovered_routes_are_registered(self) -> None:
        expected = {
            "getsystemhighlight",
            "getminibossinfo",
            "laynhanvat",
            "getinfolienminh",
            "createlienminh",
            "chatget",
            "getanhhungbang",
            "getdongnhaninfo",
            "gethuyetchieninfo",
            "getnienthuinfo",
            "getvantieuinfo",
            "ngunhacgetinfo",
            "gettongkiminfo",
        }
        self.assertTrue(expected.issubset(ROUTES))

    def test_runtime_menu_stubs_are_http_success_envelopes(self) -> None:
        for name in (
            "getinfolienminh", "createlienminh", "chatget", "getanhhungbang",
            "getdongnhaninfo", "gethuyetchieninfo", "getnienthuinfo",
            "getvantieuinfo", "ngunhacgetinfo", "gettongkiminfo",
        ):
            response = ROUTES[name]({"Aid": 1})
            self.assertEqual(response["ErrorCode"], 1, name)
            self.assertIn("ErrorMsg", response, name)

    def test_system_highlight_stub_is_empty_success(self) -> None:
        response = _system_highlight_response({"Aid": 1})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertEqual(response["SystemHighLightList"], [])

    def test_mini_boss_stub_is_empty_success(self) -> None:
        response = _mini_boss_info_response({"Aid": 1})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertIsNone(response["MiniBossInfo"])

    def test_lay_nhan_vat_response_contains_known_embedded_code(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_LenhHoXung"})
        before = STORE.account_payload()["Vang"]
        response = _lay_nhan_vat_response({"Aid": 1})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertIn(response["CodeName"], START_HEROES)
        self.assertEqual(response["NhanVatCode"], response["CodeName"])
        self.assertIsInstance(response["ListEventHon"], list)
        self.assertEqual(response["GetIdx"], 0)
        self.assertEqual(STORE.account_payload()["Vang"], before)

    def test_gm_updates_account_time_and_group(self) -> None:
        handle_gm_api(STORE, "/gm/api/account", {"DisplayName": "GM", "Vang": 999999, "Bac": 888888, "Vip": 12, "Level": 99})
        handle_gm_api(STORE, "/gm/api/time", {"LuotNV": 999, "LuotTD": 777})
        handle_gm_api(STORE, "/gm/api/group", {"name": "TrangBi", "value": [{"Id": 1, "Name": "TB_TEST"}]})
        info = STORE.user_info_payload()
        self.assertEqual(info["Account"]["Vang"], 999999)
        self.assertEqual(info["Account"]["Vip"], 12)
        self.assertEqual(info["GiaTriThoiGian"]["LuotNV"], 999)
        self.assertEqual(info["TrangBi"][0]["Name"], "TB_TEST")

    def test_gm_add_extra_hero_and_item(self) -> None:
        STORE.gm_set_main_hero("NV_LenhHoXung", 10, 50)
        handle_gm_api(STORE, "/gm/api/add-hero", {"Name": "NV_TEST", "Level": 20})
        handle_gm_api(STORE, "/gm/api/add-item", {"name": "VatPhamTieuThu", "item": {"Name": "VP_TEST", "SoLuong": 9}})
        info = STORE.user_info_payload()
        self.assertEqual(len(info["NhanVat"]), 2)
        self.assertEqual(info["NhanVat"][1]["Name"], "NV_TEST")
        self.assertEqual(info["VatPhamTieuThu"][0]["SoLuong"], 9)

    def test_gm_reset_creates_clean_named_account(self) -> None:
        STORE.gm_update_account({"Vang": 12345})
        handle_gm_api(STORE, "/gm/api/reset", {"DisplayName": "Fresh"})
        self.assertEqual(STORE.account_payload()["DisplayName"], "Fresh")
        self.assertEqual(STORE.account_payload()["Vang"], 100)
        self.assertIsNone(STORE.hero_code)

    def test_first_giangho_win_unlocks_next_mission_and_serializes_json(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_LenhHoXung"})
        response = _giang_ho_response({"giangHoIdx": 0, "nhiemVuIdx": 0})
        self.assertEqual(response["ErrorCode"], 1)
        missions = json.loads(response["UpdateUserInfo"]["GiangHo"][0]["Nhiemvu"])
        self.assertEqual(missions, [{"S": 3, "T": 1}, {"S": 0, "T": 0}])

    def test_replaying_mission_preserves_best_star_and_increments_turn(self) -> None:
        store = SaveStore(Path(_TEST_DIR.name) / "progress.json")
        store.reset(); store.complete_giangho_battle(0, 0, 3); store.complete_giangho_battle(0, 0, 1)
        self.assertEqual(json.loads(store.giangho_payload()[0]["Nhiemvu"])[0], {"S": 3, "T": 2})

    def test_locked_mission_rejected(self) -> None:
        store = SaveStore(Path(_TEST_DIR.name) / "locked.json"); store.reset()
        with self.assertRaises(ValueError): store.complete_giangho_battle(0, 1, 3)

    def test_last_first_chapter_mission_completes_and_unlocks_next_chapter(self) -> None:
        store = SaveStore(Path(_TEST_DIR.name) / "chapter.json"); store.reset()
        for idx in range(CHAPTER_MISSION_COUNTS[0]): store.complete_giangho_battle(0, idx, 3)
        self.assertEqual(store.giangho_payload()[0]["HoanThanh"], 1)
        store.complete_giangho_battle(1, 0, 3)
        self.assertEqual(json.loads(store.giangho_payload()[1]["Nhiemvu"])[1], {"S": 0, "T": 0})

    def test_minimal_giang_ho_replay_is_null_safe_for_confirmed_dereferences(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_SoLuuHuong"})
        response = _giang_ho_response({"giangHoIdx": 0, "nhiemVuIdx": 0})
        replay = response["BattleReplay"]; hiep1 = replay["Hiep1"]
        self.assertEqual(response["star"], 3); self.assertEqual(replay["DoiThang"], 0)
        self.assertIsInstance(hiep1["DoiHinh1"][0]["Buffs"], list)
        self.assertIsInstance(hiep1["LuotDau"][0]["DanhSachThuongTon"][0]["TrangThaiThuongTon"], list)
        self.assertGreater(response["UpdateUserInfo"]["Account"]["Bac"], 10000)


if __name__ == "__main__": unittest.main()
