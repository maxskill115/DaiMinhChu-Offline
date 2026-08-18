from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

MANIFEST = ".dmc_apk_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_target(root: Path, name: str) -> Path:
    target = (root / name).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        raise ValueError(f"Unsafe archive path: {name}")
    return target


def classify(name: str) -> str:
    n = name.lower()
    if n.startswith("assets/bin/data/managed/"): return "managed-dll"
    if n.startswith("assets/bin/data/"): return "unity-data"
    if n.startswith("assets/"): return "asset"
    if n.startswith("res/"): return "android-resource"
    if n.startswith("lib/"): return "native-lib"
    if n.endswith((".png", ".jpg", ".jpeg", ".webp", ".tga", ".bmp")): return "image"
    if n.endswith((".wav", ".mp3", ".ogg", ".aac", ".m4a")): return "audio"
    if n.endswith((".mp4", ".webm", ".avi")): return "video"
    if n.endswith((".xml", ".json", ".txt", ".csv")): return "text-config"
    return "other"


def unpack(apk: Path, out: Path, clean: bool) -> None:
    if clean and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    with zipfile.ZipFile(apk, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                safe_target(out, info.filename).mkdir(parents=True, exist_ok=True); continue
            target = safe_target(out, info.filename); target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, target.open("wb") as dst: shutil.copyfileobj(src, dst)
            entries.append({"name": info.filename, "compress_type": info.compress_type,
                            "date_time": list(info.date_time), "external_attr": info.external_attr,
                            "file_size": info.file_size, "crc": info.CRC, "category": classify(info.filename)})
    manifest = {"source_apk": str(apk.resolve()), "source_sha256": sha256_file(apk), "entries": entries}
    (out / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Unpacked: {apk} -> {out}")
    print(f"Files: {len(entries)}")
    for cat in sorted({e['category'] for e in entries}):
        print(f"  {cat:18} {sum(1 for e in entries if e['category']==cat)}")
    print("NOTE: Unity serialized assets/bundles remain binary. Use AssetRipper/UABE externally to export/import textures, audio, animations, prefabs, then replace the edited files in this workspace.")


def repack(workspace: Path, output: Path) -> None:
    manifest_path = workspace / MANIFEST
    if not manifest_path.exists(): raise SystemExit(f"Missing {MANIFEST}; unpack with this tool first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")); original = {e["name"]: e for e in manifest.get("entries", [])}
    files = [p for p in workspace.rglob("*") if p.is_file() and p.name != MANIFEST]
    if output.exists(): output.unlink()
    with zipfile.ZipFile(output, "w") as zf:
        for path in sorted(files):
            rel = path.relative_to(workspace).as_posix()
            upper = rel.upper()
            if upper.startswith("META-INF/") and upper.endswith((".RSA", ".DSA", ".EC", ".SF", ".MF")):
                continue
            old = original.get(rel)
            info = zipfile.ZipInfo(rel)
            if old:
                info.compress_type = int(old.get("compress_type", zipfile.ZIP_DEFLATED))
                dt = old.get("date_time")
                if dt and len(dt) == 6: info.date_time = tuple(dt)
                info.external_attr = int(old.get("external_attr", 0))
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())
    print(f"Repacked unsigned APK: {output}")
    print(f"SHA256: {sha256_file(output)}")
    print("Next: zipalign -> apksigner. Original signatures are intentionally removed.")


def scan(workspace: Path) -> None:
    rows = []
    for p in workspace.rglob("*"):
        if p.is_file() and p.name != MANIFEST:
            rel = p.relative_to(workspace).as_posix(); rows.append((classify(rel), p.stat().st_size, rel))
    for cat, size, rel in sorted(rows): print(f"{cat:18} {size:10}  {rel}")


def apktool_decode(apk: Path, out: Path) -> None:
    exe = shutil.which("apktool") or shutil.which("apktool.bat")
    if not exe: raise SystemExit("apktool not found in PATH")
    subprocess.run([exe, "d", "-f", str(apk), "-o", str(out)], check=True)


def apktool_build(folder: Path, output: Path) -> None:
    exe = shutil.which("apktool") or shutil.which("apktool.bat")
    if not exe: raise SystemExit("apktool not found in PATH")
    subprocess.run([exe, "b", str(folder), "-o", str(output)], check=True)


def main() -> None:
    p = argparse.ArgumentParser(description="DMC APK workspace unpack/repack helper")
    sub = p.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("unpack"); u.add_argument("apk", type=Path); u.add_argument("out", type=Path); u.add_argument("--clean", action="store_true")
    r = sub.add_parser("repack"); r.add_argument("workspace", type=Path); r.add_argument("output", type=Path)
    s = sub.add_parser("scan"); s.add_argument("workspace", type=Path)
    d = sub.add_parser("apktool-decode"); d.add_argument("apk", type=Path); d.add_argument("out", type=Path)
    b = sub.add_parser("apktool-build"); b.add_argument("folder", type=Path); b.add_argument("output", type=Path)
    a = p.parse_args()
    if a.cmd == "unpack": unpack(a.apk, a.out, a.clean)
    elif a.cmd == "repack": repack(a.workspace, a.output)
    elif a.cmd == "scan": scan(a.workspace)
    elif a.cmd == "apktool-decode": apktool_decode(a.apk, a.out)
    elif a.cmd == "apktool-build": apktool_build(a.folder, a.output)


if __name__ == "__main__": main()
