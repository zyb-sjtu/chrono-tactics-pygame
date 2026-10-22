"""Immutable, validated scenario inputs and fresh runtime-unit construction."""

from dataclasses import asdict, dataclass
from typing import FrozenSet, Tuple

from .models import Cell, Unit


def _cell(value, label):
    if (not isinstance(value, (tuple, list)) or len(value) != 2
            or any(type(number) is not int for number in value)):
        raise ValueError("{} must be a pair of integer grid coordinates".format(label))
    return tuple(value)


@dataclass(frozen=True)
class UnitSpawn:
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

    def __post_init__(self):
        object.__setattr__(self, "cell", _cell(self.cell, "unit {} cell".format(self.uid)))


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    cols: int
    rows: int
    units: Tuple[UnitSpawn, ...]
    obstacles: FrozenSet[Cell] = frozenset()

    def __post_init__(self):
        if not isinstance(self.scenario_id, str) or not self.scenario_id.strip():
            raise ValueError("scenario_id must be a nonempty string")
        if any(type(value) is not int or value <= 0 for value in (self.cols, self.rows)):
            raise ValueError("scenario dimensions must be positive integers")
        object.__setattr__(self, "units", tuple(self.units))
        object.__setattr__(self, "obstacles", frozenset(_cell(cell, "obstacle") for cell in self.obstacles))
        for cell in self.obstacles:
            self._check_bounds(cell, "obstacle")
        occupied = set(self.obstacles)
        uids = set()
        teams = set()
        for spawn in self.units:
            if not isinstance(spawn, UnitSpawn):
                raise ValueError("scenario units must be immutable UnitSpawn values")
            for name in ("uid", "name", "role"):
                value = getattr(spawn, name)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("unit {} must be a nonempty string".format(name))
            if spawn.uid in uids:
                raise ValueError("duplicate unit uid: {}".format(spawn.uid))
            if spawn.team not in ("ally", "enemy"):
                raise ValueError("unit {} has an unknown team".format(spawn.uid))
            self._check_bounds(spawn.cell, spawn.uid)
            if spawn.cell in occupied:
                raise ValueError("unit {} overlaps an obstacle or another unit".format(spawn.uid))
            for name in ("health", "max_health", "attack", "defense", "speed", "movement"):
                value = getattr(spawn, name)
                if type(value) is not int or value < 0:
                    raise ValueError("unit {} {} must be a nonnegative integer".format(spawn.uid, name))
            if not 0 < spawn.health <= spawn.max_health:
                raise ValueError("unit {} must start alive with health <= max_health".format(spawn.uid))
            occupied.add(spawn.cell)
            uids.add(spawn.uid)
            teams.add(spawn.team)
        if teams != {"ally", "enemy"}:
            raise ValueError("a scenario must start with at least one living unit on each team")

    def _check_bounds(self, cell, label):
        if not (0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows):
            raise ValueError("{} cell {} is outside the scenario".format(label, cell))

    def create_units(self):
        """Each battle owns its Unit instances; the reusable scenario stays unchanged."""
        return tuple(Unit(**asdict(spawn)) for spawn in self.units)


def default_scenario():
    return Scenario(
        "training_ground", 8, 8,
        (
            UnitSpawn("A1", "先锋", "ally", "近卫", (1, 1), speed=12),
            UnitSpawn("A2", "斥候", "ally", "侦察", (1, 3), health=80, speed=14, movement=4),
            UnitSpawn("A3", "卫士", "ally", "守备", (2, 6), health=120, max_health=120, speed=10, movement=2),
            UnitSpawn("D1", "木桩1", "enemy", "训练木桩", (6, 1), speed=11),
            UnitSpawn("D2", "木桩2", "enemy", "训练木桩", (5, 4), speed=9),
            UnitSpawn("D3", "木桩3", "enemy", "训练木桩", (6, 6), speed=8),
        ),
        frozenset(((3, 1), (3, 2), (3, 3), (4, 5), (4, 6))),
    )
