"""M5 extension acceptance using shipped content and public application operations."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pygame

from tactics.content import load_content
from tactics.game import Game

ROOT = Path(__file__).resolve().parents[1]
MODES = ("geometry", "classic", "dusk")


def make_game(scene, mode):
    return Game(scenario_file="scenarios/{}.json".format(scene),
                geometric=mode == "geometry",
                asset_root=ROOT / "assets/skins/dusk" if mode == "dusk" else None)


def exercise(check, game, scene, capture=None):
    """Same inputs and observations for every skin; also used for window captures."""
    trace = []

    def observe(name):
        game.draw()
        trace.append(game.controller.get_view_state())
        if capture:
            capture(name, game)
        return trace[-1]

    def click(cell):
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                           pos=game.geometry.cell_center(cell)))

    def key(value):
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))

    def unit(uid):
        return next(u for u in game.controller.get_view_state().units if u.uid == uid)

    initial = observe("initial")
    check.assertEqual(initial.active.uid, "A2")
    check.assertEqual((initial.active.health, initial.active.max_health), (80, 100))
    river = scene == "river_crossing"
    target = "R1" if river else "D2"
    click((3, 2) if river else (4, 4))
    observe("moved")
    click(unit(target).cell)
    resolving = observe("attack")
    token = resolving.pending_resolution
    check.assertTrue(resolving.input_locked)
    check.assertEqual(unit(target).health, 0 if river else 90)
    check.assertEqual(game.effects.damage_texts[0].amount, 10)
    if river:
        check.assertNotIn(target, [u.uid for u in resolving.board.units])
        check.assertTrue(game.effects.deaths or game.effects.body_views())
    for value in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_BACKSPACE):
        key(value)
    click(initial.active.cell)
    check.assertEqual(game.controller.get_view_state(), resolving)
    game.update(0.2)
    observe("death" if river else "damage")
    game.update(2.0)
    after = observe("handoff")
    check.assertEqual(after.active.uid, "A1")
    check.assertFalse(game.effects.busy)
    check.assertFalse(game.effects.body_views())
    check.assertFalse(game.controller.complete_presentation(token))
    check.assertEqual(game.controller.get_view_state(), after)

    if river:
        key(pygame.K_RETURN)
        check.assertEqual(observe("enemy").active.uid, "R2")
        key(pygame.K_RETURN)
        round_two = observe("round_two")
        check.assertEqual((round_two.round_number, round_two.active.uid), (2, "A2"))
        click((5, 3))
        check.assertEqual(game.controller.get_view_state().active.cell, (5, 3))
        click(unit("R2").cell)
        second_token = observe("final_attack").pending_resolution
        game.update(2.0)
        finished = observe("finished")
        check.assertEqual((finished.phase, finished.winner), ("finished", "ally"))
        for name in ("undo_win", "undo_round", "undo_enemy", "revived"):
            key(pygame.K_BACKSPACE)
            observe(name)
        check.assertEqual(unit("R1").health, 5)
        check.assertEqual(unit("R2").health, 10)
        check.assertEqual(game.controller.get_view_state().round_number, 1)
        check.assertFalse(game.controller.complete_presentation(second_token))
    else:
        key(pygame.K_RETURN)
        check.assertEqual(observe("enemy").active.uid, "D1")
        key(pygame.K_BACKSPACE)
        observe("undo_enemy")
        key(pygame.K_BACKSPACE)
        observe("revived")
        check.assertEqual(unit(target).health, 100)

    restored = game.controller.get_view_state()
    check.assertEqual(restored.active, initial.active)
    check.assertEqual(restored.units, initial.units)
    check.assertEqual(restored.board, initial.board)
    check.assertFalse(game.effects.busy)
    check.assertFalse(game.controller.complete_presentation(token))
    check.assertEqual(game.controller.get_view_state(), restored)
    return tuple(trace)


class ExtensionAcceptance(unittest.TestCase):
    def tearDown(self):
        pygame.quit()

    def test_second_scene_reuses_definitions_with_different_layout(self):
        original = load_content()
        river = load_content(scenario_file="scenarios/river_crossing.json")
        self.assertEqual(original.definitions, river.definitions)
        self.assertEqual((river.scenario.cols, river.scenario.rows), (6, 5))
        self.assertNotEqual(original.scenario.obstacles, river.scenario.obstacles)
        self.assertEqual(len(river.scenario.units), 4)

    def test_both_shipped_skins_load_without_fallback_issues(self):
        frames = []
        for mode in ("classic", "dusk"):
            game = make_game("river_crossing", mode)
            self.assertFalse(game.assets.issues)
            game.draw()
            frames.append(pygame.image.tostring(game.screen, "RGB"))
            pygame.quit()
        self.assertNotEqual(*frames)

    def compare_modes(self, scene):
        traces = []
        for mode in MODES:
            with self.subTest(mode=mode):
                game = make_game(scene, mode)
                traces.append(exercise(self, game, scene))
                pygame.quit()
        self.assertEqual(traces[0], traces[1])
        self.assertEqual(traces[0], traces[2])

    def test_default_scene_identical_rules_in_three_modes(self):
        self.compare_modes("training_ground")

    def test_river_kills_rounds_and_rewinds_identical_in_three_modes(self):
        self.compare_modes("river_crossing")

    def test_font_registry_fallback_and_quit_while_resolving(self):
        for mode in MODES:
            with self.subTest(mode=mode), \
                 patch("tactics.panel.Path.is_file", return_value=False), \
                 patch("tactics.panel.pygame.font.match_font", side_effect=TypeError("bad registry")):
                game = make_game("river_crossing", mode)
                self.assertFalse(game.panel.chinese)
                self.assertTrue(game.controller.move_to((3, 2)))
                self.assertTrue(game.controller.attack("R1"))
                game.draw()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                game.run()
                self.assertFalse(game.running)
                self.assertFalse(pygame.display.get_init())
                self.assertFalse(pygame.font.get_init())

    def test_real_cli_from_foreign_directory_with_dusk(self):
        # Execute the actual argparse/main entry, then inject a close event into its loop.
        script = """
import runpy, sys
from pathlib import Path
import pygame
from tactics.game import Game
original_run = Game.run
def run(self):
    assert self.screen.get_size() == (768, 512)
    assert self.controller.get_view_state().active.uid == 'A2'
    assert not self.assets.issues
    self.draw()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    original_run(self)
    assert not pygame.display.get_init()
    print('CLI_WINDOW_QUIT_OK')
Game.run = run
root = Path(sys.argv[1])
sys.argv = [str(root / 'main.py'), '--scenario', 'scenarios/river_crossing.json',
            '--assets', str(root / 'assets/skins/dusk')]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
        env = dict(os.environ, PYTHONPATH=str(ROOT), PYGAME_HIDE_SUPPORT_PROMPT="1")
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, "-c", script, str(ROOT)], cwd=folder,
                                    env=env, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CLI_WINDOW_QUIT_OK", result.stdout)
