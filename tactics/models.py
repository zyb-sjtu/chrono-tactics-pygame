"""Unit attributes and the initial scenario. All numbers are placeholders."""

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


def create_allies():
    return (
        Unit("A1", "先锋", "ally", "近卫", (1, 1), speed=12),
        Unit("A2", "斥候", "ally", "侦察", (1, 3), health=80, speed=14, movement=4),
        Unit("A3", "卫士", "ally", "守备", (2, 6), health=120, max_health=120, speed=10, movement=2),
    )


DUMMIES = ((6, 1), (5, 4), (6, 6))
OBSTACLES = frozenset(((3, 1), (3, 2), (3, 3), (4, 5), (4, 6)))


def create_enemies():
    return tuple(
        Unit("D{}".format(index), "木桩{}".format(index), "enemy", "训练木桩", cell, speed=speed)
        for index, (cell, speed) in enumerate(zip(DUMMIES, (11, 9, 8)), start=1)
    )
