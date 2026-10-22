"""Observation integrity and independent error metrics; no Pygame required."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.calibrate_board import DEFAULT, inspect_extent, load_observations, measure
from tactics.data_files import DataError
from tactics.perspective_geometry import PerspectiveBoardGeometry
from scripts.fit_board import load_map, measure_map, check_presentation


class CalibrationChecks(unittest.TestCase):
    def setUp(self):
        self.data,self.geometry = load_observations(DEFAULT)

    def test_measured_strip_is_not_claimed_as_eight_by_eight(self):
        report = measure(self.data,self.geometry)
        self.assertEqual(report['measured_physical_span'],[2,6])
        self.assertEqual(report['interior']['count'],5)
        self.assertAlmostEqual(report['interior']['mean_px'],5.555742450788599)
        self.assertAlmostEqual(report['interior']['max_px'],11.713753031428595)
        self.assertTrue(report['local_threshold_met'])
        self.assertFalse(report['requested_8x8_verified'])

    def test_metric_uses_holdout_points_excludes_fitted_corners(self):
        geometry = PerspectiveBoardGeometry(4,4,((0,0),(400,0),(400,400),(0,400)),(400,400),(400,400))
        data = {'sha256':'test','physical_span':[4,4], 'samples':[
            {'node':[1,1],'image':[102,100],'band':'far'},
            {'node':[2,2],'image':[210,200],'band':'near'}]}
        report = measure(data,geometry)
        self.assertEqual(report['interior'],{'count':2,'mean_px':6.0,'max_px':10.0})
        data['samples'][1]['image']=[214,200]
        self.assertFalse(measure(data,geometry)['local_threshold_met'])

    def test_scaled_viewport_metrics_scale_with_background(self):
        from dataclasses import replace
        original = measure(self.data,self.geometry)
        small = measure(self.data,replace(self.geometry,viewport_size=(640,360)))
        self.assertAlmostEqual(small['interior']['mean_px'],original['interior']['mean_px']/2)
        self.assertAlmostEqual(small['interior']['max_px'],original['interior']['max_px']/2)

    def test_invalid_source_digest_duplicate_sample_and_placeholder_rejected(self):
        variations = []
        changed=deepcopy(self.data); changed['sha256']='0'*64; variations.append(changed)
        changed=deepcopy(self.data); changed['samples'].append(changed['samples'][0]); variations.append(changed)
        changed=deepcopy(self.data); changed['corners']={k:[0,0] for k in changed['corners']}; variations.append(changed)
        changed=deepcopy(self.data); changed['samples'][0]['node']=[0,1]; variations.append(changed)
        changed=deepcopy(self.data); changed['physical_span']=[True,6]; variations.append(changed)
        changed=deepcopy(self.data); changed['image']='../../escape.png'; variations.append(changed)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'observations.json'
            for data in variations:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data),encoding='utf-8')
                    with self.assertRaises(DataError): load_observations(path)

    def test_extent_candidates_are_explicitly_extrapolation_not_observations(self):
        data=deepcopy(self.data)
        result=inspect_extent(self.geometry)
        self.assertIn('EXTRAPOLATION ONLY',result['warning'])
        self.assertTrue(result['candidates_inside_png'])
        self.assertEqual(result['candidates_above_loose_paving_bound'],0)
        self.assertEqual(self.data,data)

    def test_source_points_are_native_coordinates_and_interior_picks_roundtrip(self):
        self.assertEqual(self.geometry.reference_size,(1672,941))
        for sample in self.data['samples']:
            self.assertEqual(self.geometry.cell_at(self.geometry.cell_center((0,sample['node'][1]-1))),
                             (0,sample['node'][1]-1))
            native=self.geometry.fit.to_image(self.geometry.fit.to_screen(sample['image']))
            for a,b in zip(native,sample['image']): self.assertAlmostEqual(a,b)

    def test_irregular_map_holdouts_meet_target_and_runtime_matches_fit(self):
        data,geometry=load_map()
        report=measure_map(data,geometry)
        self.assertTrue(report['threshold_met'])
        self.assertFalse(report['full_rectangular_8x8'])
        self.assertEqual(report['playable_cells'],28)
        self.assertEqual(report['independent_validation']['count'],20)
        self.assertAlmostEqual(report['independent_validation']['mean_px'],5.567315763585733)
        self.assertAlmostEqual(report['independent_validation']['max_px'],11.41999211967498)
        self.assertEqual(report['independent_interior']['count'],9)
        self.assertGreater(report['four_observed_corners_baseline']['max_px'],12)
        # These four reference corners are held out, not falsely reported as zero-error fits.
        for node in ((1,3),(7,3),(7,7),(1,7)):
            self.assertEqual(next(p['role'] for p in data['observations'] if tuple(p['node'])==node),'validation')
        check_presentation(data,geometry)

    def test_map_validation_points_cannot_influence_homography(self):
        from scripts.fit_board import fit_corners
        data,geometry=load_map()
        changed=deepcopy(data)
        for item in changed['observations']:
            if item['role']=='validation': item['image'][0]+=30
        self.assertEqual(fit_corners(changed),fit_corners(data))
        self.assertFalse(measure_map(changed,geometry)['threshold_met'])

    def test_map_missing_duplicate_and_unusable_observations_rejected(self):
        data,_=load_map()
        variations=[]
        changed=deepcopy(data); changed['observations'].pop(); variations.append(changed)
        changed=deepcopy(data); changed['observations'].append(changed['observations'][0]); variations.append(changed)
        changed=deepcopy(data); changed['sha256']='0'*64; variations.append(changed)
        changed=deepcopy(data)
        for item in changed['observations']: item['role']='calibration'
        variations.append(changed)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'map.json'
            for changed in variations:
                path.write_text(json.dumps(changed),encoding='utf-8')
                with self.subTest(changed=changed),self.assertRaises(DataError): load_map(path)
