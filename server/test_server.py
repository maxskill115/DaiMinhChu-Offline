import unittest

from app import (
    PUBLIC_USER_URL,
    START_HEROES,
    _get_user_info_response,
    _login_response,
    _select_start_nhan_vat_response,
)
from crypto import decrypt_text, encrypt_text


class CryptoTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        for text in ["{}", '{"User":"test","Pass":"123"}', "Đại Minh Chủ offline"]:
            self.assertEqual(decrypt_text(encrypt_text(text)), text)


class FixtureTests(unittest.TestCase):
    def test_login_advertises_full_user_asmx(self) -> None:
        url = _login_response({})["Servers"][0]["Url"]
        self.assertEqual(url, PUBLIC_USER_URL)
        self.assertTrue(url.endswith("/Server/Webservice/User.asmx"))

    def test_new_account_has_no_hero(self) -> None:
        self.assertEqual(_get_user_info_response({})["NhanVat"], [])

    def test_all_three_start_heroes(self) -> None:
        for code in START_HEROES:
            response = _select_start_nhan_vat_response({"NhanVatCode": code})
            self.assertEqual(response["ErrorCode"], 1)
            self.assertEqual(response["NhanVat"][0]["Name"], code)
            self.assertEqual(response["DoiHinh"]["Slot1"], 1)

    def test_unknown_start_hero_rejected(self) -> None:
        self.assertEqual(
            _select_start_nhan_vat_response({"NhanVatCode": "NV_Unknown"})["ErrorCode"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
