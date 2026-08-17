from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

# CONFIRMED from embedded ConfigFile/GiangHo in the target APK.
# Only structural mission counts are kept here; no original dialogue/config dump.
CHAPTER_MISSION_COUNTS = [
    6, 7, 9, 10, 10, 12, 12, 13, 14, 15, 15, 15, 16, 16, 16, 16, 16,
    16, 16, 16, 14, 16, 16, 15, 16, 17, 16, 15, 16, 16, 13, 15, 15, 15,
    15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
    16, 16, 16, 16, 16, 16, 16,
]

START_HEROES = {
    "NV_PhongThanhDuong": {"Mau": 260, "Cong": 284, "Thu": 155, "Noicong": 234},
    "NV_LenhHoXung": {"Mau": 180, "Cong": 180, "Thu": 60, "Noicong": 300},
    "NV_SoLuuHuong": {"Mau": 250, "Cong": 150, "Thu": 160, "Noicong": 305},
}


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "hero_code": None,
        "hero_level": 1,
        "hero_exp": 0,
        "account": {
            "DisplayName": "Offline",
            "Level": 1,
            "Exp": 0,
            "ExpMax": 100,
            "Bac": 10000,
            "Vang": 100,
            "Vip": 0,
        },
        "giangho": [],
    }


class SaveStore:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.data = _default_state()
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.data = _default_state()
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        base = _default_state()
        if isinstance(raw, dict):
            base.update(raw)
            if isinstance(raw.get("account"), dict):
                account = _default_state()["account"]
                account.update(raw["account"])
                base["account"] = account
        self.data = base

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def reset(self) -> None:
        self.data = _default_state()
        if self.path.exists():
            self.path.unlink()

    @property
    def hero_code(self) -> str | None:
        value = self.data.get("hero_code")
        return str(value) if value else None

    def choose_hero(self, code: str) -> None:
        if code not in START_HEROES:
            raise ValueError(f"Unsupported start character: {code}")
        self.data["hero_code"] = code
        self.data["hero_level"] = 1
        self.data["hero_exp"] = 0
        self.save()

    def hero_payload(self) -> dict[str, Any] | None:
        code = self.hero_code
        if not code:
            return None
        stats = START_HEROES[code]
        return {
            "Id": 1,
            "Name": code,
            "Level": int(self.data.get("hero_level", 1)),
            "Exp": int(self.data.get("hero_exp", 0)),
            "ExpMax": 100,
            "Mau": stats["Mau"],
            "Cong": stats["Cong"],
            "Thu": stats["Thu"],
            "Noicong": stats["Noicong"],
            "VoCong1Level": 1,
            "KyNgoCocLevel": 1,
        }

    def account_payload(self) -> dict[str, Any]:
        return deepcopy(self.data["account"])

    def add_bac(self, value: int) -> None:
        self.data["account"]["Bac"] = int(self.data["account"].get("Bac", 0)) + int(value)

    def _chapter(self, chapter_idx: int, create: bool = False) -> dict[str, Any] | None:
        chapters = self.data["giangho"]
        for chapter in chapters:
            if int(chapter.get("GiangHoIndx", -1)) == chapter_idx:
                return chapter

        if not create:
            return None

        # Client unlock semantics are contiguous. A new chapter is legal only
        # when it is chapter 0 or the previous chapter is complete.
        if chapter_idx == 0:
            pass
        else:
            prev = self._chapter(chapter_idx - 1, create=False)
            if not prev or int(prev.get("HoanThanh", 0)) <= 0:
                raise ValueError(f"GiangHo chapter {chapter_idx} is locked")

        chapter = {
            "GiangHoIndx": chapter_idx,
            "HoanThanh": 0,
            # Runtime representation; converted to legacy JSON string in payload.
            "missions": [{"S": 0, "T": 0}],
        }
        chapters.append(chapter)
        chapters.sort(key=lambda item: int(item.get("GiangHoIndx", 0)))
        return chapter

    def complete_giangho_battle(self, chapter_idx: int, mission_idx: int, star: int) -> None:
        if not 0 <= chapter_idx < len(CHAPTER_MISSION_COUNTS):
            raise ValueError(f"Invalid GiangHo chapter: {chapter_idx}")
        mission_count = CHAPTER_MISSION_COUNTS[chapter_idx]
        if not 0 <= mission_idx < mission_count:
            raise ValueError(f"Invalid mission {mission_idx} for chapter {chapter_idx}")
        if not 0 <= star <= 3:
            raise ValueError(f"Invalid star value: {star}")

        chapter = self._chapter(chapter_idx, create=True)
        assert chapter is not None
        missions = chapter.setdefault("missions", [{"S": 0, "T": 0}])

        # The client uses the serialized record-list length as its mission
        # unlock boundary, so only an already-visible mission is legal here.
        if mission_idx >= len(missions):
            raise ValueError(f"Mission {chapter_idx}:{mission_idx} is locked")

        record = missions[mission_idx]
        record["S"] = max(int(record.get("S", 0)), star)
        record["T"] = int(record.get("T", 0)) + 1

        if star > 0:
            if mission_idx == mission_count - 1:
                chapter["HoanThanh"] = 1
            elif len(missions) == mission_idx + 1:
                missions.append({"S": 0, "T": 0})

        self.save()

    def giangho_payload(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for chapter in sorted(
            self.data.get("giangho", []),
            key=lambda item: int(item.get("GiangHoIndx", 0)),
        ):
            missions = chapter.get("missions") or [{"S": 0, "T": 0}]
            result.append(
                {
                    "GiangHoIndx": int(chapter.get("GiangHoIndx", 0)),
                    "HoanThanh": int(chapter.get("HoanThanh", 0)),
                    # CONFIRMED: HTTPUserInfo.GetNhiemVuGiangHo calls
                    # JsonMapper.ToObject<List<HTTPNhiemVuGiangHoRecord>>(Nhiemvu).
                    "Nhiemvu": json.dumps(
                        missions, ensure_ascii=False, separators=(",", ":")
                    ),
                }
            )
        return result

    def user_info_payload(self) -> dict[str, Any]:
        hero = self.hero_payload()
        payload: dict[str, Any] = {
            "ErrorCode": 1,
            "ErrorMsg": "",
            "Account": self.account_payload(),
            "GiaTriThoiGian": {
                "LuotNV": 20,
                "LuotNVMax": 20,
                "LuotTD": 10,
                "LuotTDMax": 10,
                "LatTheBai": 0,
            },
            "NhanVat": [hero] if hero else [],
            "GiangHo": self.giangho_payload(),
        }
        if hero:
            payload["DoiHinh"] = {"Slot1": 1}
        return payload
