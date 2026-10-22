"""Detached board-render data; the complete application/UI view belongs to M2."""

from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

from .models import Cell


@dataclass(frozen=True)
class BoardUnitView:
    uid: str
    team: str
    cell: Cell
    health: int
    max_health: int


@dataclass(frozen=True)
class BoardView:
    cols: int
    rows: int
    obstacles: FrozenSet[Cell]
    units: Tuple[BoardUnitView, ...]
    active_uid: Optional[str]
    selected_uid: Optional[str]
    move_cells: FrozenSet[Cell]
    attack_cells: FrozenSet[Cell]
    target_cells: FrozenSet[Cell]


def build_board_view(board, battle, selected):
    """Project existing legal queries into values; never expose live Unit objects."""
    active = battle.active_unit
    move_cells = attack_cells = target_cells = frozenset()
    if active is not None and selected is active:
        if battle.phase == "move":
            move_cells = frozenset(battle.movement_range())
        elif battle.phase == "attack":
            attack_cells = frozenset(board.neighbors(active.cell)) - board.obstacles
            target_cells = frozenset(unit.cell for unit in battle.attack_targets())
    return BoardView(
        board.cols, board.rows, frozenset(board.obstacles),
        tuple(BoardUnitView(unit.uid, unit.team, tuple(unit.cell), unit.health, unit.max_health)
              for unit in board.living_units),
        active.uid if active is not None else None,
        selected.uid if selected is not None else None,
        move_cells, attack_cells, target_cells,
    )
