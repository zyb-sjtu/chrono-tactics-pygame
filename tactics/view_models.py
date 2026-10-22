"""Detached, immutable values shared by the application and presentation layers."""

from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

from .models import AttackResult, Cell


@dataclass(frozen=True)
class BoardUnitView:
    uid: str
    team: str
    cell: Cell
    health: int
    max_health: int
    definition_id: str = ""


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


@dataclass(frozen=True)
class UnitView:
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
    definition_id: str = ""

    @property
    def alive(self):
        return self.health > 0


@dataclass(frozen=True)
class BattleView:
    board: BoardView
    units: Tuple[UnitView, ...]
    active: Optional[UnitView]
    selected: Optional[UnitView]
    phase: str
    round_number: int
    winner: Optional[str]
    order: Tuple[UnitView, ...]
    log: Tuple[Tuple[str, str], ...]
    can_undo: bool
    can_skip: bool
    can_end_turn: bool
    input_locked: bool
    presentation_generation: int
    pending_resolution: Optional["ResolutionToken"]

    @property
    def finished(self):
        return self.winner is not None


@dataclass(frozen=True)
class ResolutionToken:
    """Identity of one blocking presentation in one controller generation."""

    generation: int
    resolution_id: int


@dataclass(frozen=True)
class AttackPresentation:
    token: ResolutionToken
    result: AttackResult


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
        tuple(BoardUnitView(unit.uid, unit.team, tuple(unit.cell), unit.health, unit.max_health, unit.definition_id)
              for unit in board.living_units),
        active.uid if active is not None else None,
        selected.uid if selected is not None else None,
        move_cells, attack_cells, target_cells,
    )


def build_battle_view(board, battle, selected, presentation_generation, pending_resolution):
    """Build one consistent snapshot, including units that a later undo may revive."""
    units = tuple(UnitView(
        unit.uid, unit.name, unit.team, unit.role, tuple(unit.cell),
        unit.health, unit.max_health, unit.attack, unit.defense, unit.speed, unit.movement,
        unit.definition_id,
    ) for unit in board.units)
    by_uid = {unit.uid: unit for unit in units}
    actor = battle.active_unit
    can_act = battle.phase in ("move", "attack")
    return BattleView(
        build_board_view(board, battle, selected), units,
        by_uid[actor.uid] if actor is not None else None,
        by_uid[selected.uid] if selected is not None else None,
        battle.phase, battle.round_number, battle.winner,
        tuple(by_uid[unit.uid] for unit in battle.order),
        tuple(tuple(message) for message in battle.log),
        battle.can_undo, can_act, can_act, battle.phase == "resolving",
        presentation_generation, pending_resolution,
    )
