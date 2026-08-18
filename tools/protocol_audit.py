from __future__ import annotations

import argparse
import importlib.util
import re
import zipfile
from pathlib import Path

ASSEMBLY_PATH = "assets/bin/Data/Managed/Assembly-CSharp.dll"
ENDPOINT_RE = re.compile(r"^/[A-Za-z][A-Za-z0-9_]+$")
UTF16_ASCII_RE = re.compile(rb"(?:[ -~]\x00){3,}")


def load_assembly(path: Path) -> bytes:
    if path.suffix.lower() == ".apk":
        with zipfile.ZipFile(path, "r") as zf:
            return zf.read(ASSEMBLY_PATH)
    return path.read_bytes()


def extract_endpoints(data: bytes) -> list[str]:
    found: set[str] = set()
    for match in UTF16_ASCII_RE.finditer(data):
        value = match.group().decode("utf-16le", errors="ignore")
        if ENDPOINT_RE.fullmatch(value):
            found.add(value[1:])
    return sorted(found)


def load_server_static(path: Path) -> set[str]:
    spec = importlib.util.spec_from_file_location("dmc_static_endpoints", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return set(module.STATIC_ENDPOINTS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Đại Minh Chủ 8.0.2 endpoint strings against local server coverage")
    parser.add_argument("client", type=Path, help="original APK or Assembly-CSharp.dll")
    parser.add_argument("--static-file", type=Path, default=Path("server/static_endpoints.py"))
    parser.add_argument("--write", type=Path, help="optional text file containing all extracted endpoints")
    args = parser.parse_args()

    endpoints = extract_endpoints(load_assembly(args.client))
    covered = load_server_static(args.static_file)
    missing = sorted(set(endpoints) - covered)
    stale = sorted(covered - set(endpoints))

    print(f"Client endpoints: {len(endpoints)}")
    print(f"Static server coverage: {len(covered)}")
    print(f"Missing from server allowlist: {len(missing)}")
    for item in missing:
        print(f"  MISSING /{item}")
    print(f"Allowlist entries absent from this client: {len(stale)}")
    for item in stale:
        print(f"  STALE /{item}")

    if args.write:
        args.write.write_text("\n".join(f"/{x}" for x in endpoints) + "\n", encoding="utf-8")
        print(f"Wrote: {args.write}")

    raise SystemExit(1 if missing else 0)


if __name__ == "__main__":
    main()
