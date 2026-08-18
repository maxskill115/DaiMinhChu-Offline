import os
import tempfile
import unittest
from pathlib import Path

_TEST_DIR = tempfile.TemporaryDirectory()
os.environ["DMC_SAVE_FILE"] = str(Path(_TEST_DIR.name) / "audit-save.json")

from app import ROUTES, STORE, _danh_nhanh_giang_ho_response  # noqa: E402
from static_endpoints import STATIC_ENDPOINTS, STATIC_ENDPOINTS_LOWER  # noqa: E402


class EndpointAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        STORE.reset()

    def test_static_endpoint_inventory_count(self) -> None:
        self.assertEqual(len(STATIC_ENDPOINTS), 277)
        self.assertEqual(len(STATIC_ENDPOINTS_LOWER), 277)

    def test_core_runtime_routes_exist_in_static_inventory(self) -> None:
        for name in ("Login", "CheckUser", "GetUserInfo", "SelectStartNhanVat", "GiangHo",
                     "DanhNhanhGiangHo", "ResetTurnNhiemVuGH", "LayNhanVat"):
            self.assertIn(name, STATIC_ENDPOINTS)

    def test_exact_giangho_quick_route_names(self) -> None:
        self.assertIn("danhnhanhgiangho", ROUTES)
        self.assertIn("resetturnnhiemvugh", ROUTES)
        self.assertNotIn("resetturnnhiemvugiangho", STATIC_ENDPOINTS_LOWER)

    def test_danh_nhanh_persists_ten_rewards(self) -> None:
        STORE.choose_hero("NV_LenhHoXung")
        before = STORE.account_payload().copy()
        before_hero_exp = STORE.hero_payload()["Exp"]
        response = _danh_nhanh_giang_ho_response({"giangHoIdx": 0, "nhiemVuIdx": 0, "Count": 10})
        self.assertEqual(response["ErrorCode"], 1)
        self.assertEqual(response["Count"], 10)
        self.assertEqual(len(response["Rewards"]), 10)
        self.assertEqual(STORE.account_payload()["Bac"], before["Bac"] + 1000)
        self.assertEqual(STORE.account_payload()["Exp"], before["Exp"] + 100)
        self.assertEqual(STORE.hero_payload()["Exp"], before_hero_exp + 100)


if __name__ == "__main__":
    unittest.main()
