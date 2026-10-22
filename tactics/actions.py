"""Semantic UI actions; no keyboard codes or button geometry in the controller."""

from dataclasses import dataclass
from enum import Enum


class UIAction(Enum):
    SKIP_PHASE = "skip_phase"
    END_TURN = "end_turn"
    UNDO = "undo"


@dataclass(frozen=True)
class ActionResult:
    accepted: bool
    reason: str = ""

    def __bool__(self):
        return self.accepted
