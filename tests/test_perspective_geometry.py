"""Pure homography acceptance, including ownership of shared boundaries."""

from dataclasses import replace
import math
import unittest

from tactics.perspective_geometry import BackgroundFit, PerspectiveBoardGeometry, transform


class PerspectiveGeometryChecks(unittest.TestCase):
    def setUp(self):
        self.geometry = PerspectiveBoardGeometry(8, 8, ((600,100),(950,350),(550,650),(150,400)), (1100,700))

    def test_four_logical_outer_corners(self):
        for point, corner in zip(((0,0),(8,0),(8,8),(0,8)), self.geometry.corners):
            actual = self.geometry.project(point)
            expected = self.geometry.fit.to_screen(corner)
            for a, b in zip(actual, expected):
                self.assertAlmostEqual(a, b)

    def test_all_centers_and_interior_points_pick_their_own_cell(self):
        for row in range(8):
            for col in range(8):
                cell = (col,row)
                self.assertEqual(self.geometry.cell_at(self.geometry.cell_center(cell)), cell)
                for dx,dy in ((.05,.05),(.95,.95),(.1,.9),(.9,.1)):
                    self.assertEqual(self.geometry.cell_at(self.geometry.project((col+dx,row+dy))), cell)
                self.assertEqual(self.geometry.cell_at(self.geometry.cell_anchor(cell)), cell)
                x,y,w,h = self.geometry.body_rect(cell)
                self.assertEqual(self.geometry.cell_at((x+w/2,y+h/2)),cell)
                self.assertEqual(self.geometry.depth_at(cell), self.geometry.cell_anchor(cell)[1])

    def test_polygons_share_exact_edges_and_consistent_winding(self):
        for row in range(8):
            for col in range(8):
                a,b,c,d = self.geometry.cell_polygon((col,row))
                self.assertGreater((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]),0)
                if col < 7:
                    adjacent = self.geometry.cell_polygon((col+1,row))
                    self.assertEqual((b,c),(adjacent[0],adjacent[3]))
                if row < 7:
                    adjacent = self.geometry.cell_polygon((col,row+1))
                    self.assertEqual((d,c),(adjacent[0],adjacent[1]))

    def test_half_open_shared_edges_and_outer_boundaries(self):
        for index in range(1,8):
            self.assertEqual(self.geometry.cell_at(self.geometry.project((index,2.5))), (index,2))
            self.assertEqual(self.geometry.cell_at(self.geometry.project((2.5,index))), (2,index))
        self.assertEqual(self.geometry.cell_at(self.geometry.project((0,0))), (0,0))
        for point in ((8,2),(2,8),(-.001,2),(2,-.001),(8,8)):
            self.assertIsNone(self.geometry.cell_at(self.geometry.project(point)))

    def test_contain_letterbox_and_nonfinite_input(self):
        geometry = replace(self.geometry, viewport_size=(1600,700))
        self.assertIsNone(geometry.cell_at((10,350)))
        for cell in ((0,0),(3,6),(7,7)):
            self.assertEqual(geometry.cell_at(geometry.cell_center(cell)),cell)
        for position in ((math.nan,0),(0,math.inf),None,(0,),('x',1)):
            self.assertIsNone(geometry.cell_at(position))
        with self.assertRaisesRegex(ValueError,'horizon'):
            transform((1,0,0,0,1,0,1,0,-1),(1,0))

    def test_degenerate_crossed_reversed_and_invalid_configurations(self):
        for corners in (((0,0),)*4, ((0,0),(100,0),(200,0),(0,100)),
                        ((0,0),(100,100),(100,0),(0,100)), tuple(reversed(self.geometry.corners)),
                        ((math.nan,0),(100,0),(100,100),(0,100))):
            with self.subTest(corners=corners), self.assertRaises(ValueError):
                replace(self.geometry,corners=corners)
        for cell in ((8,0),(-1,0),(True,0),(1.0,2)):
            with self.assertRaises(ValueError):
                self.geometry.cell_polygon(cell)
        with self.assertRaises(ValueError):
            BackgroundFit((0,10),(100,100))

    def test_affine_rectangle_and_axis_orientation(self):
        geometry = PerspectiveBoardGeometry(8,8,((0,0),(800,0),(800,800),(0,800)),(800,800),(800,800))
        self.assertEqual(geometry.cell_center((2,5)),(250.0,550.0))
        self.assertEqual(geometry.cell_at((350,250)),(3,2))
