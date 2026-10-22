"""Runtime units and immutable rule values; no scene or rendering data."""

from dataclasses import asdict, dataclass
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


@dataclass(frozen=True)
class UnitSnapshot:
    """Complete unit values; no reference to a running entity or presentation."""

    uid: str
    name: str
    team: str
    role: str
    cell: Cell
    health: int
    max_health: int
    attack: int
    defense: int
    speed: int
    movement: int

    @classmethod
    def capture(cls, unit):
        values = asdict(unit)
        values["cell"] = tuple(unit.cell)
        return cls(**values)

    def create_unit(self):
        return Unit(**asdict(self))


@dataclass(frozen=True)
class AttackResult:
    resolution_id: int
    actor_uid: str
    target_uid: str
    target_cell: Cell
    target_team: str
    damage: int
    previous_hp: int
    current_hp: int
    killed: bool
