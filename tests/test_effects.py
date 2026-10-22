"""Actual window rendering, animation lifecycle, input lock and rewind controls."""

from dataclasses import replace
import unittest
from unittest.mock import patch

import pygame

from tactics.scenario import default_scenario
from tactics.game import Game


class CombatInteractionChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    @property
    def view(self):
        return self.game.controller.get_view_state()

    @property
    def actor(self):
        return next(unit for unit in self.view.units if unit.uid == "A2")

    @property
    def target(self):
        return next(unit for unit in self.view.units if unit.uid == "D2")

    def tearDown(self):
        pygame.quit()

    def click(self, position):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    def start_attack(self, lethal=False, final=False):
        if lethal:
            scenario = default_scenario()
            units = tuple(replace(unit, health=5) if unit.uid == "D2" else unit
                          for unit in scenario.units)
            if final:
                units = tuple(unit for unit in units if unit.uid in ("A2", "D2"))
            self.game = Game(replace(scenario, units=units))
        self.click(self.game.geometry.cell_center((4, 4)))
        self.click(self.game.geometry.cell_center(self.target.cell))

    def test_damage_popup_and_controls_are_locked_until_effect_finishes(self):
        self.start_attack()
        self.assertEqual(self.game.effects.damage_texts[0].amount, self.actor.attack)
        self.game.update(0.2)
        self.assertAlmostEqual(self.game.effects.damage_texts[0].age, 0.2)
        self.game.draw()
        for key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
            self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        for position in ((617, 303), (791, 303), (796, 30)):
            self.click(position)
        self.click(self.game.geometry.cell_center(self.target.cell))
        self.assertEqual(self.target.health, self.target.max_health - self.actor.attack)
        self.assertEqual(self.view.active, self.actor)
        self.assertEqual(self.view.phase, "resolving")
        self.game.update(1.0)
        self.assertFalse(self.game.effects.busy)
        self.assertEqual(self.view.phase, "move")
        self.assertEqual(self.view.active.uid, "A1")

    def test_defeated_body_animates_then_disappears_from_actual_surface(self):
        self.start_attack(lethal=True)
        self.assertEqual(len(self.game.effects.deaths), 1)
        self.assertFalse(self.target.alive)
        self.game.draw()
        center = self.game.geometry.cell_center(self.target.cell)
        background = (42, 55, 70)
        self.assertNotEqual(tuple(self.game.screen.get_at(center))[:3], background)
        self.game.update(0.4)
        self.assertEqual(len(self.game.effects.deaths), 1)
        self.game.draw()
        self.game.update(0.3)
        self.assertEqual(len(self.game.effects.deaths), 0)
        self.assertTrue(self.game.effects.busy)  # Floating damage text finishes later.
        self.game.draw()
        self.assertEqual(tuple(self.game.screen.get_at(center))[:3], background)
        self.game.update(0.3)
        self.assertFalse(self.game.effects.busy)

    def test_sidebar_undo_revives_target_and_clears_visual_state(self):
        self.start_attack(lethal=True)
        self.game.update(1.0)
        self.click((self.game.geometry.width + 284, 30))
        self.assertEqual(self.target.health, 5)
        self.assertIn(self.target.uid, tuple(unit.uid for unit in self.view.board.units))
        self.assertEqual(self.view.active, self.actor)
        self.assertEqual(self.view.selected, self.actor)
        self.assertEqual(self.actor.cell, (1, 3))
        self.assertFalse(self.game.effects.busy)
        self.game.draw()

    def test_backspace_rewinds_previous_turn_and_discards_partial_current_move(self):
        self.start_attack()
        self.game.update(1.0)
        self.click(self.game.geometry.cell_center((0, 1)))
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertEqual(self.view.active.uid, "A2")
        self.assertEqual(self.target.health, self.target.max_health)
        self.assertEqual(next(unit.cell for unit in self.view.units if unit.uid == "A1"), (1, 1))
        self.assertEqual(self.view.phase, "move")

    def test_finished_battle_is_renderable_and_can_be_undone(self):
        self.start_attack(lethal=True, final=True)
        self.game.update(1.0)
        self.assertTrue(self.view.finished)
        self.game.draw()
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertTrue(self.view.finished)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertFalse(self.view.finished)
        self.assertTrue(self.target.alive)
        self.game.draw()

    def test_health_panel_shows_current_and_maximum(self):
        scenario = default_scenario()
        self.game = Game(replace(scenario, units=tuple(
            replace(unit, health=800, max_health=1000) if unit.uid == "A2" else unit
            for unit in scenario.units)))
        with patch.object(self.game.panel, "text", wraps=self.game.panel.text) as draw_text:
            self.game.draw()
        expected = "生命: 800/1000" if self.game.panel.chinese else "HP: 800/1000"
        self.assertTrue(any(call.args[1] == expected for call in draw_text.call_args_list))

    def test_close_event_still_works_during_attack_animation(self):
        self.start_attack(lethal=True)
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.game.run()
        self.assertFalse(pygame.display.get_init())
        self.assertFalse(pygame.font.get_init())


if __name__ == "__main__":
    unittest.main()
