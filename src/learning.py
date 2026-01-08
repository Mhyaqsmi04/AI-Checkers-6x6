from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class ExperienceEntry:
    win: int = 0
    loss: int = 0
    draw: int = 0

    def update(self, result: int) -> None:
        # result: +1 black win, -1 white win, 0 draw
        if result == 1:
            self.win += 1
        elif result == -1:
            self.loss += 1
        else:
            self.draw += 1

    def value(self) -> float:
        # bounded value in [-1, 1]
        denom = self.win + self.loss + self.draw + 1
        return (self.win - self.loss) / denom


class ExperienceDB:
    """A tiny experience table to implement the 'bonus' learning part.

    We store (position_key -> (win, loss, draw)) from Black's perspective.
    At eval time, we add a small bonus based on past outcomes.
    """

    def __init__(self, path: str = "experience.json"):
        self.path = Path(path)
        self.table: Dict[str, ExperienceEntry] = {}
        self.load()

    @staticmethod
    def _k_to_str(key: Tuple[int, ...]) -> str:
        # keys are tuples of small ints; stringify for JSON
        return ",".join(map(str, key))

    @staticmethod
    def _str_to_k(s: str) -> Tuple[int, ...]:
        if not s:
            return tuple()
        return tuple(int(x) for x in s.split(","))

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            obj = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(obj, dict):
                return
            self.table = {}
            for k, v in obj.items():
                if not isinstance(v, dict):
                    continue
                self.table[k] = ExperienceEntry(
                    win=int(v.get("win", 0)),
                    loss=int(v.get("loss", 0)),
                    draw=int(v.get("draw", 0)),
                )
        except Exception:
            # ignore corrupt file
            self.table = {}

    def save(self) -> None:
        obj = {k: {"win": e.win, "loss": e.loss, "draw": e.draw} for k, e in self.table.items()}
        self.path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_value(self, key: Tuple[int, ...]) -> float:
        e = self.table.get(self._k_to_str(key))
        return e.value() if e else 0.0

    def update_game(self, visited_keys: List[Tuple[int, ...]], result: int) -> None:
        # to reduce bias, update each unique state once per game
        seen = set(visited_keys)
        for k in seen:
            ks = self._k_to_str(k)
            if ks not in self.table:
                self.table[ks] = ExperienceEntry()
            self.table[ks].update(result)
