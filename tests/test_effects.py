"""Actual window rendering, animation lifecycle, input lock and rewind controls."""

import unittest
from unittest.mock import patch

import pygame

from tactics.battle import Battle
from tactics.game import Game


class CombatInteractionChecks(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.actor = self.game.battle.active_unit
        self.target = self.game.board.enemies[1]

    def tearDown(self):
        pygame.quit()

    def click(self, position):
        self.game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    def start_attack(self, lethal=False):
        if lethal:
            self.target.health = 5
            self.game.battle = Battle(self.game.board)
            self.game.selected = self.game.battle.active_unit
        self.click(self.game.board.rect((4, 4)).center)
        self.click(self.game.board.rect(self.target.cell).center)

    def test_damage_popup_and_controls_are_locked_until_effect_finishes(self):
        self.start_attack()
        self.assertEqual(self.game.effects.damage_texts[0].amount, self.actor.attack)
        self.game.update(0.2)
        self.assertAlmostEqual(self.game.effects.damage_texts[0].age, 0.2)
        self.game.draw()
        for key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
            self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        for rect in (self.game.panel.skip_button, self.game.panel.end_button, self.game.panel.undo_button):
            self.click(rect.center)
        self.click(self.game.board.rect(self.target.cell).center)
        self.assertEqual(self.target.health, self.target.max_health - self.actor.attack)
        self.assertIs(self.game.battle.active_unit, self.actor)
        self.assertEqual(self.game.battle.phase, "resolving")
        self.game.update(1.0)
        self.assertFalse(self.game.effects.busy)
        self.assertEqual(self.game.battle.phase, "move")
        self.assertEqual(self.game.battle.active_unit.uid, "A1")

    def test_defeated_body_animates_then_disappears_from_actual_surface(self):
        self.start_attack(lethal=True)
        self.assertEqual(len(self.game.effects.deaths), 1)
        self.assertFalse(self.target.alive)
        self.game.draw()
        center = self.game.board.rect(self.target.cell).center
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
        self.click(self.game.panel.undo_button.center)
        self.assertEqual(self.target.health, 5)
        self.assertIs(self.game.board.unit_at(self.target.cell), self.target)
        self.assertIs(self.game.battle.active_unit, self.actor)
        self.assertIs(self.game.selected, self.actor)
        self.assertEqual(self.actor.cell, (1, 3))
        self.assertFalse(self.game.effects.busy)
        self.game.draw()

    def test_backspace_rewinds_previous_turn_and_discards_partial_current_move(self):
        self.start_attack()
        self.game.update(1.0)
        self.click(self.game.board.rect((0, 1)).center)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertEqual(self.game.battle.active_unit.uid, "A2")
        self.assertEqual(self.target.health, self.target.max_health)
        self.assertEqual(self.game.board.allies[0].cell, (1, 1))
        self.assertEqual(self.game.battle.phase, "move")

    def test_finished_battle_is_renderable_and_can_be_undone(self):
        self.game.board.units = (self.actor, self.target)
        self.start_attack(lethal=True)
        self.game.update(1.0)
        self.assertTrue(self.game.battle.finished)
        self.game.draw()
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertTrue(self.game.battle.finished)
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        self.assertFalse(self.game.battle.finished)
        self.assertTrue(self.target.alive)
        self.game.draw()

    def test_health_panel_shows_current_and_maximum(self):
        self.actor.health = 800
        self.actor.max_health = 1000
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
