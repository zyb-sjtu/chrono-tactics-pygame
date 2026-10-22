"""Mutable unit state and shared grid coordinates; no scene or rendering data."""

from dataclasses import dataclass
from typing import Tuple

Cell = Tuple[int, int]


@dataclass(eq=False)
class Unit:
    uid: str
    name: str
    team: str
    role: str
    cell: Cell
    health: int = 100
    max_health: int = 100
    attack: int = 10
    defense: int = 5
    speed: int = 10
    movement: int = 3

    @property
    def alive(self):
        return self.health > 0
