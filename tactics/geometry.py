"""Pure numeric conversion between logical grid cells and screen coordinates."""

from dataclasses import dataclass
from typing import Tuple

from .models import Cell


@dataclass(frozen=True)
class BoardGeometry:
    cols: int
    rows: int
    cell_size: int
    origin: Tuple[int, int] = (0, 0)

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in (self.cols, self.rows, self.cell_size)):
            raise ValueError("geometry dimensions and cell_size must be positive integers")
        if (not isinstance(self.origin, (tuple, list)) or len(self.origin) != 2
                or any(type(value) is not int for value in self.origin)):
            raise ValueError("origin must be a pair of integers")
        object.__setattr__(self, "origin", tuple(self.origin))

    @property
    def width(self):
        return self.cols * self.cell_size

    @property
    def height(self):
        return self.rows * self.cell_size

    @property
    def bounds(self):
        return (*self.origin, self.width, self.height)

    def cell_at(self, position):
        x, y = position[0] - self.origin[0], position[1] - self.origin[1]
        if 0 <= x < self.width and 0 <= y < self.height:
            return int(x // self.cell_size), int(y // self.cell_size)
        return None

    def cell_rect(self, cell: Cell):
        if (not isinstance(cell, (tuple, list)) or len(cell) != 2
                or any(type(value) is not int for value in cell)
                or not (0 <= cell[0] < self.cols and 0 <= cell[1] < self.rows)):
            raise ValueError("cell is outside the geometry: {}".format(cell))
        return (self.origin[0] + cell[0] * self.cell_size,
                self.origin[1] + cell[1] * self.cell_size, self.cell_size, self.cell_size)

    def cell_center(self, cell: Cell):
        x, y, width, height = self.cell_rect(cell)
        return x + width // 2, y + height // 2

    def cell_anchor(self, cell: Cell):
        x, y, width, height = self.cell_rect(cell)
        return x + width // 2, y + height

    def cell_scale(self, cell: Cell):
        self.cell_rect(cell)
        return self.cell_size / 64

    def body_rect(self, cell: Cell):
        return self.cell_rect(cell)
