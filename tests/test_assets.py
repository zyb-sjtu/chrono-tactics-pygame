"""Real PNG cache, fallback, layering and M3 animation handoff checks."""

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from tactics.assets import AssetManager
from tactics.content import load_content
from tactics.data_files import DataError
from tactics.game import Game
from tactics.scenario import Scenario, UnitSpawn, default_scenario


class AssetChecks(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((128, 128))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(pygame.quit)
        self.root = Path(self.temp.name)
        for name, color in (("one", (0, 200, 210)), ("two", (205, 40, 180)), ("floor", (18, 34, 58))):
            image = pygame.Surface((8, 12), pygame.SRCALPHA)
            image.fill(color if name == "floor" else (0, 0, 0, 0))
            if name != "floor":pygame.draw.rect(image, color, (1, 2, 6, 10))
            pygame.image.save(image, str(self.root / (name + ".png")))
        self.data = {
            "schema_version":1,
            "images":{key:{"path":path, "display_size":size, "pivot":[.5, 1] if key != "floor" else [.5,.5],
                           "optional":True}
                      for key, path, size in (("idle0","one.png",[64,96]), ("idle1","two.png",[64,96]),
                                               ("floor","floor.png",[64,64]), ("alias","one.png",[64,96]))},
            "animations":{
                "idle":{"frames":["idle0","idle1"], "fps":2, "loop":True},
                "attack":{"frames":["idle0","idle1"], "fps":4, "loop":False},
                "death":{"frames":["idle1","idle0"], "fps":2, "loop":False}},
            "visuals":{"unit.scout":{"idle":"idle", "attack":"attack", "death":"death"},
                       "unit.vanguard":{}, "unit.guard":{}, "unit.dummy":{}},
            "board":{"floor":"floor"}}
        self.write()

    def write(self):
        (self.root / "manifest.json").write_text(json.dumps(self.data), encoding="utf-8")

    def manager(self):
        self.write()
        return AssetManager(self.root, load_content().definitions)

    def game(self, scenario=None, **kwargs):
        self.write()
        return Game(scenario, asset_root=self.root, **kwargs)

    def test_original_and_scaled_images_are_cached_across_aliases_and_sizes(self):
        with patch("tactics.assets.pygame.image.load", wraps=pygame.image.load) as load, \
             patch("tactics.assets.pygame.transform.smoothscale", wraps=pygame.transform.smoothscale) as scale:
            manager = self.manager()
            first = manager.get_image("idle0")
            self.assertIs(first.surface, manager.get_image("alias").surface)
            count = scale.call_count
            half = manager.get_image("idle0", .5)
            self.assertEqual(half.surface.get_size(), (32, 48))
            self.assertIs(half, manager.get_image("idle0", .5))
            self.assertEqual(scale.call_count, count + 1)
            self.assertEqual(sum(Path(call.args[0]).name == "one.png" for call in load.call_args_list), 1)

    def test_optional_missing_is_negative_cached_reported_once_and_reload_is_explicit(self):
        (self.root / "one.png").unlink()
        with self.assertLogs("tactics.assets", level="WARNING"):
            manager = self.manager()
        issues = manager.issues
        with patch("tactics.assets.pygame.image.load", side_effect=AssertionError("retried missing file")):
            self.assertIsNone(manager.get_image("idle0", .5))
            self.assertIsNone(manager.get_clip("attack"))
        self.assertEqual(manager.issues, issues)
        image = pygame.Surface((8, 12), pygame.SRCALPHA)
        pygame.image.save(image, str(self.root / "one.png"))
        self.assertIsNone(manager.get_image("idle0"))
        manager.clear_cache()
        manager.preload()
        self.assertIsNotNone(manager.get_image("idle0"))

    def test_corrupt_optional_image_falls_back_and_required_image_fails_at_startup(self):
        (self.root / "one.png").write_bytes(b"broken PNG")
        with self.assertLogs("tactics.assets", level="WARNING"):
            self.assertIsNone(self.manager().visual("scout", "idle"))
        self.data["images"]["idle0"]["optional"] = False
        self.write()
        with self.assertRaisesRegex(DataError, "required image unavailable.*idle0"):
            Game(asset_root=self.root)
        self.assertFalse(pygame.display.get_init())

    def test_unused_required_entry_is_validated_even_after_optional_alias_failed(self):
        self.data["images"]["optional"] = dict(self.data["images"]["idle0"], path="missing.png")
        self.data["images"]["required"] = dict(self.data["images"]["optional"], optional=False)
        with self.assertLogs("tactics.assets", level="WARNING"), \
             self.assertRaisesRegex(DataError, "required image unavailable.*required"):
            self.manager()

    def test_unknown_visual_binding_is_a_clear_initialization_error(self):
        content = load_content()
        definitions = (replace(content.definitions[0], visual_id="unknown"),)
        with self.assertRaisesRegex(DataError, "vanguard.*unknown visual"):
            AssetManager(self.root, definitions)

    def test_asset_loading_requires_initialized_display(self):
        pygame.quit()
        with self.assertRaisesRegex(DataError, "initialized display"):
            self.manager()

    def test_frame_selection_loop_and_completion_are_independent_of_global_busy(self):
        manager = self.manager()
        idle = manager.visual("scout", "idle")
        self.assertIs(idle.frame_at(0), idle.frame_at(1))
        self.assertIsNot(idle.frame_at(0), idle.frame_at(.5))
        self.assertFalse(idle.finished(1000))
        attack = manager.visual("scout", "attack")
        self.assertFalse(attack.finished(.49))
        self.assertTrue(attack.finished(.5))
        self.assertIs(attack.frame_at(100), attack.frames[-1])
        self.assertIsNone(manager.visual("unknown", "idle"))

    def test_pivot_transparency_and_requested_sizes_are_preserved(self):
        sprite = self.manager().get_image("idle0")
        surface = pygame.Surface((100, 120))
        surface.fill("white")
        sprite.blit(surface, (50, 110))
        self.assertEqual(tuple(surface.get_at((18, 14)))[:3], (255, 255, 255))
        self.assertEqual(tuple(surface.get_at((50, 80)))[:3], (0, 200, 210))
        self.assertEqual(sprite.surface.get_at((0, 0)).a, 0)
        for value in (True, 0, -1, float("nan")):
            with self.subTest(value=value), self.assertRaises(DataError):
                self.manager().get_clip("attack", value)

    def test_game_default_render_chain_uses_supplied_floor_and_unit_images(self):
        game = self.game()
        game.draw()
        self.assertEqual(tuple(game.screen.get_at((470, 470)))[:3], (18, 34, 58))
        self.assertEqual(tuple(game.screen.get_at((85, 185)))[:3], (0, 200, 210))
        self.assertEqual(game.geometry.cell_at((85, 185)), (1, 2))  # Tall art does not move the unit.
        self.assertEqual(game.controller.get_view_state().active.cell, (1, 3))

    def test_repeated_draws_and_idle_updates_do_not_load_scale_or_change_rule_state(self):
        game = self.game()
        before = game.controller.get_view_state()
        with patch("tactics.assets.pygame.image.load", side_effect=AssertionError("per-frame load")), \
             patch("tactics.assets.pygame.transform.smoothscale", side_effect=AssertionError("per-frame scale")):
            for _ in range(5):
                game.update(.5)
                game.draw()
            self.assertEqual(game.controller.get_view_state(), before)
            game.controller.move_to((4, 4))
            game.controller.attack("D2")
            self.assertEqual(tuple(body.uid for body in game.effects.body_views()), ("A2",))
            game.update(.1)
            game.draw()
            game.update(.81)
            self.assertEqual(game.controller.get_view_state().active.uid, "A1")

    def test_geometry_and_images_produce_identical_move_attack_and_undo_state(self):
        views = []
        for geometric in (True, False):
            game = self.game(geometric=geometric)
            game.controller.move_to((4, 4))
            game.controller.attack("D2")
            game.update(2)
            after = game.controller.get_view_state()
            game.controller.undo()
            views.append((after, game.controller.get_view_state()))
        self.assertEqual(*views)

    def test_sprite_death_waits_hides_and_undo_restores_without_old_callback(self):
        scenario = Scenario("death", 3, 3, (
            UnitSpawn("blue", "Blue", "ally", "test", (0, 1), speed=20, definition_id="vanguard"),
            UnitSpawn("red", "Red", "enemy", "test", (2, 1), health=5, definition_id="scout")))
        game = self.game(scenario)
        game.controller.move_to((1, 1))
        game.controller.attack("red")
        token = game.controller.get_view_state().pending_resolution
        self.assertEqual(tuple(body.uid for body in game.effects.body_views()), ("red",))
        game.update(.91)
        self.assertTrue(game.controller.get_view_state().input_locked)
        game.draw()
        game.update(.1)
        self.assertFalse(game.effects.body_views())
        self.assertEqual(game.controller.get_view_state().winner, "ally")
        self.assertFalse(game.controller.complete_presentation(token))
        game.draw()
        self.assertEqual(tuple(game.screen.get_at(game.geometry.cell_center((2, 1))))[:3], (18, 34, 58))
        game.controller.undo()
        self.assertFalse(game.effects.busy)
        self.assertFalse(game.controller.complete_presentation(token))
        self.assertEqual(len(game.controller.get_view_state().board.units), 2)
        game.draw()

    def test_missing_all_optional_pngs_matches_geometry_pixels_and_attack_fallback(self):
        for path in self.root.glob("*.png"):path.unlink()
        with self.assertLogs("tactics.assets", level="WARNING"):
            game = self.game()
        game.draw()
        image = pygame.image.tostring(game.screen, "RGBA")
        game.controller.move_to((4, 4))
        game.controller.attack("D2")
        self.assertFalse(game.effects.sprites)
        game.update(1)
        self.assertEqual(game.controller.get_view_state().active.uid, "A1")
        geometric = self.game(geometric=True)
        geometric.draw()
        self.assertEqual(image, pygame.image.tostring(geometric.screen, "RGBA"))
        scenario = Scenario("fallback_death", 3, 3, (
            UnitSpawn("blue", "Blue", "ally", "test", (2, 1), health=5, speed=5, definition_id="scout"),
            UnitSpawn("red", "Red", "enemy", "test", (0, 1), speed=20, definition_id="dummy")))
        with self.assertLogs("tactics.assets", level="WARNING"):
            death = self.game(scenario)
        death.controller.move_to((1, 1))
        death.controller.attack("blue")
        self.assertEqual(len(death.effects.deaths), 1)
        self.assertFalse(death.effects.sprites)
        death.update(1)
        self.assertEqual(death.controller.get_view_state().winner, "enemy")
        self.assertTrue(death.controller.undo())

    def test_manifest_only_replacement_changes_art_without_changing_rule_values(self):
        game = self.game()
        game.draw()
        pixel = tuple(game.screen.get_at((85, 185)))
        before = game.controller.get_view_state()
        self.data["visuals"]["unit.scout"]["idle"] = "idle1"
        replacement = self.game()
        replacement.draw()
        self.assertNotEqual(tuple(replacement.screen.get_at((85, 185))), pixel)
        self.assertEqual(replacement.controller.get_view_state(), before)

    def test_all_overlays_remain_above_tall_sprites_and_clip_is_restored(self):
        scenario = Scenario("layers", 3, 3, (
            UnitSpawn("blue", "Blue", "ally", "test", (1, 1), speed=20, definition_id="vanguard"),
            UnitSpawn("red", "Red", "enemy", "test", (1, 2), definition_id="scout")))
        game = self.game(scenario)
        game.draw()
        self.assertEqual(tuple(game.screen.get_at((76, 122)))[:3], (105, 218, 153))
        surface = pygame.Surface((250, 250))
        surface.fill("magenta")
        surface.set_clip((10, 10, 220, 220))
        before = surface.get_clip()
        game.renderer.draw(surface, game.controller.get_view_state().board)
        self.assertEqual(surface.get_clip(), before)
        self.assertEqual(tuple(surface.get_at((200, 200)))[:3], (255, 0, 255))

    def test_geometric_mode_does_not_need_manifest_or_image_directory(self):
        game = Game(asset_root=self.root / "absent", geometric=True)
        self.assertIsNone(game.assets)
        game.draw()


if __name__ == "__main__":
    unittest.main()
