"""Window lifecycle, input dispatch, and the main render loop."""

import pygame

from .board import Board
from .board_renderer import BoardRenderer
from .battle import Battle
from .effects import CombatEffects
from .geometry import BoardGeometry
from .panel import InfoPanel
from .scenario import default_scenario
from .settings import CELL_SIZE, FPS, MIN_WINDOW_HEIGHT, PANEL_WIDTH
from .view_models import build_board_view


class Game:
    def __init__(self, scenario=None):
        self.board = Board(default_scenario() if scenario is None else scenario)
        self.geometry = BoardGeometry(self.board.cols, self.board.rows, CELL_SIZE)
        window_size = (self.geometry.width + PANEL_WIDTH, max(MIN_WINDOW_HEIGHT, self.geometry.height))
        # The prototype needs only display and fonts, so do not initialize audio.
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Grid Tactics - Battle Prototype")
        self.clock = pygame.time.Clock()
        self.renderer = BoardRenderer(self.geometry)
        self.battle = Battle(self.board)
        self.panel = InfoPanel(self.geometry.width, window_size[1])
        self.effects = CombatEffects(self.geometry)
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
        cell = self.geometry.cell_at(position)
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
        self.screen.fill((21, 30, 42))
        self.renderer.draw(self.screen, build_board_view(self.board, self.battle, self.selected))
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
