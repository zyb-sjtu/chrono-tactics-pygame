"""Generate the second self-contained programmer-art skin, without external art."""

import argparse
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parents[1]


def generate(root):
    root = Path(root)
    for folder in ("tiles", "units"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    floor = pygame.Surface((64, 64), pygame.SRCALPHA)
    floor.fill((34, 39, 61))
    for y in (2, 34):
        pygame.draw.rect(floor, (49, 56, 81), (2, y, 60, 28), border_radius=4)
        pygame.draw.line(floor, (72, 85, 115), (6, y+2), (58, y+2), 2)
    pygame.draw.circle(floor, (83, 108, 129), (12, 18), 2)
    pygame.image.save(floor, str(root / "tiles/floor.png"))
    obstacle = pygame.Surface((64, 80), pygame.SRCALPHA)
    pygame.draw.polygon(obstacle, (79, 91, 115), ((8, 70), (12, 27), (31, 10), (54, 24), (57, 70)))
    pygame.draw.polygon(obstacle, (116, 132, 156), ((12, 27), (31, 10), (36, 44), (8, 70)))
    pygame.draw.line(obstacle, (168, 191, 209), (31, 16), (36, 57), 2)
    pygame.image.save(obstacle, str(root / "tiles/obstacle.png"))
    for role in ("scout", "dummy"):
        for state, count in (("idle", 2 if role == "scout" else 1), ("attack", 3), ("death", 3)):
            for index in range(count):
                body = pygame.Surface((64, 96), pygame.SRCALPHA)
                pygame.draw.ellipse(body, (9, 12, 25, 110), (9, 85, 46, 9))
                if role == "scout":
                    dy = -index if state == "idle" else 0
                    pygame.draw.polygon(body, (31, 73, 121), ((13, 84), (19, 47+dy), (45, 47+dy), (54, 84)))
                    pygame.draw.circle(body, (58, 126, 214), (32, 64+dy), 20)
                    pygame.draw.circle(body, (140, 214, 249), (32, 64+dy), 20, 2)
                    pygame.draw.polygon(body, (65, 142, 211), ((19, 42+dy), (20, 27+dy), (32, 18+dy), (44, 27+dy), (45, 42+dy)))
                    pygame.draw.rect(body, (203, 223, 242), (25, 35+dy, 14, 6), border_radius=2)
                    pygame.draw.polygon(body, (164, 209, 245), ((13, 53), (27, 53), (27, 70), (20, 77), (13, 70)))
                else:
                    pygame.draw.rect(body, (76, 36, 39), (27, 28, 10, 63))
                    pygame.draw.rect(body, (175, 60, 70), (10, 43, 44, 38), border_radius=6)
                    pygame.draw.rect(body, (244, 142, 139), (10, 43, 44, 38), 2, border_radius=6)
                    pygame.draw.line(body, (108, 45, 48), (20, 46), (20, 77), 3)
                    pygame.draw.line(body, (108, 45, 48), (43, 46), (43, 77), 3)
                    pygame.draw.circle(body, (255, 186, 139), (32, 62), 10, 2)
                if state == "attack":
                    pygame.draw.arc(body, (237, 207, 151), (25-index*3, 27, 36, 52), -.9, 1.3, 3+index)
                image = pygame.Surface((64, 96), pygame.SRCALPHA)
                if state == "death":
                    size = (64-index*10, 96-index*17)
                    body = pygame.transform.smoothscale(body, size)
                    body.set_alpha(210-index*80)
                    image.blit(body, ((64-size[0])//2, 96-size[1]))
                else:
                    image.blit(body, (0, 0))
                pygame.image.save(image, str(root / "units" / "{}_{}_{}.png".format(role, state, index)))
    print("Generated 17 dusk PNGs in " + str(root.resolve()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/skins/dusk")
    generate(parser.parse_args().output)
