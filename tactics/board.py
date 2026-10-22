"""Board geometry, blocked-path movement range, and rendering."""

from collections import deque

import pygame

from .models import OBSTACLES, create_allies, create_enemies
from .settings import BOARD_HEIGHT, BOARD_WIDTH, CELL_SIZE, COLS, ROWS


class Board:
    def __init__(self):
        self.allies = create_allies()
        self.enemies = create_enemies()
        self.units = self.allies + self.enemies
        self.obstacles = OBSTACLES
        self.label_font = None

    @staticmethod
    def cell_at(position):
        x, y = position
        if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT:
            return x // CELL_SIZE, y // CELL_SIZE
        return None

    def unit_at(self, cell):
        return next((unit for unit in self.living_units if unit.cell == cell), None)

    @property
    def living_units(self):
        # Keep the complete roster for undo; defeated units leave play immediately.
        return tuple(unit for unit in self.units if unit.alive)

    @staticmethod
    def neighbors(cell):
        col, row = cell
        return tuple((x, y) for x, y in ((col - 1, row), (col + 1, row),
                                        (col, row - 1), (col, row + 1))
                     if 0 <= x < COLS and 0 <= y < ROWS)

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

    @staticmethod
    def rect(cell):
        col, row = cell
        return pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def draw(self, surface, selected, battle):
        if self.label_font is None:
            self.label_font = pygame.font.Font(None, 20)
        for row in range(ROWS):
            for col in range(COLS):
                color = (42, 55, 70) if (row + col) % 2 else (48, 63, 79)
                rect = self.rect((col, row))
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (66, 81, 97), rect, 1)

        active = battle.active_unit
        if active is not None and selected is active and battle.phase in ("move", "attack"):
            cells = battle.movement_range() if battle.phase == "move" else self.neighbors(active.cell)
            color = (54, 109, 103) if battle.phase == "move" else (125, 65, 74)
            for cell in cells:
                if cell not in self.obstacles:
                    pygame.draw.rect(surface, color, self.rect(cell).inflate(-4, -4), border_radius=4)
            for target in battle.attack_targets():
                pygame.draw.rect(surface, (255, 161, 128), self.rect(target.cell).inflate(-5, -5), 3)

        for cell in self.obstacles:
            block = self.rect(cell).inflate(-12, -12)
            pygame.draw.rect(surface, (111, 124, 135), block, border_radius=5)
            pygame.draw.line(surface, (146, 157, 166), block.topleft, block.bottomright, 2)
            pygame.draw.line(surface, (146, 157, 166), block.topright, block.bottomleft, 2)

        for unit in self.living_units:
            rect = self.rect(unit.cell)
            if unit.team == "ally":
                pygame.draw.circle(surface, (69, 156, 239), rect.center, 21)
                pygame.draw.circle(surface, (146, 207, 255), rect.center, 21, 2)
            else:
                block = rect.inflate(-24, -24)
                pygame.draw.rect(surface, (231, 88, 94), block, border_radius=3)
                pygame.draw.rect(surface, (255, 153, 146), block, 2, border_radius=3)
            label = self.label_font.render(unit.uid, True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=rect.center))
            if unit is active:
                pygame.draw.rect(surface, (255, 219, 116), rect.inflate(-4, -4), 3)
            if unit is selected:
                pygame.draw.circle(surface, (246, 248, 252), rect.center, 27, 2)
            bar = pygame.Rect(rect.x + 10, rect.y + 58, 44, 4)
            pygame.draw.rect(surface, (26, 31, 39), bar)
            fill = bar.copy()
            fill.width = round(bar.width * min(1, unit.health / max(1, unit.max_health)))
            pygame.draw.rect(surface, (105, 218, 153), fill)
