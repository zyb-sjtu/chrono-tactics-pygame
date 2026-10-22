"""Scenario-owned logical grid, spatial queries and blocked-path movement."""

from collections import deque

from .scenario import Scenario


class Board:
    def __init__(self, scenario: Scenario):
        self.scenario_id = scenario.scenario_id
        self.cols = scenario.cols
        self.rows = scenario.rows
        self.units = scenario.create_units()
        self.obstacles = scenario.obstacles

    @property
    def allies(self):
        return tuple(unit for unit in self.units if unit.team == "ally")

    @property
    def enemies(self):
        return tuple(unit for unit in self.units if unit.team == "enemy")

    def unit_at(self, cell):
        return next((unit for unit in self.living_units if unit.cell == cell), None)

    @property
    def living_units(self):
        # Keep the complete roster for undo; defeated units leave play immediately.
        return tuple(unit for unit in self.units if unit.alive)

    def neighbors(self, cell):
        col, row = cell
        return tuple((x, y) for x, y in ((col - 1, row), (col + 1, row),
                                        (col, row - 1), (col, row + 1))
                     if 0 <= x < self.cols and 0 <= y < self.rows)

    def reachable_cells(self, unit):
        """BFS counts real orthogonal steps; all occupied cells block paths."""
        blocked = set(self.obstacles) | {other.cell for other in self.living_units if other is not unit}
        distances = {unit.cell: 0}
        queue = deque([unit.cell])
        while queue:
            cell = queue.popleft()
            if distances[cell] >= unit.movement:
                continue
            for neighbor in self.neighbors(cell):
                if neighbor not in blocked and neighbor not in distances:
                    distances[neighbor] = distances[cell] + 1
                    queue.append(neighbor)
        return set(distances) - {unit.cell}
