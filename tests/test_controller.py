"""Application contracts; run with python -S, without Pygame or a display."""

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
import ast
from pathlib import Path
import unittest

from tactics.actions import UIAction
from tactics.controller import Controller
from tactics.scenario import default_scenario


class HeldPresentation:
    """Test-controlled completion: advancing time alone does not finish an attack."""

    def __init__(self):
        self.busy = False
        self.results = []
        self.elapsed = []
        self.clears = 0
        self.pending = None

    def play_attack(self, result):
        self.results.append(result)
        self.pending = result.token
        self.busy = True

    def update(self, elapsed):
        self.elapsed.append(elapsed)
        if not self.busy and self.pending is not None:
            token, self.pending = self.pending, None
            return (token,)
        return ()

    def clear(self):
        self.clears += 1
        self.busy = False
        self.pending = None


def changed_scenario(**changes):
    scenario = default_scenario()
    return replace(scenario, units=tuple(
        replace(unit, **changes.get(unit.uid, {})) for unit in scenario.units))


class ControllerChecks(unittest.TestCase):
    def setUp(self):
        self.presentation = HeldPresentation()
        self.controller = Controller(default_scenario(), self.presentation)

    @property
    def view(self):
        return self.controller.get_view_state()

    def unit(self, uid):
        return next(unit for unit in self.view.units if unit.uid == uid)

    def start_attack(self):
        self.assertTrue(self.controller.move_to((4, 4)))
        self.assertTrue(self.controller.attack("D2"))

    def finish(self):
        self.presentation.busy = False
        self.controller.update(0)

    def test_initial_view_contains_complete_stats_order_log_ranges_and_buttons(self):
        view = self.view
        self.assertEqual(view.active, view.selected)
        self.assertEqual((view.active.uid, view.active.health, view.active.max_health,
                          view.active.attack, view.active.defense, view.active.speed,
                          view.active.movement, view.active.role),
                         ("A2", 80, 100, 10, 5, 14, 4, "侦察"))
        self.assertEqual(tuple(unit.uid for unit in view.order), ("A2", "A1", "D1", "A3", "D2", "D3"))
        self.assertEqual(view.board.active_uid, view.active.uid)
        self.assertEqual(view.board.selected_uid, view.selected.uid)
        self.assertTrue(view.can_skip and view.can_end_turn and view.board.move_cells and view.log)
        self.assertFalse(view.can_undo or view.input_locked or view.finished)

    def test_full_view_has_only_deeply_immutable_values(self):
        def check(value):
            if is_dataclass(value):
                self.assertTrue(value.__dataclass_params__.frozen)
                for field in fields(value):
                    check(getattr(value, field.name))
            elif isinstance(value, (tuple, frozenset)):
                for child in value:
                    check(child)
            else:
                self.assertIs(type(value) in (str, int, bool, type(None)), True)
        check(self.view)
        with self.assertRaises(FrozenInstanceError):
            self.view.selected.health = 0
        with self.assertRaises(FrozenInstanceError):
            self.view.can_undo = True
        with self.assertRaises(AttributeError):
            self.view.board.move_cells.add((7, 7))

    def test_old_views_remain_detached_after_move_damage_handoff_and_undo(self):
        before = self.view
        self.start_attack()
        resolving = self.view
        self.finish()
        self.controller.undo()
        self.assertEqual(replace(self.view, presentation_generation=before.presentation_generation), before)
        self.assertEqual(before.active.cell, (1, 3))
        self.assertEqual(next(unit.health for unit in before.units if unit.uid == "D2"), 100)
        self.assertEqual(resolving.active.cell, (4, 4))
        self.assertEqual(next(unit.health for unit in resolving.units if unit.uid == "D2"), 90)
        self.assertTrue(resolving.input_locked)

    def test_click_inspection_hides_ranges_and_requires_reselecting_actor(self):
        self.assertTrue(self.controller.click_cell((1, 1)))
        self.assertEqual(self.view.selected.uid, "A1")
        self.assertEqual(self.view.active.uid, "A2")
        self.assertFalse(self.view.board.move_cells)
        before = self.view
        self.assertFalse(self.controller.click_cell((4, 4)))
        self.assertEqual(self.view, before)
        self.controller.click_cell((1, 3))
        self.controller.click_cell((4, 4))
        self.assertEqual((self.view.phase, self.view.active.cell), ("attack", (4, 4)))

    def test_invalid_clicks_and_selection_do_not_change_any_view_state(self):
        before = self.view
        for cell in (None, (-1, 0), (8, 0), (7, 7), (3, 1)):
            result = self.controller.click_cell(cell)
            self.assertFalse(result)
            self.assertTrue(result.reason)
            self.assertEqual(self.view, before)
        self.assertFalse(self.controller.select("missing"))
        self.assertEqual(self.view, before)
        self.assertFalse(self.presentation.results)

    def test_explicit_commands_act_on_active_actor_and_validate_once_in_rules(self):
        self.controller.select("D1")
        self.assertTrue(self.controller.move_to((4, 4)))
        self.assertEqual(self.view.selected.uid, "A2")
        before = self.view
        self.assertFalse(self.controller.move_to((4, 3)))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.attack("D2"))
        self.assertEqual(self.unit("D2").health, 90)

    def test_illegal_attacks_return_failure_without_changing_state_or_playing_effects(self):
        self.assertFalse(self.controller.attack("D2"))  # Before moving/skipping.
        self.controller.move_to((4, 4))
        before = self.view
        for uid in ("missing", "A2", "A1", "D1"):
            result = self.controller.attack(uid)
            self.assertFalse(result)
            self.assertEqual(result.reason, "illegal_target")
            self.assertEqual(self.view, before)
        self.assertFalse(self.presentation.results)

    def test_all_application_inputs_are_locked_while_resolving(self):
        self.start_attack()
        before = self.view
        self.assertTrue(before.input_locked)
        self.assertFalse(before.can_skip or before.can_end_turn or before.can_undo)
        attempts = [lambda: self.controller.select("D1"),
                    lambda: self.controller.click_cell((6, 1)),
                    lambda: self.controller.move_to((4, 3)),
                    lambda: self.controller.attack("D2"), self.controller.undo]
        attempts += [lambda action=action: self.controller.handle_action(action) for action in UIAction]
        for attempt in attempts:
            self.assertFalse(attempt())
            self.assertEqual(self.view, before)
        self.assertEqual(len(self.presentation.results), 1)
        self.assertEqual(self.presentation.clears, 0)

    def test_completion_waits_for_presentation_and_hands_off_only_once(self):
        self.start_attack()
        self.controller.update(100)
        self.assertEqual(self.view.phase, "resolving")
        self.controller.update(-1)
        self.assertEqual(self.presentation.elapsed[-1], 0)
        self.finish()
        handoff = self.view
        self.assertEqual(handoff.active.uid, "A1")
        self.assertEqual(handoff.selected, handoff.active)
        self.assertFalse(handoff.input_locked)
        for _ in range(3):
            self.controller.update(1)
            self.assertEqual(self.view, handoff)

    def test_without_presentation_attack_completes_on_next_update(self):
        self.controller = Controller(default_scenario())
        self.start_attack()
        self.assertEqual(self.view.phase, "resolving")
        self.controller.update(0)
        self.assertEqual(self.view.active.uid, "A1")
        self.assertTrue(self.controller.undo())
        self.assertEqual(self.unit("D2").health, 100)

    def test_undo_clears_effects_restores_previous_turn_and_discards_partial_move(self):
        before = self.view
        self.assertFalse(self.controller.undo())
        self.assertEqual(self.presentation.clears, 0)
        self.start_attack()
        self.finish()
        self.controller.move_to((0, 1))
        self.assertTrue(self.controller.handle_action(UIAction.UNDO))
        self.assertEqual(replace(self.view, presentation_generation=before.presentation_generation), before)
        self.assertEqual(self.presentation.clears, 1)
        self.assertFalse(self.presentation.busy)
        self.assertFalse(self.controller.undo())

    def test_final_kill_waits_then_finishes_and_undo_revives_target(self):
        scenario = changed_scenario(D2={"health": 5})
        scenario = replace(scenario, units=tuple(unit for unit in scenario.units if unit.uid in ("A2", "D2")))
        self.controller = Controller(scenario, self.presentation)
        self.start_attack()
        self.assertFalse(self.view.finished)
        self.assertFalse(self.controller.select("D2"))
        self.assertNotIn("D2", tuple(unit.uid for unit in self.view.board.units))
        self.finish()
        self.assertEqual((self.view.phase, self.view.winner, self.view.active, self.view.selected),
                         ("finished", "ally", None, None))
        before = self.view
        self.assertFalse(self.controller.handle_action(UIAction.END_TURN))
        self.assertFalse(self.controller.handle_action(UIAction.SKIP_PHASE))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.select("A2"))  # Inspection remains available.
        self.assertTrue(self.controller.undo())
        self.assertEqual((self.view.active.uid, self.unit("D2").health), ("A2", 5))
        self.assertEqual(len(self.view.board.units), 2)
        self.assertFalse(self.view.finished)

    def test_semantic_actions_work_for_both_teams_and_round_wrap(self):
        for uid in ("A2", "A1", "D1", "A3", "D2", "D3"):
            self.assertEqual(self.view.active.uid, uid)
            self.assertTrue(self.controller.handle_action(UIAction.SKIP_PHASE))
            self.assertEqual(self.view.phase, "attack")
            self.assertTrue(self.controller.handle_action(UIAction.SKIP_PHASE))
            self.assertEqual(self.view.selected, self.view.active)
        self.assertEqual((self.view.round_number, self.view.active.uid), (2, "A2"))
        self.assertTrue(self.controller.undo())
        self.assertEqual((self.view.round_number, self.view.active.uid), (1, "D3"))

    def test_zero_movement_and_invalid_action_do_not_need_presentation(self):
        self.controller = Controller(changed_scenario(A2={"movement": 0}), self.presentation)
        before = self.view
        self.assertFalse(before.board.move_cells)
        self.assertFalse(self.controller.handle_action("end_turn"))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.handle_action(UIAction.SKIP_PHASE))
        self.assertEqual(self.view.phase, "attack")
        self.assertFalse(self.presentation.results)

    def test_effect_result_is_detached_and_read_only_even_after_undo(self):
        self.start_attack()
        result = self.presentation.results[0].result
        self.assertEqual((result.actor_uid, result.target_uid, result.target_cell,
                          result.target_team, result.damage, result.killed),
                         ("A2", "D2", (5, 4), "enemy", 10, False))
        self.assertFalse(hasattr(result, "target") or hasattr(result, "actor"))
        with self.assertRaises(FrozenInstanceError):
            result.damage = 0
        self.finish()
        self.controller.undo()
        self.assertEqual((result.target_cell, result.damage), ((5, 4), 10))

    def test_presentation_and_game_do_not_import_mutable_rule_objects(self):
        root = Path(__file__).resolve().parents[1] / "tactics"
        for name in ("game", "panel", "effects", "board_renderer"):
            tree = ast.parse((root / (name + ".py")).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, ("board", "battle", "models",
                                                  "tactics.board", "tactics.battle", "tactics.models"), name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name, ("tactics.board", "tactics.battle", "tactics.models"), name)


if __name__ == "__main__":
    unittest.main()
