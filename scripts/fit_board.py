"""Refine ONE homography from native-image observations; keep holdouts independent."""

import argparse
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
from tactics.perspective_geometry import PerspectiveBoardGeometry, pair, transform
from tactics.presentation_layout import size_pair

DEFAULT = ROOT / "docs/calibration/war_torn_map_observations.json"
PRESENTATION = ROOT / "presentations/war_torn_8x8.json"
NAMES = ("p00", "p10", "p11", "p01")


def solve(matrix, values):
    rows = [list(row)+[value] for row,value in zip(matrix,values)]
    for col in range(len(values)):
        pivot = max(range(col,len(values)), key=lambda r: abs(rows[r][col]))
        rows[col],rows[pivot] = rows[pivot],rows[col]
        divisor = rows[col][col]
        if abs(divisor) < 1e-12:
            raise DataError("calibration observations do not determine a homography")
        rows[col] = [v/divisor for v in rows[col]]
        for row in range(len(values)):
            if row != col:
                factor = rows[row][col]
                rows[row] = [a-factor*b for a,b in zip(rows[row],rows[col])]
    return tuple(row[-1] for row in rows)


def fit_corners(data):
    """Offline linear least squares. Only role=calibration is allowed into the fit."""
    ox,oy,width,height = data["reference_region"]
    iw,ih = data["image_size"]
    equations,values = [],[]
    for item in data["observations"]:
        if item["role"] != "calibration":
            continue
        u,v = (item["node"][0]-ox)/width,(item["node"][1]-oy)/height
        x,y = item["image"][0]/iw,item["image"][1]/ih
        equations.extend(((u,v,1,0,0,0,-x*u,-x*v),(0,0,0,u,v,1,-y*u,-y*v)))
        values.extend((x,y))
    normal = [[sum(row[i]*row[j] for row in equations) for j in range(8)] for i in range(8)]
    rhs = [sum(row[i]*v for row,v in zip(equations,values)) for i in range(8)]
    matrix = (*solve(normal,rhs),1)
    return tuple(tuple(v*d for v,d in zip(transform(matrix,p),(iw,ih)))
                 for p in ((0,0),(1,0),(1,1),(0,1)))


def load_map(path=DEFAULT):
    data = read_json(path)
    label = str(path)
    fields(data,("schema_version","image","sha256","image_size","viewport_size","logical_size",
                 "reference_region","cells","observations","annotation"),(),label)
    version(data,label)
    image = rooted_path(ROOT,data["image"],label+".image")
    raw = image.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n" or len(raw) < 24 or hashlib.sha256(raw).hexdigest() != data["sha256"]:
        raise DataError("native background changed or invalid PNG; recheck observations")
    native = struct.unpack(">II",raw[16:24])
    if native != size_pair(data["image_size"],label+".image_size"):
        raise DataError("native image dimensions differ from observations")
    cols,rows = size_pair(data["logical_size"],label+".logical_size")
    viewport = size_pair(data["viewport_size"],label+".viewport_size")
    if not isinstance(data["observations"],list):
        raise DataError("observations must be a list")
    observed = {}
    for item in data["observations"]:
        fields(item,("node","image","role","band"),(),label+".observation")
        node,point = pair(item["node"],"node"),pair(item["image"],"image point")
        if (any(type(v) is not int for v in node) or not (0 <= node[0] <= cols and 0 <= node[1] <= rows)
                or not (0 <= point[0] < native[0] and 0 <= point[1] < native[1]) or node in observed
                or item["role"] not in ("calibration","validation") or item["band"] not in ("far","middle","near")):
            raise DataError("duplicate or invalid native observation")
        observed[node] = point
    if any(sum(item["role"]==role for item in data["observations"]) < 4 for role in ("calibration","validation")):
        raise DataError("at least four calibration and four independent validation points required")
    if any(not any(p["role"]=="validation" and p["band"]==band for p in data["observations"])
           for band in ("far","middle","near")):
        raise DataError("independent validation must cover far, middle and near bands")
    corners = fit_corners(data)
    geometry = PerspectiveBoardGeometry(cols,rows,corners,native,viewport,data["reference_region"],data["cells"])
    needed = {(c+dx,r+dy) for c,r in geometry.cells for dx,dy in ((0,0),(1,0),(1,1),(0,1))}
    if needed != observed.keys():
        raise DataError("every playable tile vertex must have a real observation, with no unused nodes")
    return data,geometry


def statistics(points):
    values = [item["error_px"] for item in points]
    return {"count":len(values),"mean_px":sum(values)/len(values),"max_px":max(values)}


def measure_map(data,geometry):
    points = [{**item,"predicted_image":list(geometry.fit.to_image(geometry.project(item["node"]))),
               "error_px":math.dist(geometry.project(item["node"]),geometry.fit.to_screen(item["image"]))}
              for item in data["observations"]]
    ox,oy,width,height = data["reference_region"]
    nodes = ((ox,oy),(ox+width,oy),(ox+width,oy+height),(ox,oy+height))
    observed = {tuple(item["node"]):item["image"] for item in points}
    baseline = PerspectiveBoardGeometry(geometry.cols,geometry.rows,tuple(observed[n] for n in nodes),
        geometry.reference_size,geometry.viewport_size,geometry.reference_region,geometry.cells)
    baseline_points = [{"error_px":math.dist(baseline.project(p["node"]),baseline.fit.to_screen(p["image"]))}
                       for p in points if tuple(p["node"]) not in nodes]
    validation = [p for p in points if p["role"]=="validation"]
    cells = frozenset(geometry.cells)
    interior = [p for p in validation if all((p["node"][0]+dx,p["node"][1]+dy) in cells
                for dx,dy in ((-1,-1),(0,-1),(0,0),(-1,0)))]
    metrics = statistics(validation)
    all_metrics = statistics(points)
    return {"image_sha256":data["sha256"],"viewport_size":list(geometry.viewport_size),
            "scale":geometry.fit.scale,"offset":list(geometry.fit.offset),"playable_cells":len(geometry.cells),
            "method":"One homography refined offline; runtime PerspectiveBoardGeometry formula unchanged.",
            "reference_region":data["reference_region"],"fitted_corners_image":dict(zip(NAMES,geometry.corners)),
            "observed_reference_corners_image":dict(zip(NAMES,(observed[n] for n in nodes))),
            "four_observed_corners_baseline":statistics(baseline_points),
            "calibration":statistics([p for p in points if p["role"]=="calibration"]),
            "independent_validation":metrics,"all_vertices":all_metrics,
            "independent_interior":statistics(interior) if interior else None,
            "bands":{band:statistics([p for p in validation if p["band"]==band]) for band in ("far","middle","near")},
            "threshold_met":metrics["mean_px"] <= 6 and metrics["max_px"] <= 12
                            and all_metrics["mean_px"] <= 6 and all_metrics["max_px"] <= 12,
            "full_rectangular_8x8":False,"points":points}


def check_presentation(data,geometry,path=PRESENTATION):
    board = read_json(path)["board"]
    if (board.get("reference_region") != data["reference_region"] or board.get("cells") != data["cells"]
            or board["reference_image_size"] != data["image_size"]
            or [board["cols"],board["rows"]] != data["logical_size"]
            or any(math.dist(board["corners"][name],point) > 1e-5 for name,point in zip(NAMES,geometry.corners))):
        raise DataError("presentation differs from measured calibration; regenerate explicitly with --write-presentation")


def capture_game(data,geometry,output):
    """Capture the actual Game/F3 surface; optional measured-point overlay is diagnostic UI."""
    import pygame
    from tactics.game import Game
    game = Game(presentation_file=PRESENTATION.relative_to(ROOT).as_posix(),debug_grid=True)
    try:
        game.draw()
        for item in data["observations"]:
            if item["role"] != "validation":
                continue
            measured = geometry.fit.to_screen(item["image"])
            projected = geometry.project(item["node"])
            pygame.draw.line(game.screen,(255,180,130),measured,projected,1)
            pygame.draw.circle(game.screen,(80,255,150),measured,4,1)
            pygame.draw.circle(game.screen,(255,140,140),projected,2)
        pygame.display.flip()
        pygame.event.pump()
        output.parent.mkdir(parents=True,exist_ok=True)
        pygame.image.save(game.screen,str(output))
        print("Actual Game/F3 capture; SDL driver="+pygame.display.get_driver())
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run()
    finally:
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations",type=Path,default=DEFAULT)
    parser.add_argument("--report",type=Path)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--write-presentation",action="store_true")
    parser.add_argument("--screenshot",type=Path,help="actual Game/F3 with held-out seam markers")
    args = parser.parse_args()
    try:
        data,geometry = load_map(args.observations)
        report = measure_map(data,geometry)
        if not report["threshold_met"]:
            raise DataError("measured alignment does not meet 6/12 px thresholds")
        if args.write_presentation:
            config = read_json(PRESENTATION)
            config["board"].update(corners=dict(zip(NAMES,geometry.corners)),
                                   reference_region=data["reference_region"],cells=data["cells"])
            PRESENTATION.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if args.check:
            check_presentation(data,geometry)
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if args.screenshot:
            check_presentation(data,geometry)
            capture_game(data,geometry,args.screenshot)
        print(json.dumps({k:v for k,v in report.items() if k != "points"},ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as error:
        parser.exit(2,"Calibration error: {}\n".format(error))


if __name__ == "__main__":
    main()
