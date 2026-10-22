"""Rebuild the named programmer-art PNGs; never fetch external artwork."""

import argparse
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]


def generate(root):
    root = Path(root)
    (root / "tiles").mkdir(parents=True, exist_ok=True)
    (root / "units").mkdir(parents=True, exist_ok=True)
    tile = pygame.Surface((64, 64), pygame.SRCALPHA)
    tile.fill((43, 62, 72))
    for rect in ((2, 2, 29, 29), (33, 2, 29, 29), (2, 33, 29, 29), (33, 33, 29, 29)):
        pygame.draw.rect(tile, (51, 73, 80), rect, border_radius=3)
        pygame.draw.line(tile, (66, 89, 94), (rect[0]+3, rect[1]+2), (rect[0]+24, rect[1]+2))
    pygame.image.save(tile, str(root / "tiles/floor.png"))
    for state, count in (("idle", 2), ("attack", 3), ("death", 3)):
        for index in range(count):
            image = pygame.Surface((64, 96), pygame.SRCALPHA)
            body = pygame.Surface((64, 96), pygame.SRCALPHA)
            y = -index if state == "idle" else 0
            pygame.draw.ellipse(body, (8, 18, 24, 90), (10, 85, 44, 9))
            pygame.draw.polygon(body, (24, 82, 130), ((17, 50+y), (47, 50+y), (54, 86), (10, 86)))
            pygame.draw.circle(body, (69, 156, 239), (32, 64+y), 21)
            pygame.draw.circle(body, (146, 207, 255), (32, 64+y), 21, 2)
            pygame.draw.circle(body, (198, 222, 230), (32, 36+y), 13)
            pygame.draw.polygon(body, (38, 100, 157), ((17, 35+y), (32, 14+y), (49, 35+y)))
            pygame.draw.rect(body, (255, 204, 109), (21, 45+y, 23, 6), border_radius=2)
            if state == "attack":
                pygame.draw.arc(body, (255, 225, 144), (25-index*4, 28, 36, 49), -.9, 1.3, 3+index)
            if state == "death":
                size = (64-index*9, 96-index*14)
                body = pygame.transform.smoothscale(body, size)
                body.set_alpha(220-index*85)
                image.blit(body, ((64-size[0])//2, 96-size[1]))
            else:
                image.blit(body, (0, 0))
            pygame.image.save(image, str(root / "units" / ("scout_{}_{}.png".format(state, index))))
    print("Generated 9 demo PNGs in " + str(root.resolve()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "assets")
    generate(parser.parse_args().output)
