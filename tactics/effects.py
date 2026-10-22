"""Non-blocking damage popups and geometric defeat animations."""

import math
from dataclasses import dataclass

import pygame

from .geometry import BoardGeometry
from .view_models import AttackPresentation

DAMAGE_DURATION = 0.9
DEATH_DURATION = 0.65


@dataclass
class DamageText:
    cell: tuple
    amount: int
    age: float = 0.0


@dataclass
class DeathEffect:
    cell: tuple
    team: str
    uid: str
    age: float = 0.0


class CombatEffects:
    def __init__(self, geometry: BoardGeometry):
        self.geometry = geometry
        self.damage_texts = []
        self.deaths = []
        self._pending_token = None
        self.damage_font = pygame.font.Font(None, 32)
        self.label_font = pygame.font.Font(None, 20)

    @property
    def busy(self):
        return bool(self.damage_texts or self.deaths)

    def play_attack(self, event: AttackPresentation):
        self.clear()
        self._pending_token = event.token
        result = event.result
        self.damage_texts.append(DamageText(result.target_cell, result.damage))
        if result.killed:
            self.deaths.append(DeathEffect(result.target_cell, result.target_team, result.target_uid))

    def clear(self):
        self.damage_texts.clear()
        self.deaths.clear()
        self._pending_token = None

    def update(self, elapsed):
        for effect in self.damage_texts + self.deaths:
            effect.age += max(0, elapsed)
        self.damage_texts = [effect for effect in self.damage_texts if effect.age < DAMAGE_DURATION]
        self.deaths = [effect for effect in self.deaths if effect.age < DEATH_DURATION]
        if self._pending_token is not None and not self.busy:
            token, self._pending_token = self._pending_token, None
            return (token,)
        return ()

    def draw(self, surface):
        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(pygame.Rect(self.geometry.bounds)))
        cell_size = self.geometry.cell_size
        scale = cell_size / 64
        for effect in self.deaths:
            progress = effect.age / DEATH_DURATION
            layer = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
            size = max(1, round(max(4, 42 * (1 - progress * 0.6)) * scale))
            color = (69, 156, 239) if effect.team == "ally" else (231, 88, 94)
            if int(effect.age * 20) % 2 == 0:
                color = (255, 224, 192)
            center = (cell_size // 2, cell_size // 2)
            if effect.team == "ally":
                pygame.draw.circle(layer, color, center, size // 2)
            else:
                rect = pygame.Rect(0, 0, size, size)
                rect.center = center
                pygame.draw.rect(layer, color, rect, border_radius=3)
            label = self.label_font.render(effect.uid, True, "white")
            layer.blit(label, label.get_rect(center=center))
            for index in range(6):
                angle = index * math.tau / 6
                radius = (8 + 23 * progress) * scale
                point = (round(center[0] + math.cos(angle) * radius),
                         round(center[1] + math.sin(angle) * radius))
                pygame.draw.circle(layer, (255, 192, 132), point, max(1, round(3 * (1 - progress) * scale)))
            layer.set_alpha(round(255 * (1 - progress)))
            surface.blit(layer, self.geometry.cell_rect(effect.cell)[:2])

        for effect in self.damage_texts:
            progress = effect.age / DAMAGE_DURATION
            text = "-{}".format(effect.amount)
            label = self.damage_font.render(text, True, (255, 217, 150))
            shadow = self.damage_font.render(text, True, (37, 21, 28))
            alpha = round(255 * min(1, (1 - progress) * 3))
            label.set_alpha(alpha)
            shadow.set_alpha(alpha)
            _, cell_y, _, _ = self.geometry.cell_rect(effect.cell)
            x = self.geometry.cell_center(effect.cell)[0]
            y = max(self.geometry.origin[1] + 5, cell_y + 8 - round(progress * 30))
            rect = label.get_rect(midtop=(x, y))
            surface.blit(shadow, rect.move(2, 2))
            surface.blit(label, rect)
        surface.set_clip(old_clip)
