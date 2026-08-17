import unittest

from app import (
    PUBLIC_BATTLE_URL,
    PUBLIC_USER_URL,
    START_HEROES,
    STATE,
    _get_user_info_response,
    _giang_ho_response,
    _login_response,
    _select_start_nhan_vat_response,
)
from crypto import decrypt_text, encrypt_text


class CryptoTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        for text in ["{}", '{"User":"test","Pass":"123"}', "Đại Minh Chủ offline"]:
            self.assertEqual(decrypt_text(encrypt_text(text)), text)


class FixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        STATE["selected_hero"] = "NV_LenhHoXung"

    def test_login_advertises_full_user_asmx(self) -> None:
        url = _login_response({})["Servers"][0]["Url"]
        self.assertEqual(url, PUBLIC_USER_URL)
        self.assertTrue(url.endswith("/Server/Webservice/User.asmx"))
        self.assertTrue(PUBLIC_BATTLE_URL.endswith("/Server/Webservice/Battle.asmx"))

    def test_new_account_has_no_hero(self) -> None:
        self.assertEqual(_get_user_info_response({})["NhanVat"], [])

    def test_all_three_start_heroes(self) -> None:
        for code in START_HEROES:
            response = _select_start_nhan_vat_response({"NhanVatCode": code})
            self.assertEqual(response["ErrorCode"], 1)
            self.assertEqual(response["NhanVat"][0]["Name"], code)
            self.assertEqual(response["DoiHinh"]["Slot1"], 1)
            self.assertEqual(STATE["selected_hero"], code)

    def test_unknown_start_hero_rejected(self) -> None:
        self.assertEqual(
            _select_start_nhan_vat_response({"NhanVatCode": "NV_Unknown"})["ErrorCode"],
            0,
        )

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


if __name__ == "__main__":
    unittest.main()
