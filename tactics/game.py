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
from .data_files import DataError, PROJECT_ROOT
from .presentation_layout import load_presentation
from .perspective_board_renderer import PerspectiveBoardRenderer
from .scene_hud import SceneHUD
from .settings import CELL_SIZE, FPS, MIN_WINDOW_HEIGHT, PANEL_WIDTH


class Game:
    def __init__(self, scenario=None, *, content_root=None, scenario_file=None,
                 asset_root=None, geometric=False, presentation_file=None, debug_grid=False):
        layout = load_presentation(presentation_file) if presentation_file is not None else None
        if layout is not None:
            if any(value is not None for value in (content_root,scenario_file,asset_root)) or geometric:
                raise DataError("--presentation cannot be combined with --scenario, --assets, --content-root or --geometry")
            scenario_file, asset_root = layout.scenario_file, layout.asset_root
        elif debug_grid:
            raise DataError("--debug-grid needs --presentation")
        scenario_file = scenario_file or "scenarios/training_ground.json"
        content = load_content(content_root, scenario_file)
        scenario = content.scenario if scenario is None else scenario
        if layout is not None:
            self.geometry = layout.geometry
            if (scenario.cols,scenario.rows) != (self.geometry.cols,self.geometry.rows):
                raise DataError("presentation board dimensions differ from scenario")
            cells = frozenset(self.geometry.cells)
            voids = {(c,r) for r in range(scenario.rows) for c in range(scenario.cols)} - cells
            if not voids <= set(scenario.obstacles):
                raise DataError("presentation void cells must be blocked in scenario.obstacles")
            if any(unit.cell not in cells for unit in scenario.units):
                raise DataError("scenario unit starts outside presentation playable cells")
            window_size = self.geometry.viewport_size
        else:
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
            if layout is not None:
                debug = dict(layout.debug)
                if debug_grid:
                    debug = dict.fromkeys(debug,True)
                self.renderer = PerspectiveBoardRenderer(self.geometry,self.assets,debug.items())
                self.panel = SceneHUD(window_size,layout.safe_margin)
            else:
                self.renderer = BoardRenderer(self.geometry, self.assets)
                self.panel = InfoPanel(self.geometry.width, window_size[1])
            self.effects = CombatEffects(self.geometry, self.assets)
            self.controller = Controller(scenario, self.effects)
        except Exception:
            pygame.quit()
            raise
        self.running = True

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F3 and isinstance(self.renderer,PerspectiveBoardRenderer):
                self.renderer.toggle_debug()
            action = {pygame.K_BACKSPACE: UIAction.UNDO,
                      pygame.K_SPACE: UIAction.SKIP_PHASE,
                      pygame.K_RETURN: UIAction.END_TURN}.get(event.key)
            if action is not None:
                self.controller.handle_action(action)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            action = self.panel.hit_test(event.pos)
            if action is not None:
                self.controller.handle_action(action)
            elif isinstance(self.panel,SceneHUD) and self.panel.contains(event.pos):
                return
            else:
                cell = (self.renderer.cell_at(event.pos,self.controller.get_view_state().board)
                        if isinstance(self.renderer,PerspectiveBoardRenderer) else self.geometry.cell_at(event.pos))
                self.controller.click_cell(cell)

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
