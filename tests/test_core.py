"""M1 contracts; runnable with python -S and no third-party packages installed."""

from dataclasses import FrozenInstanceError, replace
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tactics.battle import Battle
from tactics.board import Board
from tactics.geometry import BoardGeometry
from tactics.scenario import Scenario, UnitSpawn, default_scenario


def alternate_scenario():
    return Scenario("detour", 5, 4, (
        UnitSpawn("blue", "Blue", "ally", "test", (0, 0), speed=20, movement=4, attack=17),
        UnitSpawn("red", "Red", "enemy", "test", (3, 0), health=50, speed=5),
    ), frozenset(((1, 0),)))


class ScenarioChecks(unittest.TestCase):
    def test_default_layout_and_stats_match_original(self):
        scenario = default_scenario()
        self.assertEqual((scenario.cols, scenario.rows), (8, 8))
        board = Board(scenario)
        self.assertEqual([(unit.uid, unit.cell, unit.health, unit.max_health, unit.speed, unit.movement)
                          for unit in board.units], [
            ("A1", (1, 1), 100, 100, 12, 3), ("A2", (1, 3), 80, 100, 14, 4),
            ("A3", (2, 6), 120, 120, 10, 2), ("D1", (6, 1), 100, 100, 11, 3),
            ("D2", (5, 4), 100, 100, 9, 3), ("D3", (6, 6), 100, 100, 8, 3),
        ])
        self.assertEqual(board.obstacles, {(3, 1), (3, 2), (3, 3), (4, 5), (4, 6)})
        self.assertTrue(all(unit.attack == 10 and unit.defense == 5 for unit in board.units))

    def test_reused_scenario_does_not_share_runtime_units(self):
        scenario = default_scenario()
        first, second = Board(scenario), Board(scenario)
        first.units[0].health = 1
        first.units[0].cell = (0, 0)
        self.assertEqual(second.units[0].health, 100)
        self.assertEqual(scenario.units[0].cell, (1, 1))
        self.assertIsNot(first.units[0], second.units[0])

    def test_immutable_configuration_normalizes_mutable_inputs(self):
        source = list(alternate_scenario().units)
        obstacles = [[1, 0]]
        scenario = Scenario("copied", 5, 4, source, obstacles)
        source.clear()
        obstacles[0][0] = 4
        self.assertEqual(len(scenario.units), 2)
        self.assertEqual(scenario.obstacles, {(1, 0)})
        with self.assertRaises(FrozenInstanceError):
            scenario.units[0].health = 1

    def test_alternate_board_runs_path_attack_handoff_and_undo(self):
        board = Board(alternate_scenario())
        battle = Battle(board)
        actor, target = board.units
        self.assertEqual(board.neighbors((4, 3)), ((3, 3), (4, 2)))
        self.assertIn((2, 0), battle.movement_range())
        self.assertNotIn((1, 0), battle.movement_range())
        self.assertNotIn((4, 0), battle.movement_range())
        self.assertTrue(battle.move((2, 0)))
        self.assertTrue(battle.attack(target))
        self.assertEqual(target.health, 33)
        battle.finish_attack()
        self.assertIs(battle.active_unit, target)
        self.assertTrue(battle.undo())
        self.assertIs(battle.active_unit, actor)
        self.assertEqual(actor.cell, (0, 0))
        self.assertEqual(target.health, 50)

    def test_rejects_invalid_dimensions_empty_or_one_sided_scenarios(self):
        source = alternate_scenario()
        for changes in ({"cols": 0}, {"rows": -1}, {"cols": True}, {"rows": 3.5},
                        {"scenario_id": ""}, {"units": ()}, {"units": source.units[:1]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(source, **changes)

    def test_rejects_bad_spawn_coordinates_collisions_and_duplicate_ids(self):
        source = alternate_scenario()
        for changes in ({"cell": (5, 0)}, {"cell": (-1, 0)}, {"cell": (1, 0)},
                        {"cell": (3, 0)}, {"cell": (True, 0)}, {"cell": (0.5, 0)}, {"uid": "red"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(source, units=(replace(source.units[0], **changes), source.units[1]))
        for obstacles in ([(5, 0)], [(1,)], [(1, False)]):
            with self.subTest(obstacles=obstacles), self.assertRaises(ValueError):
                replace(source, obstacles=obstacles)

    def test_rejects_invalid_teams_attributes_and_initially_dead_units(self):
        source = alternate_scenario()
        for changes in ({"health": 0}, {"health": 101}, {"max_health": 0}, {"team": "unknown"},
                        {"attack": -1}, {"defense": -1}, {"speed": -1}, {"movement": -1},
                        {"movement": 1.5}, {"speed": True}, {"uid": ""}, {"role": ""}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(source, units=(replace(source.units[0], **changes), source.units[1]))


class GeometryChecks(unittest.TestCase):
    def test_nonzero_origin_and_odd_cell_size_roundtrip(self):
        geometry = BoardGeometry(5, 3, 31, (17, 29))
        self.assertEqual(geometry.bounds, (17, 29, 155, 93))
        self.assertEqual(geometry.cell_rect((1, 1)), (48, 60, 31, 31))
        for row in range(3):
            for col in range(5):
                self.assertEqual(geometry.cell_at(geometry.cell_center((col, row))), (col, row))

    def test_half_open_pixel_edges_and_sidebar(self):
        geometry = BoardGeometry(8, 8, 64)
        self.assertEqual(geometry.cell_at((0, 0)), (0, 0))
        self.assertEqual(geometry.cell_at((511, 511)), (7, 7))
        for pixel in ((512, 0), (0, 512), (-1, 0), (0, -1), (799, 511)):
            self.assertIsNone(geometry.cell_at(pixel))
        offset = BoardGeometry(2, 2, 32, (10, 20))
        self.assertIsNone(offset.cell_at((9, 20)))
        self.assertEqual(offset.cell_at((73, 83)), (1, 1))
        self.assertIsNone(offset.cell_at((74, 84)))

    def test_invalid_geometry_and_cells_are_rejected(self):
        for args in ((0, 8, 64), (8, -1, 64), (8, 8, 0), (True, 8, 64), (8, 8, 32.5)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                BoardGeometry(*args)
        with self.assertRaises(ValueError):
            BoardGeometry(8, 8, 64, (0.5, 0))
        for cell in ((8, 0), (-1, 0), (0, 8), (False, 0), (0.5, 0)):
            with self.subTest(cell=cell), self.assertRaises(ValueError):
                BoardGeometry(8, 8, 64).cell_rect(cell)


class CoreBoundaryChecks(unittest.TestCase):
    def test_board_has_no_pixel_or_rendering_entrypoints(self):
        board = Board(default_scenario())
        for name in ("draw", "rect", "cell_at", "label_font"):
            self.assertFalse(hasattr(board, name), name)

    def test_full_rule_flow_without_site_packages_and_with_pygame_blocked(self):
        root = Path(__file__).resolve().parents[1]
        script = """
import importlib.abc
import importlib.util
import sys
assert importlib.util.find_spec('pygame') is None
class NoPygame(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'pygame' or fullname.startswith('pygame.'):
            raise AssertionError('Core imported Pygame: ' + fullname)
sys.meta_path.insert(0, NoPygame())
from tactics.board import Board
from tactics.battle import Battle
from tactics.scenario import default_scenario
from tactics.geometry import BoardGeometry
from tactics.view_models import build_board_view
board = Board(default_scenario())
battle = Battle(board)
assert battle.move((4, 4))
assert battle.attack(board.enemies[1])
assert board.enemies[1].health == 90
battle.finish_attack()
assert battle.undo()
assert board.enemies[1].health == 100
assert build_board_view(board, battle, battle.active_unit).active_uid == 'A2'
assert BoardGeometry(8, 8, 64).cell_at((511, 511)) == (7, 7)
assert 'pygame' not in sys.modules
print('core-without-pygame: OK')
"""
        result = subprocess.run([sys.executable, "-S", "-c", script], cwd=str(root),
                                env={**os.environ, "PYTHONPATH": str(root)},
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("core-without-pygame: OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
