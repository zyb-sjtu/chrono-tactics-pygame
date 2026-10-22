"""Inspect measured seams or collect a draft homography calibration; never changes gameplay config."""

import argparse
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tactics.data_files import DataError, fields, read_json, rooted_path, version
from tactics.perspective_geometry import BackgroundFit, PerspectiveBoardGeometry, pair
from tactics.presentation_layout import size_pair

DEFAULT = ROOT / "docs/calibration/war_torn_observations.json"
CORNER_NAMES = ("p00", "p10", "p11", "p01")


def load_observations(path):
    data = read_json(path)
    label = str(path)
    fields(data, ("schema_version", "status", "image", "sha256", "image_size", "viewport_size",
                  "physical_span", "corners", "samples", "annotation"), (), label)
    version(data, label)
    if data["status"] not in ("diagnostic_only", "draft"):
        raise DataError(label + ": observations must be diagnostic_only or draft")
    image = rooted_path(ROOT, data["image"], label + ".image")
    raw = image.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 24:
        raise DataError(label + ": invalid native PNG")
    if hashlib.sha256(raw).hexdigest() != data["sha256"]:
        raise DataError(label + ": background SHA256 changed; recheck annotations")
    native = struct.unpack(">II", raw[16:24])
    if native != size_pair(data["image_size"], label + ".image_size"):
        raise DataError(label + ": native image size differs from observations")
    span = size_pair(data["physical_span"], label + ".physical_span")
    viewport = size_pair(data["viewport_size"], label + ".viewport_size")
    fields(data["corners"], CORNER_NAMES, (), label + ".corners")
    try:
        geometry = PerspectiveBoardGeometry(*span,
            tuple(data["corners"][key] for key in CORNER_NAMES), native, viewport)
    except (TypeError, ValueError) as error:
        raise DataError(label + ": " + str(error)) from error
    if not isinstance(data["samples"], list) or not data["samples"]:
        raise DataError(label + ": independent interior samples are required")
    seen = set()
    for sample in data["samples"]:
        fields(sample, ("node", "image", "band"), (), label + ".sample")
        node = pair(sample["node"], "sample node")
        point = pair(sample["image"], "sample image")
        if (any(type(v) is not int for v in node)
                or not (0 < node[0] < geometry.cols and 0 < node[1] < geometry.rows)
                or not (0 <= point[0] < native[0] and 0 <= point[1] < native[1])
                or node in seen or sample["band"] not in ("far", "middle", "near")):
            raise DataError(label + ": duplicate, outside, or invalid interior sample")
        seen.add(node)
    return data, geometry


def measure(data, geometry):
    """Only held-out observations enter error statistics; four fitted corners do not."""
    errors = []
    for sample in data["samples"]:
        projected = geometry.project(sample["node"])
        observed = geometry.fit.to_screen(sample["image"])
        errors.append({"node": sample["node"], "observed_image": sample["image"],
                       "predicted_image": list(geometry.fit.to_image(projected)),
                       "band": sample["band"], "error_viewport_px": math.dist(projected, observed)})

    def statistics(points):
        values = [point["error_viewport_px"] for point in points]
        return {"count": len(values), "mean_px": sum(values)/len(values), "max_px": max(values)}

    summary = statistics(errors)
    report = {"image_sha256": data["sha256"], "viewport_size": list(geometry.viewport_size),
              "scale": geometry.fit.scale, "offset": list(geometry.fit.offset),
              "measured_physical_span": data["physical_span"], "interior": summary,
              "bands": {band: statistics([p for p in errors if p["band"] == band])
                        for band in ("far", "middle", "near") if any(p["band"] == band for p in errors)},
              "points": errors, "local_threshold_met": summary["mean_px"] <= 6 and summary["max_px"] <= 12,
              "requested_8x8_verified": False,
              "reason": "This is a diagnostic strip, not a measured complete 8x8 region. No acceptance claim or automatic config export."}
    return report


def inspect_extent(geometry):
    """Finite diagnostic search, never promotes extrapolated vertices to measurements."""
    candidates = []
    for row in range(-16, 9):
        for col in range(-16, 9):
            nodes = ((col,row),(col+8,row),(col+8,row+8),(col,row+8))
            try:
                points = [geometry.fit.to_image(geometry.project(node)) for node in nodes]
            except ValueError:
                continue
            if all(0 <= x <= geometry.reference_size[0] and 0 <= y <= geometry.reference_size[1]
                   for x,y in points):
                candidates.append({"origin_node": [col,row], "predicted_corners_image": points,
                                   "all_y_at_least_160": all(y >= 160 for _,y in points)})
    return {"search_origins": "integer col,row in [-16,8] relative to diagnostic strip",
            "warning": "EXTRAPOLATION ONLY; not measured corners, not a proof of global image topology. y>=160 is a loose necessary paving bound, not a segmentation mask.",
            "candidates_inside_png": candidates,
            "candidates_above_loose_paving_bound": sum(c["all_y_at_least_160"] for c in candidates)}


def capture_game(data, geometry, output):
    import pygame
    from tactics.game import Game

    game = Game(presentation_file="presentations/war_torn_8x8.json", debug_grid=True)
    try:
        geometry = replace(geometry, viewport_size=game.screen.get_size())
        game.draw()
        font = pygame.font.Font(None, 18)
        polygon = [geometry.fit.to_screen(data["corners"][key]) for key in CORNER_NAMES]
        pygame.draw.polygon(game.screen, (255,210,70), polygon, 2)
        for key, point in zip(CORNER_NAMES, polygon):
            pygame.draw.circle(game.screen, (255,210,70), point, 5, 1)
            game.screen.blit(font.render("REF " + key, True, (255,230,90)), (point[0]+6,point[1]-20))
        for sample in data["samples"]:
            observed = geometry.fit.to_screen(sample["image"])
            predicted = geometry.project(sample["node"])
            pygame.draw.line(game.screen, (255,160,110), observed, predicted, 2)
            pygame.draw.circle(game.screen, (80,255,170), observed, 4, 1)
            pygame.draw.circle(game.screen, (255,140,140), predicted, 2)
            game.screen.blit(font.render("REF {},{}".format(*sample["node"]), True, (110,255,180)),
                             (observed[0]+5,observed[1]+4))
        pygame.display.flip()
        pygame.event.pump()
        pygame.image.save(game.screen, str(output))
        print("Actual Game diagnostic screenshot; SDL driver=" + pygame.display.get_driver())
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run()
    finally:
        pygame.quit()


def pick(image_path, cols, rows, output):
    """Four corners followed by row-major interior samples; saves raw mouse observations only."""
    import pygame

    raw = image_path.read_bytes()
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((1280,720))
    pygame.display.set_caption("Homography calibration DRAFT - native image coordinates")
    original = pygame.image.load(str(image_path)).convert_alpha()
    fit = BackgroundFit(original.get_size(), screen.get_size())
    background = pygame.transform.smoothscale(original, tuple(round(v*fit.scale) for v in original.get_size()))
    font = pygame.font.Font(None, 22)
    order = [(0,0),(cols,0),(cols,rows),(0,rows)]
    order += [(col,row) for row in range(1,rows) for col in range(1,cols)]
    points, geometry, error, preview = [], None, "", True
    clock = pygame.time.Clock()
    running = True
    try:
        while running:
            changed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                      and event.pos[1] >= 76 and len(points) < len(order)):
                    point = fit.to_image(event.pos)
                    if 0 <= point[0] < original.get_width() and 0 <= point[1] < original.get_height():
                        points.append(tuple(round(v,2) for v in point))
                        changed = True
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_BACKSPACE,pygame.K_z) and points:
                        points.pop()
                        changed = True
                    elif event.key == pygame.K_p:
                        preview = not preview
                    elif event.key == pygame.K_s:
                        result = {"schema_version":1,"status":"draft", "image":image_path.relative_to(ROOT).as_posix(),
                                  "sha256":hashlib.sha256(raw).hexdigest(), "image_size":list(original.get_size()),
                                  "viewport_size":[1280,720],"physical_span":[cols,rows],
                                  "corners":dict(zip(CORNER_NAMES,points[:4])),
                                  "samples":[{"node":node,"image":point,"band":"far" if node[1]<rows/3 else "near" if node[1]>rows*2/3 else "middle"}
                                             for node,point in zip(order[4:],points[4:])],
                                  "annotation":"Draft raw clicks only. Verify stone counts and independent seam landmarks before runtime adoption."}
                        output.parent.mkdir(parents=True,exist_ok=True)
                        output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                        error = "DRAFT saved: " + str(output)
            if changed:
                geometry, error = None, ""
                if len(points) >= 4:
                    try:
                        geometry = PerspectiveBoardGeometry(cols,rows,tuple(points[:4]),original.get_size())
                    except ValueError as problem:
                        error = str(problem)
            screen.fill((21,30,42))
            screen.blit(background,tuple(round(v) for v in fit.offset))
            if preview and geometry is not None:
                for row in range(rows):
                    for col in range(cols):
                        pygame.draw.polygon(screen,(140,215,235),geometry.cell_polygon((col,row)),1)
            for index,point in enumerate(points):
                screen_point = fit.to_screen(point)
                pygame.draw.circle(screen,(80,255,160),screen_point,4,1)
                screen.blit(font.render(str(order[index]),True,(245,230,150)),screen_point)
            next_point = str(order[len(points)]) if len(points)<len(order) else "all observations collected"
            bar = pygame.Surface((1280,76),pygame.SRCALPHA)
            bar.fill((15,22,30,220))
            screen.blit(bar,(0,0))
            for index,line in enumerate(("DRAFT: pick real seam intersections. Next="+next_point,
                                         "Left: mark | Backspace/Z: undo | P: preview | S: save draft | Esc: quit",
                                         error)):
                screen.blit(font.render(line,True,(240,232,206)),(12,6+index*22))
            pygame.display.flip()
            clock.tick(30)
    finally:
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations",type=Path,default=DEFAULT)
    parser.add_argument("--report",type=Path)
    parser.add_argument("--screenshot",type=Path,help="actual Game with F3 plus observed seam overlay")
    parser.add_argument("--pick",action="store_true",help="open draft four-corner and interior-point picker")
    parser.add_argument("--cols",type=int,default=8)
    parser.add_argument("--rows",type=int,default=8)
    parser.add_argument("--output",type=Path,default=ROOT/".delivery/war_torn_calibration_draft.json")
    args = parser.parse_args()
    try:
        if args.pick:
            if args.cols < 2 or args.rows < 2:
                raise DataError("calibration requires at least 2 rows/columns for interior samples")
            pick(ROOT/"assets/skins/war_torn/backgrounds/battlefield.png",args.cols,args.rows,args.output)
            return
        data, geometry = load_observations(args.observations)
        report = measure(data,geometry)
        report["extent_diagnostic"] = inspect_extent(geometry)
        encoded = json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(encoded,encoding="utf-8")
        print(encoded)
        if args.screenshot:
            capture_game(data,geometry,args.screenshot)
    except (OSError,ValueError,KeyError,TypeError) as error:
        parser.exit(2,"Calibration error: {}\n".format(error))


if __name__ == "__main__":
    main()
