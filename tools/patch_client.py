from __future__ import annotations

import argparse
import hashlib
import io
import struct
import zipfile
from pathlib import Path

EXPECTED_APK_SHA256 = "2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194"
ASSEMBLY_PATH = "assets/bin/Data/Managed/Assembly-CSharp.dll"
LOGIN_URL_US_INDEX = 0x153B9
ON_LOGIN_BTN_RVA = 0xA3998
EXPECTED_METHOD_CODE_SIZE = 107

# CONFIRMED RUNTIME on LDPlayer 32-bit: after /GetUserInfo succeeds,
# HTTP.WaitForGetUserInfo calls SohaSDKManager.SetUserInfo(...). The legacy
# Java SohaSDK singleton is null in the offline environment, causing:
# AndroidJavaException -> java.lang.NullPointerException -> setUserConfig(...)
# Patch this telemetry/account-SDK bridge to a no-op so the game can continue.
SOHA_SET_USER_INFO_RVA = 0xCB940
SOHA_SET_USER_INFO_CODE_SIZE = 41

# LoginForm.OnLoginBtnClick -> HTTP.Instance.Login(
#     new OnRequest(HTTP.Instance.WaitForLogin),
#     accountInput.text,
#     passInput.text)
DIRECT_LOGIN_IL = bytes.fromhex(
    "28 8d 11 00 06"      # call HTTP::get_Instance
    "28 8d 11 00 06"      # call HTTP::get_Instance (delegate target)
    "fe 06 e0 11 00 06"   # ldftn HTTP::WaitForLogin
    "73 54 35 00 06"      # newobj OnRequest::.ctor
    "02"                  # ldarg.0
    "7b cf 13 00 04"      # ldfld LoginForm::accountInput
    "6f 7a 34 00 06"      # callvirt UIInput::get_text
    "02"                  # ldarg.0
    "7b d0 13 00 04"      # ldfld LoginForm::passInput
    "6f 7a 34 00 06"      # callvirt UIInput::get_text
    "6f d3 11 00 06"      # callvirt HTTP::Login
    "2a"                  # ret
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u16(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<H", data, off)[0]


def _u32(data: bytes | bytearray, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def _rva_to_offset(data: bytes | bytearray, rva: int) -> int:
    pe_off = _u32(data, 0x3C)
    coff = pe_off + 4
    section_count = _u16(data, coff + 2)
    optional_size = _u16(data, coff + 16)
    optional_off = coff + 20
    section_off = optional_off + optional_size

    for i in range(section_count):
        off = section_off + i * 40
        virtual_size = _u32(data, off + 8)
        virtual_address = _u32(data, off + 12)
        raw_size = _u32(data, off + 16)
        raw_ptr = _u32(data, off + 20)
        size = max(virtual_size, raw_size)
        if virtual_address <= rva < virtual_address + size:
            return raw_ptr + (rva - virtual_address)

    raise ValueError(f"RVA not mapped: 0x{rva:x}")


def _find_metadata_stream(data: bytes | bytearray, wanted: str) -> tuple[int, int]:
    pe_off = _u32(data, 0x3C)
    coff = pe_off + 4
    optional_off = coff + 20
    magic = _u16(data, optional_off)
    data_dir_off = optional_off + (96 if magic == 0x10B else 112)

    cli_rva = _u32(data, data_dir_off + 14 * 8)
    cli_off = _rva_to_offset(data, cli_rva)
    metadata_rva = _u32(data, cli_off + 8)
    metadata_off = _rva_to_offset(data, metadata_rva)

    if data[metadata_off : metadata_off + 4] != b"BSJB":
        raise ValueError("invalid .NET metadata signature")

    version_len = _u32(data, metadata_off + 12)
    pos = metadata_off + 16 + version_len
    pos = (pos + 3) & ~3
    stream_count = _u16(data, pos + 2)
    pos += 4

    for _ in range(stream_count):
        relative_off = _u32(data, pos)
        size = _u32(data, pos + 4)
        pos += 8
        end = data.index(0, pos)
        name = bytes(data[pos:end]).decode("ascii")
        pos = (end + 4) & ~3
        if name == wanted:
            return metadata_off + relative_off, size

    raise ValueError(f"metadata stream not found: {wanted}")


def patch_user_string(data: bytearray, us_index: int, value: str) -> None:
    if not value.isascii():
        raise ValueError("base URL must be ASCII")

    us_off, us_size = _find_metadata_stream(data, "#US")
    entry = us_off + us_index
    if entry >= us_off + us_size:
        raise ValueError("#US index out of range")

    old_len = data[entry]
    if old_len & 0x80:
        raise ValueError("target string uses multi-byte compressed length; unsupported by targeted patcher")

    payload = value.encode("utf-16le") + b"\x00"
    new_len = len(payload)
    if new_len >= 0x80:
        raise ValueError("new URL is too long for the one-byte #US length used by this APK")
    if new_len > old_len:
        raise ValueError(f"new URL is too long ({new_len} bytes > original slot {old_len} bytes)")

    old_payload = bytes(data[entry + 1 : entry + 1 + old_len])
    old_text = old_payload[:-1].decode("utf-16le", errors="replace")
    expected = "http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx"
    if old_text != expected:
        raise ValueError(f"unexpected login URL at #US index: {old_text!r}")

    data[entry] = new_len
    data[entry + 1 : entry + 1 + new_len] = payload
    if new_len < old_len:
        data[entry + 1 + new_len : entry + 1 + old_len] = b"\x00" * (old_len - new_len)


def _fat_method_layout(data: bytearray, rva: int, expected_code_size: int) -> tuple[int, int, int]:
    method_off = _rva_to_offset(data, rva)
    flags = _u16(data, method_off)
    if flags & 0x3 != 0x3:
        raise ValueError(f"method at RVA 0x{rva:x} is not a fat IL method as expected")

    header_dwords = (flags >> 12) & 0xF
    header_size = header_dwords * 4
    code_size = _u32(data, method_off + 4)
    if code_size != expected_code_size:
        raise ValueError(
            f"unexpected method code size at RVA 0x{rva:x}: "
            f"{code_size} (expected {expected_code_size})"
        )
    return method_off, header_size, code_size


def _replace_fat_method_body(
    data: bytearray,
    rva: int,
    expected_code_size: int,
    replacement_il: bytes,
) -> None:
    method_off, header_size, code_size = _fat_method_layout(data, rva, expected_code_size)
    if len(replacement_il) > code_size:
        raise ValueError("replacement IL does not fit original method")

    code_off = method_off + header_size
    struct.pack_into("<I", data, method_off + 4, len(replacement_il))
    data[code_off : code_off + len(replacement_il)] = replacement_il
    data[code_off + len(replacement_il) : code_off + code_size] = b"\x00" * (
        code_size - len(replacement_il)
    )


def patch_login_button(data: bytearray) -> None:
    _replace_fat_method_body(
        data,
        ON_LOGIN_BTN_RVA,
        EXPECTED_METHOD_CODE_SIZE,
        DIRECT_LOGIN_IL,
    )


def patch_soha_set_user_info(data: bytearray) -> None:
    # A single IL ret is sufficient: SetUserInfo returns void and is only a
    # bridge into the legacy Soha Android SDK. Offline gameplay does not need it.
    _replace_fat_method_body(
        data,
        SOHA_SET_USER_INFO_RVA,
        SOHA_SET_USER_INFO_CODE_SIZE,
        b"\x2a",
    )


def patch_assembly(assembly: bytes, base_url: str) -> bytes:
    data = bytearray(assembly)
    patch_user_string(data, LOGIN_URL_US_INDEX, base_url)
    patch_login_button(data)
    patch_soha_set_user_info(data)
    return bytes(data)


def patch_apk(input_apk: Path, output_apk: Path, base_url: str) -> None:
    original = input_apk.read_bytes()
    actual_sha = sha256_bytes(original)
    if actual_sha != EXPECTED_APK_SHA256:
        raise SystemExit(
            "Refusing to patch an unknown APK.\n"
            f"Expected SHA-256: {EXPECTED_APK_SHA256}\n"
            f"Actual SHA-256:   {actual_sha}"
        )

    with zipfile.ZipFile(io.BytesIO(original), "r") as src:
        assembly = src.read(ASSEMBLY_PATH)
        patched_assembly = patch_assembly(assembly, base_url)

        with zipfile.ZipFile(output_apk, "w") as dst:
            for info in src.infolist():
                upper_name = info.filename.upper()
                if upper_name.startswith("META-INF/") and upper_name.endswith((".RSA", ".DSA", ".EC", ".SF", ".MF")):
                    # Original APK signatures become invalid after Assembly-CSharp.dll changes.
                    continue
                content = patched_assembly if info.filename == ASSEMBLY_PATH else src.read(info.filename)
                # Preserve archive metadata/compression where practical; signing is a separate step.
                dst.writestr(info, content)

    print(f"Patched APK written to: {output_apk}")
    print(f"Login base URL: {base_url}")
    print("Patched legacy SohaSDKManager.SetUserInfo to no-op for offline runtime.")
    print("IMPORTANT: the rebuilt APK must be zipaligned/signed before Android will install it.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch Dai Minh Chu 8.0.2 for local login server")
    parser.add_argument("input_apk", type=Path)
    parser.add_argument("output_apk", type=Path)
    parser.add_argument(
        "--base-url",
        default="http://10.0.2.2:8000/Server/Webservice/User.asmx",
        help="HTTP base URL embedded into HTTP.loginURL; client appends /Login",
    )
    args = parser.parse_args()

    patch_apk(args.input_apk, args.output_apk, args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
