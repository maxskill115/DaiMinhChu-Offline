from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

from patch_client import (
    ASSEMBLY_PATH,
    DIRECT_LOGIN_IL,
    LOGIN_URL_US_INDEX,
    ON_LOGIN_BTN_RVA,
    SOHA_SET_USER_INFO_NOOP_IL,
    SOHA_SET_USER_INFO_RVA,
    _find_metadata_stream,
    _rva_to_offset,
)


def _read_user_string(data: bytes | bytearray, us_index: int) -> str:
    us_off, us_size = _find_metadata_stream(data, "#US")
    entry = us_off + us_index
    if entry >= us_off + us_size:
        raise ValueError("#US index out of range")

    first = data[entry]
    if first & 0x80:
        raise ValueError("target user string uses unsupported multi-byte length")
    payload = bytes(data[entry + 1 : entry + 1 + first])
    if not payload:
        return ""
    return payload[:-1].decode("utf-16le", errors="replace")


def _method_body(data: bytes | bytearray, rva: int) -> bytes:
    mutable = bytearray(data)
    method_off = _rva_to_offset(mutable, rva)
    flags = int.from_bytes(mutable[method_off : method_off + 2], "little")
    if flags & 0x3 != 0x3:
        raise ValueError(f"method at RVA 0x{rva:x} is not fat IL")
    header_dwords = (flags >> 12) & 0xF
    header_size = header_dwords * 4
    code_size = int.from_bytes(mutable[method_off + 4 : method_off + 8], "little")
    code_off = method_off + header_size
    return bytes(mutable[code_off : code_off + code_size])


def verify_apk(path: Path) -> int:
    raw = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        assembly = zf.read(ASSEMBLY_PATH)

    login_url = _read_user_string(assembly, LOGIN_URL_US_INDEX)
    login_body = _method_body(assembly, ON_LOGIN_BTN_RVA)
    set_user_info_body = _method_body(assembly, SOHA_SET_USER_INFO_RVA)

    login_ok = login_body == DIRECT_LOGIN_IL
    soha_ok = set_user_info_body == SOHA_SET_USER_INFO_NOOP_IL

    print(f"APK: {path}")
    print(f"Login URL: {login_url}")
    print(f"Direct login patch: {'OK' if login_ok else 'MISSING'}")
    print(f"Soha SetUserInfo no-op: {'OK' if soha_ok else 'MISSING'}")
    print(f"SetUserInfo CodeSize: {len(set_user_info_body)}")
    print(f"SetUserInfo IL: {set_user_info_body.hex(' ')}")

    return 0 if login_ok and soha_ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Dai Minh Chu offline client patches")
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    raise SystemExit(verify_apk(args.apk))


if __name__ == "__main__":
    main()
