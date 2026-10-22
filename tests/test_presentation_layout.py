"""Pure, strict presentation and background manifest checks."""

import json
from pathlib import Path
import tempfile
import unittest

from tactics.asset_manifest import load_manifest
from tactics.data_files import DataError
from tactics.presentation_layout import load_presentation

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "presentations/war_torn_8x8.json"


class PresentationLayoutChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'presentations').mkdir()
        self.data = json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))

    def load(self):
        (self.root/CONFIG).write_text(json.dumps(self.data),encoding='utf-8')
        return load_presentation(CONFIG,self.root)

    def test_shipped_layout_and_compatible_manifests(self):
        layout = load_presentation(CONFIG)
        self.assertEqual(layout.geometry.reference_size,(1672,941))
        for folder in ('assets','assets/skins/dusk','assets/skins/war_torn'):
            self.assertTrue(load_manifest(ROOT/folder).visuals)
        self.assertEqual(layout.geometry.cell_at(layout.geometry.cell_center((7,7))),(7,7))

    def test_unknown_fields_versions_modes_and_placeholder_corners(self):
        for key,value in (('schema_version',2),('mode','unknown'),('unexpected',1)):
            with self.subTest(key=key):
                original = dict(self.data)
                self.data[key]=value
                with self.assertRaises(DataError): self.load()
                self.data=original
        self.data['board']['corners']={k:[0,0] for k in ('p00','p10','p11','p01')}
        with self.assertRaisesRegex(DataError,'corners'): self.load()

    def test_paths_must_stay_in_project_or_content_root(self):
        for key in ('scenario_file','asset_root'):
            for value in ('../../escape','C:/absolute','/absolute','..\\escape'):
                with self.subTest(key=key,value=value):
                    original=self.data[key]
                    self.data[key]=value
                    with self.assertRaises(DataError): self.load()
                    self.data[key]=original
        with self.assertRaises(DataError): load_presentation('../escape',self.root)

    def test_invalid_viewport_hud_and_debug_are_rejected(self):
        for section,key,value in (('viewport','background_fit','stretch'),('viewport','reference_size',[0,720]),
                                  ('hud','safe_margin',999),('hud','layout','sidebar'),
                                  ('debug','show_grid',1),('board','cols',True)):
            with self.subTest(section=section,key=key):
                original=self.data[section][key]
                self.data[section][key]=value
                with self.assertRaises(DataError): self.load()
                self.data[section][key]=original

    def test_background_reference_and_required_flag_are_validated(self):
        data=json.loads((ROOT/'assets/skins/war_torn/manifest.json').read_text(encoding='utf-8'))
        for bad in ('unknown','optional'):
            if bad=='unknown': data['board']['background']='missing'
            else:
                data['board']['background']='battlefield'
                data['images']['battlefield']['optional']=True
            (self.root/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
            with self.assertRaisesRegex(DataError,'background|unknown image'): load_manifest(self.root)
