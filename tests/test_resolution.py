"""M3 snapshot and completion contracts, runnable with python -S."""

from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
import json
import unittest

from tactics.actions import UIAction
from tactics.battle import Battle
from tactics.board import Board
from tactics.controller import Controller
from tactics.models import Unit, UnitSnapshot
from tactics.scenario import default_scenario
from tactics.view_models import ResolutionToken


def scenario_with(**changes):
    scenario = default_scenario()
    return replace(scenario, units=tuple(
        replace(unit, **changes.get(unit.uid, {})) for unit in scenario.units))


def assert_pure(test, value):
    if is_dataclass(value):
        test.assertTrue(value.__dataclass_params__.frozen)
        for field in fields(value):
            assert_pure(test, getattr(value, field.name))
    elif isinstance(value, tuple):
        for child in value:
            assert_pure(test, child)
    else:
        test.assertIn(type(value), (str, int, bool, type(None)))


class SnapshotAndResultChecks(unittest.TestCase):
    def setUp(self):
        self.board = Board(default_scenario())
        self.battle = Battle(self.board)

    def attack(self):
        self.assertTrue(self.battle.move((4, 4)))
        self.assertTrue(self.battle.attack(next(unit for unit in self.board.units if unit.uid == "D2")))
        return self.battle.pending_attack

    def test_snapshots_are_deeply_immutable_values_covering_every_unit_field(self):
        snapshot = self.battle.history[0]
        self.assertEqual({field.name for field in fields(UnitSnapshot)},
                         {field.name for field in fields(Unit)})
        assert_pure(self, snapshot)
        self.assertEqual(snapshot.order_uids, ("A2", "A1", "D1", "A3", "D2", "D3"))
        with self.assertRaises(FrozenInstanceError):
            snapshot.units[0].health = 0
        with self.assertRaises(FrozenInstanceError):
            snapshot.index = 2
        self.assertIsInstance(json.loads(json.dumps(asdict(snapshot)))["units"], list)
        self.assertFalse(hasattr(snapshot, "_next_resolution_id"))

    def test_saved_values_do_not_change_with_runtime_damage_attributes_or_logs(self):
        snapshot = self.battle.history[0]
        before = asdict(snapshot)
        self.attack()
        for unit in self.board.units:
            unit.health = 1
            unit.attack = 999
            unit.cell = (0, 0)
            unit.name = "Changed"
        self.battle.notify("changed", "changed")
        self.assertEqual(asdict(snapshot), before)

    def test_undo_recreates_all_attributes_and_canonical_slots_by_uid(self):
        self.board = Board(scenario_with(A2={"health": 800, "max_health": 1000, "attack": 300},
                                         D2={"health": 5}))
        self.battle = Battle(self.board)
        original_units = self.board.units
        before = self.battle.history[0]
        result = self.attack()
        self.battle.finish_attack(result.resolution_id)
        self.battle.move((0, 1))
        for unit in self.board.units:
            unit.name, unit.role, unit.defense = "Changed", "Other", 999
            unit.speed, unit.movement, unit.max_health, unit.health = 1, 0, 1, 1
        self.assertTrue(self.battle.undo())
        self.assertEqual(self.battle._snapshot(), before)
        for old, current in zip(original_units, self.board.units):
            self.assertIsNot(old, current)
        by_uid = {unit.uid: unit for unit in self.board.units}
        self.assertTrue(all(unit is by_uid[unit.uid] for unit in self.battle.entry_order))
        self.assertEqual((by_uid["D2"].health, by_uid["A2"].health, by_uid["A2"].max_health), (5, 800, 1000))
        self.battle.move((4, 4))
        self.assertFalse(self.battle.attack(original_units[4]))  # Stale object identity is not a target.
        self.assertTrue(self.battle.attack(by_uid["D2"]))

    def test_dead_state_and_round_are_restored_through_multiple_undos(self):
        self.board = Board(scenario_with(D2={"health": 5}))
        self.battle = Battle(self.board)
        result = self.attack()
        self.battle.finish_attack(result.resolution_id)
        after_kill = self.battle.history[-1]
        for _ in range(4):
            self.battle.end_turn()
        self.assertEqual((self.battle.round_number, self.battle.active_unit.uid), (2, "A2"))
        for _ in range(4):
            self.assertTrue(self.battle.undo())
        self.assertEqual(self.battle._snapshot(), after_kill)
        self.assertEqual(next(unit.health for unit in self.board.units if unit.uid == "D2"), 0)
        self.assertNotIn("D2", tuple(unit.uid for unit in self.battle.order))
        self.assertTrue(self.battle.undo())
        self.assertEqual(next(unit.health for unit in self.board.units if unit.uid == "D2"), 5)
        self.assertIn("D2", tuple(unit.uid for unit in self.battle.order))

    def test_rule_completion_requires_matching_id_and_ids_do_not_rewind(self):
        self.assertFalse(self.battle.attack(self.board.enemies[1]))
        first = self.attack()
        self.assertEqual(first.resolution_id, 1)
        before = self.battle._snapshot()
        self.assertFalse(self.battle.finish_attack(first.resolution_id + 1))
        self.assertEqual(self.battle._snapshot(), before)
        self.assertTrue(self.battle.finish_attack(first.resolution_id))
        self.assertFalse(self.battle.finish_attack(first.resolution_id))
        self.battle.undo()
        second = self.attack()
        self.assertGreater(second.resolution_id, first.resolution_id)
        self.assertFalse(self.battle.finish_attack(first.resolution_id))
        self.assertEqual(self.battle.phase, "resolving")
        self.assertTrue(self.battle.finish_attack(second.resolution_id))

    def test_attack_results_capture_ids_location_full_damage_and_hp_change(self):
        for attack, health, expected_hp, killed in ((10, 100, 90, False), (300, 7, 0, True), (0, 7, 7, False)):
            with self.subTest(attack=attack):
                self.board = Board(scenario_with(A2={"attack": attack}, D2={"health": health}))
                self.battle = Battle(self.board)
                result = self.attack()
                assert_pure(self, result)
                self.assertEqual((result.actor_uid, result.target_uid, result.target_team,
                                  result.target_cell, result.damage, result.previous_hp,
                                  result.current_hp, result.killed),
                                 ("A2", "D2", "enemy", (5, 4), attack, health, expected_hp, killed))
                with self.assertRaises(FrozenInstanceError):
                    result.current_hp = 100
                self.board.enemies[1].cell = (7, 7)
                self.board.enemies[1].health = 1
                self.assertEqual((result.target_cell, result.current_hp), ((5, 4), expected_hp))


class DelayedPresentation:
    """Can deliver in-flight notifications even after clear; controller must reject them."""

    def __init__(self):
        self.events = []
        self.completions = []
        self.clears = 0
        self.busy = False
        self.on_clear = None

    def play_attack(self, event):
        self.events.append(event)

    def update(self, elapsed):
        completed, self.completions = tuple(self.completions), []
        return completed

    def clear(self):
        self.clears += 1
        if self.on_clear is not None:
            self.on_clear()


class CompletionContractChecks(unittest.TestCase):
    def setUp(self):
        self.presentation = DelayedPresentation()
        self.controller = Controller(default_scenario(), self.presentation)

    @property
    def view(self):
        return self.controller.get_view_state()

    def attack(self):
        self.assertTrue(self.controller.move_to((4, 4)))
        self.assertTrue(self.controller.attack("D2"))
        return self.presentation.events[-1].token

    def test_matching_completion_is_accepted_only_once(self):
        token = self.attack()
        self.assertEqual(self.view.pending_resolution, token)
        assert_pure(self, self.presentation.events[-1])
        self.assertTrue(self.controller.complete_presentation(token))
        after = self.view
        self.assertEqual(after.active.uid, "A1")
        self.assertIsNone(after.pending_resolution)
        self.assertFalse(self.controller.complete_presentation(token))
        self.assertEqual(self.view, after)

    def test_wrong_generation_or_resolution_is_rejected_without_side_effects(self):
        token = self.attack()
        before = self.view
        for wrong in (replace(token, generation=token.generation + 1),
                      replace(token, resolution_id=token.resolution_id + 1), None):
            self.assertFalse(self.controller.complete_presentation(wrong))
            self.assertEqual(self.view, before)
        self.assertTrue(self.controller.complete_presentation(token))

    def test_busy_false_without_completion_cannot_handoff(self):
        self.attack()
        self.assertFalse(self.presentation.busy)
        before = self.view
        self.controller.update(10000)
        self.assertEqual(self.view, before)

    def test_background_busy_does_not_block_explicit_attack_completion(self):
        token = self.attack()
        self.presentation.busy = True  # Future ambient/idle animation may continue forever.
        self.presentation.completions.append(token)
        self.controller.update(0)
        self.assertEqual((self.view.active.uid, self.view.phase), ("A1", "move"))

    def test_undo_replay_rejects_old_completion_before_and_during_new_attack(self):
        old = self.attack()
        self.controller.complete_presentation(old)
        self.controller.undo()
        self.assertEqual(self.view.presentation_generation, old.generation + 1)
        self.assertFalse(self.controller.complete_presentation(old))
        current = self.attack()
        self.assertGreater(current.resolution_id, old.resolution_id)
        before = self.view
        self.assertFalse(self.controller.complete_presentation(old))
        self.assertEqual(self.view, before)
        self.assertTrue(self.controller.complete_presentation(current))

    def test_restart_during_attack_cancels_old_generation_even_when_ids_repeat(self):
        old = self.attack()
        self.assertTrue(self.controller.restart())
        self.assertEqual((self.view.presentation_generation, self.view.active.cell), (1, (1, 3)))
        self.assertEqual(next(unit.health for unit in self.view.units if unit.uid == "D2"), 100)
        self.assertFalse(self.view.can_undo)
        current = self.attack()
        self.assertEqual(old.resolution_id, current.resolution_id)
        self.assertNotEqual(old.generation, current.generation)
        self.assertFalse(self.controller.complete_presentation(old))
        self.assertEqual(self.view.pending_resolution, current)
        self.assertTrue(self.controller.complete_presentation(current))

    def test_generation_is_invalidated_before_clear_can_deliver_late_callback(self):
        old = self.attack()
        results = []

        def late_callback():
            self.assertEqual(self.view.presentation_generation, old.generation + 1)
            self.assertIsNone(self.view.pending_resolution)
            results.append(self.controller.complete_presentation(old))

        self.presentation.on_clear = late_callback
        self.controller.restart()  # Old token was valid and resolving immediately before clear.
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0])
        self.assertEqual((self.view.active.uid, self.view.phase), ("A2", "move"))
        self.assertEqual(self.presentation.clears, 1)

    def test_failed_undo_does_not_advance_generation_or_clear_current_presentation(self):
        before = self.view
        self.assertFalse(self.controller.undo())
        self.assertEqual(self.view, before)
        self.controller.handle_action(UIAction.END_TURN)
        self.controller.undo()
        self.attack()
        before = self.view
        clears = self.presentation.clears
        self.assertFalse(self.controller.undo())
        self.assertEqual(self.view, before)
        self.assertEqual(self.presentation.clears, clears)

    def test_batch_of_late_duplicate_and_current_notifications_hands_off_once(self):
        old = self.attack()
        self.controller.complete_presentation(old)
        self.presentation.completions.append(old)
        self.controller.undo()  # In-flight notification survives adapter.clear().
        current = self.attack()
        self.presentation.completions += [current, current, old]
        self.controller.update(0)
        after = self.view
        self.assertEqual((after.active.uid, after.round_number), ("A1", 1))
        self.controller.update(1)
        self.assertEqual(self.view, after)

    def test_final_kill_completion_cannot_repeat_after_finish_or_undo(self):
        scenario = scenario_with(D2={"health": 5})
        scenario = replace(scenario, units=tuple(unit for unit in scenario.units if unit.uid in ("A2", "D2")))
        self.controller = Controller(scenario, self.presentation)
        token = self.attack()
        self.assertFalse(self.view.finished)
        self.controller.complete_presentation(token)
        self.assertEqual(self.view.winner, "ally")
        after = self.view
        self.assertFalse(self.controller.complete_presentation(token))
        self.assertEqual(self.view, after)
        self.controller.undo()
        self.assertFalse(self.controller.complete_presentation(token))
        self.assertEqual(next(unit.health for unit in self.view.units if unit.uid == "D2"), 5)


if __name__ == "__main__":
    unittest.main()
