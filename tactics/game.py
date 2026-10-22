"""Window lifecycle, input dispatch, and the main render loop."""

import pygame

from .board import Board
from .battle import Battle
from .effects import CombatEffects
from .panel import InfoPanel
from .settings import FPS, WINDOW_SIZE


class Game:
    def __init__(self):
        # The prototype needs only display and fonts, so do not initialize audio.
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Grid Tactics - Battle Prototype")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.battle = Battle(self.board)
        self.panel = InfoPanel()
        self.effects = CombatEffects()
        self.selected = self.battle.active_unit
        self.running = True

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif self.battle.phase == "resolving":
            return
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.undo()
            elif event.key == pygame.K_SPACE:
                self.battle.skip_phase()
                self.selected = self.battle.active_unit
            elif event.key == pygame.K_RETURN:
                self.battle.end_turn()
                self.selected = self.battle.active_unit
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.panel.undo_button.collidepoint(event.pos):
                self.undo()
            elif self.panel.skip_button.collidepoint(event.pos):
                self.battle.skip_phase()
                self.selected = self.battle.active_unit
            elif self.panel.end_button.collidepoint(event.pos):
                self.battle.end_turn()
                self.selected = self.battle.active_unit
            else:
                self.board_click(event.pos)

    def board_click(self, position):
        if self.battle.phase == "resolving":
            return
        cell = self.board.cell_at(position)
        if cell is None:
            return
        unit = self.board.unit_at(cell)
        if self.battle.active_unit is not None and self.selected is self.battle.active_unit:
            if self.battle.move(cell):
                return
            if unit is not None and self.battle.attack(unit):
                self.effects.play_attack(self.battle.pending_attack)
                return
        if unit is not None:
            self.selected = unit

    def undo(self):
        if not self.battle.undo():
            return False
        self.effects.clear()
        self.selected = self.battle.active_unit
        return True

    def update(self, elapsed):
        self.effects.update(elapsed)
        if self.battle.phase == "resolving" and not self.effects.busy:
            self.battle.finish_attack()
            self.selected = self.battle.active_unit

    def draw(self):
        self.board.draw(self.screen, self.selected, self.battle)
        self.effects.draw(self.screen)
        self.panel.draw(self.screen, self.selected, self.battle)
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                elapsed = self.clock.tick(FPS) / 1000.0
                for event in pygame.event.get():
                    self.handle_event(event)
                if self.running:
                    self.update(elapsed)
                    self.draw()
        finally:
            pygame.quit()
