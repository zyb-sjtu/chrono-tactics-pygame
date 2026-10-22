"""Cached planar projection and inverse picking, with no graphics dependency."""

import math
from dataclasses import dataclass, field

EPSILON = 1e-9


def pair(value, label, positive=False):
    if (not isinstance(value, (tuple, list)) or len(value) != 2
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in value)
            or (positive and any(v <= 0 for v in value))):
        raise ValueError(label + " must be a finite pair" + (" of positive numbers" if positive else ""))
    return tuple(value)


@dataclass(frozen=True)
class BackgroundFit:
    image_size: tuple
    viewport_size: tuple

    def __post_init__(self):
        object.__setattr__(self, "image_size", pair(self.image_size, "image size", True))
        object.__setattr__(self, "viewport_size", pair(self.viewport_size, "viewport size", True))

    @property
    def scale(self):
        return min(v / i for v, i in zip(self.viewport_size, self.image_size))

    @property
    def offset(self):
        return tuple((v - i * self.scale) / 2 for v, i in zip(self.viewport_size, self.image_size))

    def to_screen(self, point):
        return tuple(v * self.scale + d for v, d in zip(point, self.offset))

    def to_image(self, point):
        return tuple((v - d) / self.scale for v, d in zip(point, self.offset))


def inverse(matrix):
    a, b, c, d, e, f, g, h, i = matrix
    adj = (e*i-f*h, c*h-b*i, b*f-c*e, f*g-d*i, a*i-c*g, c*d-a*f,
           d*h-e*g, b*g-a*h, a*e-b*d)
    determinant = a*adj[0] + b*adj[3] + c*adj[6]
    if abs(determinant) < EPSILON:
        raise ValueError("board corners produce a singular homography")
    return tuple(v / determinant for v in adj)


def transform(matrix, point):
    x, y = point
    denominator = matrix[6]*x + matrix[7]*y + matrix[8]
    if not math.isfinite(denominator) or abs(denominator) < EPSILON:
        raise ValueError("point is on the projection horizon")
    result = ((matrix[0]*x + matrix[1]*y + matrix[2])/denominator,
              (matrix[3]*x + matrix[4]*y + matrix[5])/denominator)
    if not all(math.isfinite(v) for v in result):
        raise ValueError("non-finite projection")
    return result


@dataclass(frozen=True)
class PerspectiveBoardGeometry:
    cols: int
    rows: int
    corners: tuple
    reference_size: tuple
    viewport_size: tuple = (1280, 720)
    _matrix: tuple = field(init=False, repr=False)
    _inverse: tuple = field(init=False, repr=False)
    _polygons: tuple = field(init=False, repr=False)
    _centers: tuple = field(init=False, repr=False)
    _anchors: tuple = field(init=False, repr=False)
    _scales: tuple = field(init=False, repr=False)
    fit: BackgroundFit = field(init=False)

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in (self.cols, self.rows)):
            raise ValueError("board dimensions must be positive integers")
        fit = BackgroundFit(self.reference_size, self.viewport_size)
        object.__setattr__(self, "reference_size", fit.image_size)
        object.__setattr__(self, "viewport_size", fit.viewport_size)
        object.__setattr__(self, "fit", fit)
        if not isinstance(self.corners, (tuple, list)) or len(self.corners) != 4:
            raise ValueError("board requires p00, p10, p11, p01 corners")
        corners = tuple(pair(p, "board corner") for p in self.corners)
        w, height = self.reference_size
        if any(not (0 <= x <= w and 0 <= y <= height) for x, y in corners):
            raise ValueError("board corners must be inside the reference image")
        points = tuple((x/w, y/height) for x, y in corners)
        for index in range(4):
            a, b, c = (points[(index+k) % 4] for k in range(3))
            if (b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0]) <= EPSILON:
                raise ValueError("board corners must form a strictly convex clockwise screen polygon")
        object.__setattr__(self, "corners", corners)
        (x0,y0), (x1,y1), (x2,y2), (x3,y3) = points
        dx1, dx2, dx3 = x1-x2, x3-x2, x0-x1+x2-x3
        dy1, dy2, dy3 = y1-y2, y3-y2, y0-y1+y2-y3
        if abs(dx3) + abs(dy3) < EPSILON:
            g = h = 0.0
        else:
            denominator = dx1*dy2-dx2*dy1
            if abs(denominator) < EPSILON:
                raise ValueError("board corners produce a degenerate projection")
            g = (dx3*dy2-dx2*dy3)/denominator
            h = (dx1*dy3-dx3*dy1)/denominator
        matrix = (x1-x0+g*x1, x3-x0+h*x3, x0,
                  y1-y0+g*y1, y3-y0+h*y3, y0, g, h, 1.0)
        object.__setattr__(self, "_matrix", matrix)
        object.__setattr__(self, "_inverse", inverse(matrix))
        polygons, centers, anchors, scales = [], [], [], []
        for row in range(self.rows):
            for col in range(self.cols):
                polygon = tuple(self.project(p) for p in ((col,row),(col+1,row),(col+1,row+1),(col,row+1)))
                polygons.append(polygon)
                centers.append(self.project((col+.5, row+.5)))
                anchors.append(self.project((col+.5, row+.82)))
                # Quantize to a small, bounded set of preloaded sprite scales.
                edge = math.dist(polygon[0], polygon[1]) + math.dist(polygon[1], polygon[2])
                scales.append(round(max(.5, min(1.5, edge / 2 / 64)) * 8) / 8)
        for name, value in (("_polygons",polygons),("_centers",centers),("_anchors",anchors),("_scales",scales)):
            object.__setattr__(self, name, tuple(value))

    @property
    def bounds(self):
        return (0, 0, *self.viewport_size)

    def _index(self, cell):
        if (not isinstance(cell, (tuple, list)) or len(cell) != 2
                or any(type(v) is not int for v in cell)
                or not (0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows)):
            raise ValueError("cell outside perspective board: {}".format(cell))
        return cell[1]*self.cols + cell[0]

    def project(self, logical_point):
        point = pair(logical_point, "logical point")
        x, y = transform(self._matrix, (point[0]/self.cols, point[1]/self.rows))
        return self.fit.to_screen((x*self.reference_size[0], y*self.reference_size[1]))

    def cell_at(self, position):
        try:
            x, y = self.fit.to_image(pair(position, "screen point"))
            if not (0 <= x < self.reference_size[0] and 0 <= y < self.reference_size[1]):
                return None
            u, v = transform(self._inverse, (x/self.reference_size[0], y/self.reference_size[1]))
            u, v = u*self.cols, v*self.rows
            # Snap roundoff on exact shared edges; ownership remains [left, right).
            u = round(u) if abs(u-round(u)) < EPSILON else u
            v = round(v) if abs(v-round(v)) < EPSILON else v
            if 0 <= u < self.cols and 0 <= v < self.rows:
                return math.floor(u), math.floor(v)
        except (ValueError, TypeError, OverflowError):
            pass
        return None

    def cell_polygon(self, cell):
        return self._polygons[self._index(cell)]

    def cell_center(self, cell):
        return self._centers[self._index(cell)]

    def cell_anchor(self, cell):
        return self._anchors[self._index(cell)]

    def cell_scale(self, cell):
        return self._scales[self._index(cell)]

    def depth_at(self, cell):
        return self.cell_anchor(cell)[1]

    def body_rect(self, cell):
        # Geometric placeholders remain centered on their actual pickable cell.
        # PNG bodies use cell_anchor separately, so their bottom pivot stays intact.
        x, y = self.cell_center(cell)
        size = round(64*self.cell_scale(cell))
        return round(x-size/2), round(y-size/2), size, size

    @property
    def scales(self):
        return tuple(sorted(set(self._scales)))
