"""M4 file formats and portable paths, runnable before installing Pygame."""

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tactics.asset_manifest import load_manifest
from tactics.content import load_content
from tactics.data_files import DataError, PROJECT_ROOT, rooted_path
from tactics.scenario import default_scenario


class ContentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scenarios").mkdir()
        self.units = json.loads((PROJECT_ROOT / "content/units.json").read_text(encoding="utf-8"))
        self.scene = json.loads((PROJECT_ROOT / "content/scenarios/training_ground.json").read_text(encoding="utf-8"))

    def write(self):
        (self.root / "units.json").write_text(json.dumps(self.units), encoding="utf-8")
        (self.root / "scenarios/training_ground.json").write_text(json.dumps(self.scene), encoding="utf-8")

    def test_default_json_preserves_scenario_and_definition_identity(self):
        content = load_content()
        self.assertEqual(content.scenario, default_scenario())
        self.assertEqual(tuple(unit.definition_id for unit in content.scenario.units),
                         ("vanguard", "scout", "guard", "dummy", "dummy", "dummy"))
        self.assertEqual(content.definitions[1].visual_id, "unit.scout")
        self.assertEqual(content.scenario.units[1].health, 80)
        self.assertEqual(content.scenario.units[-1].speed, 8)

    def test_alternate_scenario_uses_same_definitions_without_rule_changes(self):
        self.scene.update(id="small", cols=5, rows=4, obstacles=[[1, 0]], spawns=[
            {"uid":"blue", "definition_id":"scout", "team":"ally", "cell":[0,0]},
            {"uid":"red", "definition_id":"dummy", "team":"enemy", "cell":[3,0],
             "overrides":{"max_health":50, "attack":17}},
        ])
        self.write()
        content = load_content(self.root)
        self.assertEqual((content.scenario.cols, content.scenario.rows), (5, 4))
        self.assertEqual((content.scenario.units[-1].health, content.scenario.units[-1].max_health), (50, 50))
        from tactics.controller import Controller
        controller = Controller(content.scenario)
        self.assertTrue(controller.move_to((2, 0)))
        self.assertTrue(controller.attack("red"))
        controller.update(0)
        self.assertTrue(controller.undo())
        self.assertEqual(controller.get_view_state().active.definition_id, "scout")

    def test_unknown_definition_and_unknown_fields_are_located(self):
        for change, expected in (({"definition_id":"missing"}, "unknown definition"),
                                 ({"typo":1}, "unknown")):
            with self.subTest(change=change):
                record = dict(self.scene["spawns"][0])
                self.scene["spawns"][0].update(change)
                self.write()
                with self.assertRaisesRegex(DataError, expected):
                    load_content(self.root)
                self.scene["spawns"][0] = record

    def test_duplicate_definition_ids_and_json_keys_are_rejected(self):
        self.units["units"].append(self.units["units"][0])
        self.write()
        with self.assertRaisesRegex(DataError, "duplicate definition"):
            load_content(self.root)
        (self.root / "units.json").write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaisesRegex(DataError, "units.json.*duplicate key"):
            load_content(self.root)

    def test_definition_numbers_and_versions_are_strict(self):
        for key, value in (("speed", True), ("movement", -1), ("attack", 1.5), ("max_health", 0),
                           ("defense", float("nan"))):
            with self.subTest(key=key):
                old = self.units["units"][0][key]
                self.units["units"][0][key] = value
                self.write()
                with self.assertRaises(DataError):load_content(self.root)
                self.units["units"][0][key] = old
        self.units["schema_version"] = True
        self.write()
        with self.assertRaisesRegex(DataError, "schema_version"):
            load_content(self.root)

    def test_invalid_spawn_configuration_is_rejected_by_existing_scenario_validator(self):
        for changes in ({"cell":[8, 0]}, {"cell":[3, 1]}, {"uid":"D1"},
                        {"team":"other"}, {"overrides":{"health":0}}, {"overrides":{"health":101}}):
            old = dict(self.scene["spawns"][0])
            self.scene["spawns"][0].update(changes)
            self.write()
            with self.subTest(changes=changes), self.assertRaises(DataError):
                load_content(self.root)
            self.scene["spawns"][0] = old

    def test_rooted_paths_reject_absolute_windows_and_traversal_inputs(self):
        for value in ("../outside.png", "/outside.png", "C:/outside.png", "C:outside.png",
                      "\\\\server\\file.png", "units\\file.png"):
            with self.subTest(value=value), self.assertRaises(DataError):
                rooted_path(self.root, value, "asset")
        self.assertEqual(rooted_path(self.root, "units/../ok.png", "asset"), (self.root / "ok.png").resolve())

    def test_symlink_escape_is_rejected_when_os_permits_symlinks(self):
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / "escape").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("OS does not permit creating symlinks")
            with self.assertRaisesRegex(DataError, "escapes root"):
                rooted_path(self.root, "escape/file.png", "asset")

    def test_missing_and_malformed_json_have_file_context(self):
        with self.assertRaisesRegex(DataError, "units.json"):
            load_content(self.root)
        (self.root / "units.json").write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(DataError, "units.json"):
            load_content(self.root)

    def test_content_and_manifest_work_from_other_cwd_with_pygame_blocked(self):
        script = """
import importlib.abc,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname == 'pygame' or fullname.startswith('pygame.'):
   raise AssertionError('Pygame import in data loader')
sys.meta_path.insert(0,Block())
from tactics.content import load_content
from tactics.asset_manifest import load_manifest
from tactics.data_files import PROJECT_ROOT
from tactics.controller import Controller
content=load_content()
manifest=load_manifest(PROJECT_ROOT/'assets')
controller=Controller(content.scenario)
assert controller.move_to((4,4)) and controller.attack('D2')
controller.update(0)
assert controller.undo()
assert controller.get_view_state().active.definition_id=='scout'
assert len(manifest.images)==9 and 'pygame' not in sys.modules
"""
        result = subprocess.run([sys.executable, "-S", "-c", script], cwd=self.root,
                                env={**os.environ, "PYTHONPATH":str(PROJECT_ROOT)},
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ManifestChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = json.loads((PROJECT_ROOT / "assets/manifest.json").read_text(encoding="utf-8"))

    def load(self):
        (self.root / "manifest.json").write_text(json.dumps(self.data), encoding="utf-8")
        return load_manifest(self.root)

    def test_dimensions_pivots_paths_and_boolean_fields_are_validated(self):
        for changes in ({"display_size":[0, 64]}, {"display_size":[True, 64]}, {"pivot":[1.1, 0]},
                        {"pivot":[float("nan"), 0]}, {"optional":"yes"}, {"path":"../x.png"},
                        {"path":"tile.jpg"}, {"typo":0}):
            old = dict(self.data["images"]["tile.floor"])
            self.data["images"]["tile.floor"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(DataError):self.load()
            self.data["images"]["tile.floor"] = old

    def test_animation_references_rates_and_loop_policies_are_validated(self):
        for changes in ({"frames":[]}, {"frames":["unknown"]}, {"fps":0}, {"fps":float("inf")},
                        {"loop":True}, {"loop":1}):
            old = dict(self.data["animations"]["scout.attack"])
            self.data["animations"]["scout.attack"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(DataError):self.load()
            self.data["animations"]["scout.attack"] = old

    def test_visual_board_and_duplicate_cross_kind_references_are_rejected(self):
        self.data["visuals"]["unit.scout"]["idle"] = "unknown"
        with self.assertRaises(DataError):self.load()
        self.data["visuals"]["unit.scout"] = {}
        self.data["board"]["floor"] = "unknown"
        with self.assertRaises(DataError):self.load()
        self.data["board"] = {}
        self.data["animations"]["tile.floor"] = self.data["animations"]["scout.attack"]
        with self.assertRaisesRegex(DataError, "also used"):
            self.load()


if __name__ == "__main__":
    unittest.main()
