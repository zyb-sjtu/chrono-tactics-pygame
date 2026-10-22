"""Shared layout settings. Board coordinates are (column, row), zero based."""

COLS = 8
ROWS = 8
CELL_SIZE = 64
BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE
PANEL_WIDTH = 384
WINDOW_SIZE = (BOARD_WIDTH + PANEL_WIDTH, BOARD_HEIGHT)
FPS = 60
