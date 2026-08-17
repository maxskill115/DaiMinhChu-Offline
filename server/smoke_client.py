from __future__ import annotations

import argparse
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from crypto import decrypt_text, encrypt_text


def post_encrypted(url: str, payload: dict) -> dict:
    plain = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    body = urlencode({"data": encrypt_text(plain)}).encode("utf-8")
    request = Request(url, data=body, method="POST")
    with urlopen(request, timeout=5) as response:
        encrypted = response.read().decode("utf-8")
    return json.loads(decrypt_text(encrypted))


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the local DaiMinhChu compatibility server")
    parser.add_argument("--base", default="http://127.0.0.1:8000", help="server root URL")
    parser.add_argument(
        "--hero",
        default="NV_LenhHoXung",
        choices=["NV_PhongThanhDuong", "NV_LenhHoXung", "NV_SoLuuHuong"],
    )
    args = parser.parse_args()
    base = args.base.rstrip("/")
    user = f"{base}/Server/Webservice/User.asmx"
    battle = f"{base}/Server/Webservice/Battle.asmx"

    calls = [
        ("Login", f"{user}/Login", {"User": "offline", "Pass": "offline", "Version": 0}),
        ("CheckUser", f"{user}/CheckUser", {"User": "offline", "Token": "offline-token"}),
        (
            "GetUserInfo",
            f"{user}/GetUserInfo",
            {"Aid": 1, "Token": "offline-token", "Property": [{"Name": "account"}, {"Name": "nhanVat"}]},
        ),
        (
            "SelectStartNhanVat",
            f"{user}/SelectStartNhanVat",
            {"Aid": 1, "Token": "offline-token", "NhanVatCode": args.hero},
        ),
        (
            "GiangHo",
            f"{battle}/GiangHo",
            {"aid": 1, "token": "offline-token", "giangHoIdx": 0, "nhiemVuIdx": 0},
        ),
    ]

    for name, url, payload in calls:
        result = post_encrypted(url, payload)
        print(f"[{name}] ErrorCode={result.get('ErrorCode')} keys={','.join(result.keys())}")
        if name == "GiangHo":
            replay = result.get("BattleReplay") or {}
            hiep1 = replay.get("Hiep1") or {}
            print(
                "  replay:",
                f"winner={replay.get('DoiThang')}",
                f"star={result.get('star')}",
                f"turns={len(hiep1.get('LuotDau') or [])}",
            )


if __name__ == "__main__":
    main()
