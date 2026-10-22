"""Window lifecycle, input dispatch, and the main render loop."""

import pygame

from .actions import UIAction
from .assets import AssetManager
from .board_renderer import BoardRenderer
from .controller import Controller
from .effects import CombatEffects
from .geometry import BoardGeometry
from .panel import InfoPanel
from .content import load_content
from .data_files import PROJECT_ROOT
from .settings import CELL_SIZE, FPS, MIN_WINDOW_HEIGHT, PANEL_WIDTH


class Game:
    def __init__(self, scenario=None, *, content_root=None, scenario_file="scenarios/training_ground.json",
                 asset_root=None, geometric=False):
        content = load_content(content_root, scenario_file)
        scenario = content.scenario if scenario is None else scenario
        self.geometry = BoardGeometry(scenario.cols, scenario.rows, CELL_SIZE)
        window_size = (self.geometry.width + PANEL_WIDTH, max(MIN_WINDOW_HEIGHT, self.geometry.height))
        # The prototype needs only display and fonts, so do not initialize audio.
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Grid Tactics - Battle Prototype")
        self.clock = pygame.time.Clock()
        try:
            self.assets = None if geometric else AssetManager(
                PROJECT_ROOT / "assets" if asset_root is None else asset_root, content.definitions)
            if self.assets is not None:
                self.assets.preload(CELL_SIZE / 64)
        except Exception:
            pygame.quit()
            raise
        self.renderer = BoardRenderer(self.geometry, self.assets)
        self.panel = InfoPanel(self.geometry.width, window_size[1])
        self.effects = CombatEffects(self.geometry, self.assets)
        self.controller = Controller(scenario, self.effects)
        self.running = True

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            action = {pygame.K_BACKSPACE: UIAction.UNDO,
                      pygame.K_SPACE: UIAction.SKIP_PHASE,
                      pygame.K_RETURN: UIAction.END_TURN}.get(event.key)
            if action is not None:
                self.controller.handle_action(action)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.panel.hit_test(event.pos)
            if action is not None:
                self.controller.handle_action(action)
            else:
                self.controller.click_cell(self.geometry.cell_at(event.pos))

    def update(self, elapsed):
        self.renderer.update(elapsed)
        self.controller.update(elapsed)

    def draw(self):
        self.screen.fill((21, 30, 42))
        view = self.controller.get_view_state()
        self.renderer.draw(self.screen, view.board, self.effects.body_views())
        self.effects.draw(self.screen)
        self.panel.draw(self.screen, view)
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
