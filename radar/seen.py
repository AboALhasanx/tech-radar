"""Cross-run memory of what has already been shown.

The SQLite store is per-machine; GitHub Actions starts from an empty runner
every time. A committed JSON set keeps "already seen" working across runs, so
a returning reader does not get the same story five times.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Signal, url_hash


class SeenSet:
    def __init__(self, path: str = "data/seen.json", cap: int = 60000) -> None:
        self.path = Path(path)
        self.cap = cap
        self.ids: list[str] = []
        self._set: set[str] = set()
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text("utf-8"))
                self.ids = list(data.get("ids", []))
                self._set = set(self.ids)
            except (json.JSONDecodeError, OSError):
                self.ids, self._set = [], set()

    def is_seen(self, signal: Signal) -> bool:
        return url_hash(signal.url) in self._set

    def mark(self, signal: Signal) -> None:
        sid = url_hash(signal.url)
        if sid not in self._set:
            self._set.add(sid)
            self.ids.append(sid)

    def save(self) -> None:
        # keep the newest ids; older ones fall off and may reappear, which is
        # acceptable and keeps the file bounded
        if len(self.ids) > self.cap:
            self.ids = self.ids[-self.cap :]
            self._set = set(self.ids)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"ids": self.ids}), encoding="utf-8")
        tmp.replace(self.path)

    def __len__(self) -> int:
        return len(self._set)
