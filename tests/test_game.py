"""Window input adapters and retained font regression checks."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from tactics.actions import UIAction
from tactics.game import Game
from tactics.panel import InfoPanel
from tactics.settings import CELL_SIZE


class GameChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    @property
    def view(self):
        return self.game.controller.get_view_state()

    def unit(self, uid):
        return next(unit for unit in self.view.units if unit.uid == uid)

    def click(self, position, button=1):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=position, button=button))

    def test_layout_and_initial_scenario(self):
        for name in ("board", "battle", "selected"):
            self.assertFalse(hasattr(self.game, name), name)
        self.assertEqual(self.game.screen.get_size(), (896, 512))
        self.assertEqual(CELL_SIZE, 64)
        self.assertEqual((self.game.geometry.width, self.game.geometry.height), (512, 512))
        cells = [unit.cell for unit in self.view.units] + list(self.view.board.obstacles)
        self.assertEqual(sum(unit.team == "ally" for unit in self.view.units), 3)
        self.assertEqual(sum(unit.team == "enemy" for unit in self.view.units), 3)
        self.assertTrue(self.view.board.obstacles)
        self.assertEqual(len(cells), len(set(cells)))
        self.assertTrue(all(0 <= col < 8 and 0 <= row < 8 for col, row in cells))

    def test_inspect_each_unit_without_changing_turn(self):
        actor = self.view.active
        for unit in self.view.units:
            self.click(self.game.geometry.cell_center(unit.cell))
            self.assertEqual(self.view.selected, unit)
            self.assertEqual(self.view.active, actor)
            self.game.draw()

    def test_invalid_terrain_and_outside_clicks_do_not_consume_action(self):
        before = self.view
        positions = [(511, 511), (530, 20), (-1, 0), (0, 512)]
        positions += [self.game.geometry.cell_center(cell) for cell in self.view.board.obstacles]
        for position in positions:
            self.click(position)
            self.assertEqual(self.view, before)
        self.assertEqual(self.game.geometry.cell_at((511, 511)), (7, 7))

    def test_right_click_does_not_change_selection_or_scenario(self):
        before = self.view
        self.click(self.game.geometry.cell_center((4, 4)), button=3)
        self.assertEqual(self.view, before)

    def test_mouse_move_attack_and_turn_handoff(self):
        actor = self.view.active
        target = self.unit("D2")
        self.click(self.game.geometry.cell_center((4, 4)))
        self.assertEqual(self.view.active.cell, (4, 4))
        self.assertEqual(self.view.phase, "attack")
        self.game.draw()
        self.click(self.game.geometry.cell_center(target.cell))
        self.assertEqual(self.unit("D2").health, target.health - actor.attack)
        self.assertEqual(self.view.phase, "resolving")
        self.assertTrue(self.game.effects.busy)
        self.game.draw()
        self.game.update(1.0)
        self.assertEqual(self.view.selected, self.view.active)
        self.assertNotEqual(self.view.selected.uid, actor.uid)
        self.game.draw()

    def test_inspection_cannot_move_a_unit_out_of_turn(self):
        actor = self.view.active
        other = self.unit("A1")
        self.click(self.game.geometry.cell_center(other.cell))
        self.click(self.game.geometry.cell_center((4, 4)))
        self.assertEqual(self.view.active, actor)
        self.assertEqual(self.unit("A1"), other)
        self.click(self.game.geometry.cell_center(actor.cell))
        self.click(self.game.geometry.cell_center((4, 4)))
        self.assertEqual(self.view.active.cell, (4, 4))

    def test_keyboard_and_sidebar_skip_controls(self):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertEqual(self.view.phase, "attack")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.view.active.uid, "A1")
        # Exercise public input and semantic hit testing, without reading panel rectangles.
        skip = (self.game.geometry.width + 105, 303)
        end = (self.game.geometry.width + 279, 303)
        self.assertIs(self.game.panel.hit_test(skip), UIAction.SKIP_PHASE)
        self.assertIs(self.game.panel.hit_test(end), UIAction.END_TURN)
        self.click(skip)
        self.assertEqual(self.view.phase, "attack")
        self.click(end)
        self.assertEqual(self.view.active.uid, "D1")
        self.assertEqual(self.view.active.team, "enemy")
        self.assertEqual(self.view.selected, self.view.active)
        self.game.draw()

    def test_window_quit_event_exits_main_loop(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.game.run()
        self.assertFalse(self.game.running)
        self.assertFalse(pygame.display.get_init())
        self.assertFalse(pygame.font.get_init())


class FontChecks(unittest.TestCase):
    def setUp(self):
        pygame.font.init()

    def tearDown(self):
        pygame.quit()

    def test_known_windows_font_bypasses_registry_scan(self):
        font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        if not (font_dir / "msyh.ttc").is_file():
            self.skipTest("Microsoft YaHei is not installed on this machine")
        with patch("tactics.panel.pygame.font.match_font", side_effect=TypeError("non-string entry")) as scan:
            panel = InfoPanel()
        self.assertTrue(panel.chinese)
        scan.assert_not_called()

    def test_registry_errors_still_allow_window_render_and_quit(self):
        errors = (TypeError("non-string entry"), OSError("registry unavailable"),
                  ValueError("invalid font"), pygame.error("font discovery failed"))
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with patch("tactics.panel.Path.is_file", return_value=False), \
                     patch("tactics.panel.pygame.font.match_font", side_effect=error):
                    game = Game()
                self.assertFalse(game.panel.chinese)
                game.draw()
                game.controller.select("A1")
                game.draw()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                game.run()
                self.assertFalse(pygame.display.get_init())

    def test_missing_chinese_font_uses_builtin_font(self):
        with patch("tactics.panel.Path.is_file", return_value=False), \
             patch("tactics.panel.pygame.font.match_font", return_value=None):
            panel = InfoPanel()
        self.assertFalse(panel.chinese)
        self.assertGreater(panel.font.render("No selection", True, "white").get_width(), 0)


if __name__ == "__main__":
    unittest.main()
