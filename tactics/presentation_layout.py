"""Strict, graphics-independent presentation configuration rooted in the project."""

from dataclasses import dataclass
from pathlib import Path

from .data_files import DataError, PROJECT_ROOT, fields, number, read_json, rooted_path, text, version
from .perspective_geometry import PerspectiveBoardGeometry


@dataclass(frozen=True)
class PresentationLayout:
    presentation_id: str
    scenario_file: str
    asset_root: Path
    geometry: PerspectiveBoardGeometry
    safe_margin: int
    debug: tuple


def size_pair(value, label):
    if not isinstance(value, list) or len(value) != 2:
        raise DataError(label + ": expected integer size pair")
    return tuple(number(v, label, minimum=1, integer=True) for v in value)


def load_presentation(filename, root=None):
    root = PROJECT_ROOT if root is None else Path(root)
    path = rooted_path(root, filename, "presentation path")
    label = str(path)
    data = read_json(path)
    fields(data, ("schema_version","id","mode","scenario_file","asset_root","viewport","board","hud","debug"), (), label)
    version(data, label)
    if data["mode"] != "perspective":
        raise DataError(label + ": mode must be perspective")
    scenario_file = text(data["scenario_file"], label + ".scenario_file")
    rooted_path(root / "content", scenario_file, label + ".scenario_file")
    asset_root = rooted_path(root, data["asset_root"], label + ".asset_root")
    viewport, board, hud, debug = (data[k] for k in ("viewport","board","hud","debug"))
    fields(viewport, ("reference_size","background_fit"), (), label + ".viewport")
    if viewport["background_fit"] != "contain":
        raise DataError(label + ": background_fit must be contain")
    viewport_size = size_pair(viewport["reference_size"], label + ".viewport.reference_size")
    fields(board, ("cols","rows","reference_image_size","corners"), (), label + ".board")
    cols = number(board["cols"], label + ".board.cols", minimum=1, integer=True)
    rows = number(board["rows"], label + ".board.rows", minimum=1, integer=True)
    image_size = size_pair(board["reference_image_size"], label + ".board.reference_image_size")
    fields(board["corners"], ("p00","p10","p11","p01"), (), label + ".board.corners")
    try:
        geometry = PerspectiveBoardGeometry(cols, rows, tuple(board["corners"][k] for k in ("p00","p10","p11","p01")),
                                            image_size, viewport_size)
    except ValueError as error:
        raise DataError(label + ".board.corners: " + str(error)) from error
    fields(hud, ("layout","safe_margin"), (), label + ".hud")
    margin = number(hud["safe_margin"], label + ".hud.safe_margin", minimum=0, integer=True)
    if (hud["layout"] != "overlay" or viewport_size[0] < 960 or viewport_size[1] < 600
            or 2*margin+860 > viewport_size[0] or 2*margin+254 > viewport_size[1]):
        raise DataError(label + ": overlay HUD needs viewport >= 960x600 and both cards inside safe margins")
    fields(debug, ("show_grid","show_cell_centers","show_coordinates"), (), label + ".debug")
    if any(type(v) is not bool for v in debug.values()):
        raise DataError(label + ".debug: expected booleans")
    return PresentationLayout(text(data["id"], label + ".id"), scenario_file, asset_root, geometry, margin,
                              tuple(debug.items()))
