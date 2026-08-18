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
            reloaded = SaveStore(STORE.path)
            self.assertEqual(reloaded.hero_code, code)

    def test_unknown_start_hero_rejected(self) -> None:
        self.assertEqual(
            _select_start_nhan_vat_response({"NhanVatCode": "NV_Unknown"})["ErrorCode"],
            0,
        )

    def test_existing_save_skips_character_creation(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_SoLuuHuong"})
        info = _get_user_info_response({})
        self.assertEqual(info["NhanVat"][0]["Name"], "NV_SoLuuHuong")
        self.assertEqual(info["DoiHinh"]["Slot1"], 1)

    def test_runtime_discovered_routes_are_registered(self) -> None:
        self.assertIn("getsystemhighlight", ROUTES)
        self.assertIn("getminibossinfo", ROUTES)
        self.assertIn("laynhanvat", ROUTES)

    def test_system_highlight_stub_is_empty_success(self) -> None:
        response = _system_highlight_response({"Aid": 1})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertEqual(response["SystemHighLightList"], [])
        self.assertEqual(response["SystemHighLight"], [])

    def test_mini_boss_stub_is_empty_success(self) -> None:
        response = _mini_boss_info_response({"Aid": 1})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertIsNone(response["MiniBossInfo"])
        self.assertEqual(response["DanhSachMiniBoss"], [])

    def test_lay_nhan_vat_stub_returns_current_snapshot_without_spending(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_LenhHoXung"})
        vang_before = STORE.account_payload()["Vang"]
        response = _lay_nhan_vat_response({"Aid": 1})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertEqual(response["NhanVat"][0]["Name"], "NV_LenhHoXung")
        self.assertEqual(response["Account"]["Vang"], vang_before)
        self.assertEqual(STORE.account_payload()["Vang"], vang_before)

    def test_first_giangho_win_unlocks_next_mission_and_serializes_json(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_LenhHoXung"})
        response = _giang_ho_response({"giangHoIdx": 0, "nhiemVuIdx": 0})
        self.assertEqual(response["ErrorCode"], 1)
        progress = response["UpdateUserInfo"]["GiangHo"]
        self.assertEqual(len(progress), 1)
        self.assertEqual(progress[0]["GiangHoIndx"], 0)
        self.assertEqual(progress[0]["HoanThanh"], 0)
        missions = json.loads(progress[0]["Nhiemvu"])
        self.assertEqual(missions, [{"S": 3, "T": 1}, {"S": 0, "T": 0}])

    def test_replaying_mission_preserves_best_star_and_increments_turn(self) -> None:
        store = SaveStore(Path(_TEST_DIR.name) / "progress.json")
        store.reset()
        store.complete_giangho_battle(0, 0, 3)
        store.complete_giangho_battle(0, 0, 1)
        missions = json.loads(store.giangho_payload()[0]["Nhiemvu"])
        self.assertEqual(missions[0], {"S": 3, "T": 2})

    def test_locked_mission_rejected(self) -> None:
        store = SaveStore(Path(_TEST_DIR.name) / "locked.json")
        store.reset()
        with self.assertRaises(ValueError):
            store.complete_giangho_battle(0, 1, 3)

    def test_last_first_chapter_mission_completes_and_unlocks_next_chapter(self) -> None:
        store = SaveStore(Path(_TEST_DIR.name) / "chapter.json")
        store.reset()
        for idx in range(CHAPTER_MISSION_COUNTS[0]):
            store.complete_giangho_battle(0, idx, 3)
        first = store.giangho_payload()[0]
        self.assertEqual(first["HoanThanh"], 1)
        store.complete_giangho_battle(1, 0, 3)
        progress = store.giangho_payload()
        self.assertEqual(len(progress), 2)
        second_missions = json.loads(progress[1]["Nhiemvu"])
        self.assertEqual(second_missions[0]["S"], 3)
        self.assertEqual(second_missions[1], {"S": 0, "T": 0})

    def test_minimal_giang_ho_replay_is_null_safe_for_confirmed_dereferences(self) -> None:
        _select_start_nhan_vat_response({"NhanVatCode": "NV_SoLuuHuong"})
        response = _giang_ho_response({"giangHoIdx": 0, "nhiemVuIdx": 0})
        replay = response["BattleReplay"]
        hiep1 = replay["Hiep1"]

        self.assertEqual(response["ErrorCode"], 1)
        self.assertEqual(response["star"], 3)
        self.assertEqual(replay["DoiThang"], 0)
        self.assertTrue(replay["Team1"])
        self.assertTrue(replay["Team2"])
        self.assertGreaterEqual(len(hiep1["DoiHinh1"]), 1)
        self.assertGreaterEqual(len(hiep1["DoiHinh2"]), 1)
        self.assertGreaterEqual(len(hiep1["LuotDau"]), 1)
        self.assertEqual(hiep1["DoiHinh1"][0]["Name"], "NV_SoLuuHuong")
        self.assertIsInstance(hiep1["DoiHinh1"][0]["Buffs"], list)
        self.assertEqual(hiep1["LuotDau"][0]["VoCong"], "")
        self.assertGreaterEqual(len(hiep1["LuotDau"][0]["DanhSachThuongTon"]), 1)
        self.assertIsInstance(
            hiep1["LuotDau"][0]["DanhSachThuongTon"][0]["TrangThaiThuongTon"],
            list,
        )
        self.assertIsInstance(response["Reward"]["Items"], list)
        self.assertEqual(response["UpdateUserInfo"]["NhanVat"][0]["Id"], 1)
        self.assertGreater(response["UpdateUserInfo"]["Account"]["Bac"], 10000)


if __name__ == "__main__":
    unittest.main()
