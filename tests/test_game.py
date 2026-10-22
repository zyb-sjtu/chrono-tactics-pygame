"""Run with: python -m unittest discover -s tests -v"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from tactics.game import Game
from tactics.panel import InfoPanel
from tactics.settings import BOARD_HEIGHT, BOARD_WIDTH, CELL_SIZE, WINDOW_SIZE


class GameChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def click(self, position, button=1):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=position, button=button))

    def test_layout_and_initial_scenario(self):
        self.assertEqual(WINDOW_SIZE, (896, 512))
        self.assertEqual(CELL_SIZE, 64)
        self.assertEqual((BOARD_WIDTH, BOARD_HEIGHT), (512, 512))
        cells = [unit.cell for unit in self.game.board.units] + list(self.game.board.obstacles)
        self.assertEqual(len(self.game.board.allies), 3)
        self.assertEqual(len(self.game.board.enemies), 3)
        self.assertTrue(self.game.board.obstacles)
        self.assertEqual(len(cells), len(set(cells)))
        self.assertTrue(all(0 <= col < 8 and 0 <= row < 8 for col, row in cells))

    def test_inspect_each_unit_without_changing_turn(self):
        actor = self.game.battle.active_unit
        for unit in self.game.board.units:
            self.click(self.game.board.rect(unit.cell).center)
            self.assertIs(self.game.selected, unit)
            self.assertIs(self.game.battle.active_unit, actor)
            self.game.draw()

    def test_invalid_terrain_and_outside_clicks_do_not_consume_action(self):
        actor = self.game.battle.active_unit
        start = actor.cell
        positions = [(511, 511), (530, 20), (-1, 0), (0, 512)]
        positions += [self.game.board.rect(cell).center for cell in self.game.board.obstacles]
        for position in positions:
            self.click(position)
            self.assertEqual(actor.cell, start)
            self.assertEqual(self.game.battle.phase, "move")
        self.assertEqual(self.game.board.cell_at((511, 511)), (7, 7))

    def test_right_click_does_not_change_selection_or_scenario(self):
        before = tuple(unit.cell for unit in self.game.board.units)
        selected = self.game.selected
        self.click(self.game.board.rect((4, 4)).center, button=3)
        self.assertIs(self.game.selected, selected)
        self.assertEqual(tuple(unit.cell for unit in self.game.board.units), before)

    def test_mouse_move_attack_and_turn_handoff(self):
        actor = self.game.battle.active_unit
        target = self.game.board.enemies[1]
        health = target.health
        self.click(self.game.board.rect((4, 4)).center)
        self.assertEqual(actor.cell, (4, 4))
        self.assertEqual(self.game.battle.phase, "attack")
        self.game.draw()
        self.click(self.game.board.rect(target.cell).center)
        self.assertEqual(target.health, health - actor.attack)
        self.assertEqual(self.game.battle.phase, "resolving")
        self.assertTrue(self.game.effects.busy)
        self.game.draw()
        self.game.update(1.0)
        self.assertIs(self.game.selected, self.game.battle.active_unit)
        self.assertIsNot(self.game.selected, actor)
        self.game.draw()

    def test_inspection_cannot_move_a_unit_out_of_turn(self):
        actor = self.game.battle.active_unit
        start = actor.cell
        other = self.game.board.allies[0]
        self.click(self.game.board.rect(other.cell).center)
        self.click(self.game.board.rect((4, 4)).center)
        self.assertEqual(actor.cell, start)
        self.assertEqual(other.cell, (1, 1))
        self.click(self.game.board.rect(actor.cell).center)
        self.click(self.game.board.rect((4, 4)).center)
        self.assertEqual(actor.cell, (4, 4))

    def test_keyboard_and_sidebar_skip_controls(self):
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertEqual(self.game.battle.phase, "attack")
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.game.battle.index, 1)
        self.click(self.game.panel.skip_button.center)
        self.assertEqual(self.game.battle.phase, "attack")
        self.click(self.game.panel.end_button.center)
        self.assertEqual(self.game.battle.index, 2)
        self.assertEqual(self.game.battle.active_unit.team, "enemy")
        self.assertIs(self.game.selected, self.game.battle.active_unit)
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
                game.selected = game.board.allies[0]
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
