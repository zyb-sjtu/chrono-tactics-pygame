"""M1 renderer/view contracts, separate from the retained gameplay checks."""

from dataclasses import FrozenInstanceError, asdict, replace
import unittest
from unittest.mock import patch

import pygame

from tactics.actions import UIAction
from tactics.battle import Battle
from tactics.controller import Controller
from tactics.board import Board
from tactics.board_renderer import BoardRenderer
from tactics.game import Game
from tactics.geometry import BoardGeometry
from tactics.panel import InfoPanel
from tactics.scenario import Scenario, UnitSpawn, default_scenario
from tactics.view_models import build_board_view


class RenderBoundaryChecks(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.board = Board(default_scenario())
        self.battle = Battle(self.board)
        self.actor = self.battle.active_unit

    def tearDown(self):
        pygame.quit()

    def test_view_is_detached_and_deeply_read_only(self):
        view = build_board_view(self.board, self.battle, self.actor)
        unit_view = next(unit for unit in view.units if unit.uid == self.actor.uid)
        self.actor.health = 1
        self.actor.cell = (0, 0)
        self.assertEqual((unit_view.health, unit_view.cell), (80, (1, 3)))
        self.assertIsInstance(view.move_cells, frozenset)
        self.assertIsInstance(view.units, tuple)
        with self.assertRaises(FrozenInstanceError):
            unit_view.health = 0
        with self.assertRaises(FrozenInstanceError):
            view.active_uid = "D1"

    def test_ranges_follow_selection_phase_and_legal_queries(self):
        view = build_board_view(self.board, self.battle, self.actor)
        self.assertEqual(view.move_cells, self.battle.movement_range())
        self.assertFalse(view.attack_cells)
        hidden = build_board_view(self.board, self.battle, self.board.enemies[0])
        self.assertFalse(hidden.move_cells or hidden.attack_cells or hidden.target_cells)
        self.battle.move((4, 4))
        view = build_board_view(self.board, self.battle, self.actor)
        self.assertFalse(view.move_cells)
        self.assertEqual(view.attack_cells, {(4, 3), (3, 4), (5, 4)})
        self.assertEqual(view.target_cells, {(5, 4)})
        self.battle.attack(self.board.enemies[1])
        resolving = build_board_view(self.board, self.battle, self.actor)
        self.assertFalse(resolving.move_cells or resolving.attack_cells or resolving.target_cells)

    def test_renderer_needs_only_values_and_preserves_state_and_surface_clip(self):
        view = build_board_view(self.board, self.battle, self.actor)
        before = [asdict(unit) for unit in self.board.units]
        geometry = BoardGeometry(8, 8, 32, (11, 13))
        surface = pygame.Surface((300, 300))
        surface.fill("magenta")
        surface.set_clip((5, 5, 280, 280))
        clip = surface.get_clip()
        with patch.object(self.battle, "movement_range", side_effect=AssertionError("renderer queried rules")), \
             patch.object(self.battle, "attack_targets", side_effect=AssertionError("renderer queried targets")):
            BoardRenderer(geometry).draw(surface, view)
        self.assertEqual([asdict(unit) for unit in self.board.units], before)
        self.assertEqual(surface.get_clip(), clip)
        self.assertEqual(tuple(surface.get_at((10, 13)))[:3], (255, 0, 255))
        self.assertNotEqual(tuple(surface.get_at((11, 13)))[:3], (255, 0, 255))
        with self.assertRaises(ValueError):
            BoardRenderer(geometry).draw(surface, replace(view, cols=5))

    def test_injected_scenario_uses_its_dimensions_for_window_clicks_and_effects(self):
        scenario = Scenario("small", 5, 4, (
            UnitSpawn("blue", "Blue", "ally", "test", (0, 0), speed=20, movement=4, attack=17),
            UnitSpawn("red", "Red", "enemy", "test", (3, 0), health=50, speed=5),
        ), frozenset(((1, 0),)))
        game = Game(scenario)
        self.assertEqual(game.geometry.bounds, (0, 0, 320, 256))
        self.assertEqual(game.screen.get_size(), (704, 512))
        self.assertIs(game.panel.hit_test((344, 284)), UIAction.SKIP_PHASE)
        self.assertIs(game.effects.geometry, game.geometry)
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                            pos=game.geometry.cell_center((2, 0))))
        self.assertEqual(game.controller.get_view_state().phase, "attack")
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                            pos=game.geometry.cell_center((3, 0))))
        self.assertEqual(next(unit.health for unit in game.controller.get_view_state().units if unit.uid == "red"), 33)
        self.assertEqual(game.effects.damage_texts[0].cell, (3, 0))
        game.draw()
        game.update(1)
        game.controller.undo()
        self.assertEqual(next(unit.health for unit in game.controller.get_view_state().units if unit.uid == "red"), 50)
        game.draw()

    def test_panel_hit_test_returns_intent_with_half_open_bounds_at_custom_width(self):
        panel = InfoPanel(320)
        for position, expected in (
            ((344, 284), UIAction.SKIP_PHASE), ((505, 321), UIAction.SKIP_PHASE),
            ((518, 284), UIAction.END_TURN), ((679, 321), UIAction.END_TURN),
            ((528, 14), UIAction.UNDO), ((679, 45), UIAction.UNDO),
            ((343, 284), None), ((506, 303), None), ((344, 322), None),
            ((680, 30), None), ((528, 46), None), ((0, 0), None),
        ):
            with self.subTest(position=position):
                self.assertIs(panel.hit_test(position), expected)
        for name in ("undo_button", "skip_button", "end_button"):
            self.assertFalse(hasattr(panel, name), name)

    def test_panel_draws_saved_view_without_access_to_controller_or_rules(self):
        controller = Controller(default_scenario())
        saved = controller.get_view_state()
        controller.handle_action(UIAction.END_TURN)
        panel = InfoPanel()
        surface = pygame.Surface((896, 512))
        with patch.object(panel, "text", wraps=panel.text) as text:
            panel.draw(surface, saved)
        expected = "当前行动：斥候 [A2]" if panel.chinese else "Active: A2 [A2]"
        self.assertTrue(any(call.args[1] == expected for call in text.call_args_list))
        self.assertEqual(saved.active.uid, "A2")
        self.assertEqual(controller.get_view_state().active.uid, "A1")


if __name__ == "__main__":
    unittest.main()
