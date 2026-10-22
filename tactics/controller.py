"""Application operations and animation handoff, independent of Pygame.

The injected presentation provides play_attack(values), update(seconds), busy and
clear(). It never receives live entities. A no-op implementation supports callers
without a window; a successful attack still resolves on the next update().
"""

from .actions import ActionResult, UIAction
from .battle import Battle
from .board import Board
from .scenario import Scenario
from .view_models import AttackPresentation, BattleView, build_battle_view


class NullPresentation:
    busy = False

    def play_attack(self, result):
        pass

    def update(self, elapsed):
        pass

    def clear(self):
        pass


class Controller:
    def __init__(self, scenario: Scenario, presentation=None):
        self._board = Board(scenario)
        self._battle = Battle(self._board)
        self._presentation = NullPresentation() if presentation is None else presentation
        self._selected_uid = self._battle.active_unit.uid

    def _unit(self, uid):
        return next((unit for unit in self._board.units if unit.uid == uid), None)

    def _select_active(self):
        actor = self._battle.active_unit
        self._selected_uid = actor.uid if actor is not None else None

    def get_view_state(self) -> BattleView:
        return build_battle_view(self._board, self._battle, self._unit(self._selected_uid))

    def select(self, uid: str) -> ActionResult:
        if self._battle.phase == "resolving":
            return ActionResult(False, "resolving")
        unit = self._unit(uid)
        if unit is None or not unit.alive:
            return ActionResult(False, "unknown_or_dead_unit")
        self._selected_uid = uid
        return ActionResult(True)

    def move_to(self, cell) -> ActionResult:
        """Move the active actor; legality remains exclusively in Battle."""
        if not self._battle.move(cell):
            return ActionResult(False, "illegal_move")
        self._select_active()
        return ActionResult(True)

    def attack(self, target_uid: str) -> ActionResult:
        target = self._unit(target_uid)
        if target is None or not self._battle.attack(target):
            return ActionResult(False, "illegal_target")
        result = self._battle.pending_attack
        self._select_active()
        self._presentation.play_attack(AttackPresentation(
            result.actor.uid, result.target.uid, tuple(result.target.cell),
            result.target.team, result.damage, result.killed,
        ))
        return ActionResult(True)

    def click_cell(self, cell) -> ActionResult:
        """Inspect any living unit, or move/attack when inspecting the active actor."""
        if self._battle.phase == "resolving":
            return ActionResult(False, "resolving")
        if cell is None:
            return ActionResult(False, "outside_board")
        unit = self._board.unit_at(cell)
        actor = self._battle.active_unit
        if actor is not None and self._selected_uid == actor.uid:
            if self.move_to(cell):
                return ActionResult(True)
            if unit is not None and self.attack(unit.uid):
                return ActionResult(True)
        if unit is not None:
            return self.select(unit.uid)
        return ActionResult(False, "no_action")

    def handle_action(self, action: UIAction) -> ActionResult:
        if self._battle.phase == "resolving":
            return ActionResult(False, "resolving")
        if action is UIAction.UNDO:
            return self.undo()
        if action is UIAction.SKIP_PHASE and self._battle.phase in ("move", "attack"):
            self._battle.skip_phase()
        elif action is UIAction.END_TURN and self._battle.end_turn():
            pass
        else:
            return ActionResult(False, "unavailable_action")
        self._select_active()
        return ActionResult(True)

    def undo(self) -> ActionResult:
        if not self._battle.undo():
            return ActionResult(False, "undo_unavailable")
        self._presentation.clear()
        self._select_active()
        return ActionResult(True)

    def update(self, elapsed):
        self._presentation.update(max(0, elapsed))
        if self._battle.phase == "resolving" and not self._presentation.busy:
            self._battle.finish_attack()
            self._select_active()
