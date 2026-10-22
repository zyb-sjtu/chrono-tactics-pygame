"""Speed order and one move / one adjacent attack per turn; no AI."""

from dataclasses import asdict, dataclass
from typing import Optional

from .models import Unit


@dataclass(frozen=True)
class AttackResult:
    actor: Unit
    target: Unit
    damage: int
    killed: bool


@dataclass(frozen=True)
class TurnSnapshot:
    units: tuple
    order: tuple
    index: int
    round_number: int
    phase: str
    log: tuple
    winner: Optional[str]


class Battle:
    def __init__(self, board):
        self.board = board
        # Python's stable sort preserves entry order when speeds are equal.
        self.entry_order = tuple(sorted(board.units, key=lambda unit: -unit.speed))
        self.index = 0
        self.round_number = 1
        self.phase = "move"
        self.winner = None
        self.pending_attack = None
        self.log = []
        self.notify("按速度从高到低行动，双方均手动操作", "Speed order; both teams are controlled manually.")
        self.history = [self._snapshot()]

    @property
    def order(self):
        return tuple(unit for unit in self.entry_order if unit.alive)

    @property
    def active_unit(self):
        return None if self.finished else self.entry_order[self.index]

    @property
    def finished(self):
        return self.winner is not None

    @property
    def can_undo(self):
        return self.phase != "resolving" and len(self.history) > 1

    def _snapshot(self):
        return TurnSnapshot(tuple((unit, asdict(unit)) for unit in self.board.units),
                            self.entry_order, self.index, self.round_number,
                            self.phase, tuple(self.log), self.winner)

    def undo(self):
        """Restore the previous unit turn's start, discarding this turn as well."""
        if not self.can_undo:
            return False
        self.history.pop()
        snapshot = self.history[-1]
        self.board.units = tuple(unit for unit, _ in snapshot.units)
        for unit, values in snapshot.units:
            for name, value in values.items():
                setattr(unit, name, value)
        self.entry_order = snapshot.order
        self.index = snapshot.index
        self.round_number = snapshot.round_number
        self.phase = snapshot.phase
        self.log = list(snapshot.log)
        self.winner = snapshot.winner
        self.pending_attack = None
        return True

    def notify(self, chinese, english):
        self.log.append((chinese, english))
        self.log = self.log[-2:]

    def movement_range(self):
        return self.board.reachable_cells(self.active_unit) if self.phase == "move" else set()

    def attack_targets(self):
        if self.phase != "attack":
            return ()
        actor = self.active_unit
        neighbors = self.board.neighbors(actor.cell)
        return tuple(unit for unit in self.board.living_units
                     if unit.team != actor.team and unit.cell in neighbors)

    def move(self, destination):
        if destination not in self.movement_range():
            return False
        actor = self.active_unit
        actor.cell = destination
        self.phase = "attack"
        self.notify("{} 已移动；请选择相邻敌方攻击".format(actor.name),
                    "{} moved. Choose an adjacent enemy.".format(actor.uid))
        return True

    def attack(self, target):
        if target not in self.attack_targets():
            return False
        actor = self.active_unit
        damage = max(0, actor.attack)
        target.health = max(0, target.health - damage)
        self.pending_attack = AttackResult(actor, target, damage, not target.alive)
        self.phase = "resolving"
        self.notify("{} 攻击 {}，造成 {} 点伤害".format(actor.name, target.name, damage),
                    "{} attacked {} for {} damage.".format(actor.uid, target.uid, damage))
        if not target.alive:
            self.notify("{} 被击杀".format(target.name), "{} was defeated.".format(target.uid))
        return True

    def finish_attack(self):
        """Called once the presentation has finished its attack/death effects."""
        if self.phase != "resolving":
            return False
        self.pending_attack = None
        self._advance()
        return True

    def skip_phase(self):
        if self.phase == "move":
            self.phase = "attack"
            self.notify("{} 跳过移动；请选择相邻敌方".format(self.active_unit.name),
                        "{} skipped movement. Choose a target.".format(self.active_unit.uid))
        elif self.phase == "attack":
            self.end_turn()

    def end_turn(self):
        if self.phase not in ("move", "attack"):
            return False
        self.notify("{} 结束行动".format(self.active_unit.name),
                    "{} ended their turn.".format(self.active_unit.uid))
        self._advance()
        return True

    def _advance(self):
        teams = {unit.team for unit in self.board.living_units}
        if len(teams) <= 1:
            self.winner = next(iter(teams), "draw")
            self.phase = "finished"
            self.history.append(self._snapshot())
            return
        # Keep entry slots stable so deaths before/after the current slot cannot
        # shift the actor or cause an extra/skipped turn at the round boundary.
        for step in range(1, len(self.entry_order) + 1):
            absolute_index = self.index + step
            next_index = absolute_index % len(self.entry_order)
            if self.entry_order[next_index].alive:
                self.round_number += absolute_index // len(self.entry_order)
                self.index = next_index
                break
        self.phase = "move"
        self.history.append(self._snapshot())
