from __future__ import annotations

import os
from pathlib import Path

from state import SaveStore

DEFAULT_SAVE_FILE = Path(__file__).resolve().parent / "local_data" / "save.json"
path = os.getenv("DMC_SAVE_FILE", str(DEFAULT_SAVE_FILE))
store = SaveStore(path)
store.reset()
print(f"Reset offline save: {store.path}")
