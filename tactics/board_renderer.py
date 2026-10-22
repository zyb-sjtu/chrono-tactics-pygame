"""Draw detached board views, with no battle queries or state mutations."""

import pygame

from .geometry import BoardGeometry
from .view_models import BoardView


class BoardRenderer:
    def __init__(self, geometry: BoardGeometry, assets=None):
        self.geometry = geometry
        self.assets = assets
        self.elapsed = 0
        self.scale = geometry.cell_size / 64
        self.label_font = None

    def _size(self, value):
        return max(1, round(value * self.scale))

    def _rect(self, cell):
        return pygame.Rect(self.geometry.cell_rect(cell))

    def update(self, elapsed):
        self.elapsed += max(0, elapsed)

    def draw(self, surface, view: BoardView, bodies=()):
        if (view.cols, view.rows) != (self.geometry.cols, self.geometry.rows):
            raise ValueError("board view and geometry dimensions do not match")
        if self.label_font is None:
            self.label_font = pygame.font.Font(None, self._size(20))
        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(pygame.Rect(self.geometry.bounds)))
        try:
            self._draw(surface, view, bodies)
        finally:
            surface.set_clip(old_clip)

    def _draw(self, surface, view, bodies):
        floor = self.assets.board_image("floor", self.scale) if self.assets else None
        for row in range(view.rows):
            for col in range(view.cols):
                color = (42, 55, 70) if (row + col) % 2 else (48, 63, 79)
                rect = self._rect((col, row))
                pygame.draw.rect(surface, color, rect)
                if floor is not None:
                    floor.blit(surface, rect.center)
                pygame.draw.rect(surface, (66, 81, 97), rect, self._size(1))

        for cells, color in ((view.move_cells, (54, 109, 103)), (view.attack_cells, (125, 65, 74))):
            for cell in cells:
                pygame.draw.rect(surface, color, self._rect(cell).inflate(-self._size(4), -self._size(4)),
                                 border_radius=self._size(4))
        for cell in view.target_cells:
            pygame.draw.rect(surface, (255, 161, 128),
                             self._rect(cell).inflate(-self._size(5), -self._size(5)), self._size(3))

        overrides = {body.uid: body for body in bodies}
        # Feet determine overlap; all overlays are drawn after every body.
        drawables = [(cell[1], "obstacle:{}:{}".format(*cell), "obstacle", cell) for cell in view.obstacles]
        drawables += [(unit.cell[1], unit.uid, "unit", unit) for unit in view.units
                      if unit.uid not in overrides]
        drawables += [(body.cell[1], body.uid, "sprite", body) for body in bodies]
        for _, _, kind, item in sorted(drawables, key=lambda item: item[:2]):
            if kind == "obstacle":
                self._draw_obstacle(surface, item)
            elif kind == "sprite":
                item.sprite.blit(surface, self._rect(item.cell).midbottom)
            else:
                self._draw_unit(surface, item)

        for unit in view.units:
            rect = self._rect(unit.cell)
            label = self.label_font.render(unit.uid, True, (255, 255, 255))
            surface.blit(label, label.get_rect(center=rect.center))
            self._draw_overlay(surface, view, unit, rect)

    def _draw_obstacle(self, surface, cell):
        sprite = self.assets.board_image("obstacle", self.scale) if self.assets else None
        if sprite is not None:
            sprite.blit(surface, self._rect(cell).midbottom)
            return
        block = self._rect(cell).inflate(-self._size(12), -self._size(12))
        pygame.draw.rect(surface, (111, 124, 135), block, border_radius=self._size(5))
        pygame.draw.line(surface, (146, 157, 166), block.topleft, block.bottomright, self._size(2))
        pygame.draw.line(surface, (146, 157, 166), block.topright, block.bottomleft, self._size(2))

    def _draw_unit(self, surface, unit):
        rect = self._rect(unit.cell)
        clip = self.assets.visual(unit.definition_id, "idle", self.scale) if self.assets else None
        if clip is not None:
            clip.frame_at(self.elapsed).blit(surface, rect.midbottom)
            return
        if unit.team == "ally":
            pygame.draw.circle(surface, (69, 156, 239), rect.center, self._size(21))
            pygame.draw.circle(surface, (146, 207, 255), rect.center, self._size(21), self._size(2))
        else:
            block = rect.inflate(-self._size(24), -self._size(24))
            pygame.draw.rect(surface, (231, 88, 94), block, border_radius=self._size(3))
            pygame.draw.rect(surface, (255, 153, 146), block, self._size(2), border_radius=self._size(3))

    def _draw_overlay(self, surface, view, unit, rect):
        if unit.uid == view.active_uid:
            pygame.draw.rect(surface, (255, 219, 116),
                             rect.inflate(-self._size(4), -self._size(4)), self._size(3))
        if unit.uid == view.selected_uid:
            pygame.draw.circle(surface, (246, 248, 252), rect.center, self._size(27), self._size(2))
        bar = pygame.Rect(rect.x + self._size(10), rect.y + self._size(58), self._size(44), self._size(4))
        pygame.draw.rect(surface, (26, 31, 39), bar)
        fill = bar.copy()
        fill.width = round(bar.width * min(1, unit.health / max(1, unit.max_health)))
        pygame.draw.rect(surface, (105, 218, 153), fill)
