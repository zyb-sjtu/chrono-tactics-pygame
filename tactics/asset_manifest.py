"""Version-one manifest parsing and references, without Pygame or image I/O."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .data_files import DataError, fields, number, read_json, rooted_path, text, version


@dataclass(frozen=True)
class ImageSpec:
    asset_id: str
    path: Path
    display_size: Tuple[int, int]
    pivot: Tuple[float, float]
    optional: bool


@dataclass(frozen=True)
class AnimationSpec:
    asset_id: str
    frames: Tuple[str, ...]
    fps: float
    loop: bool


@dataclass(frozen=True)
class Manifest:
    images: Tuple[ImageSpec, ...]
    animations: Tuple[AnimationSpec, ...]
    visuals: Tuple[Tuple[str, Tuple[Tuple[str, str], ...]], ...]
    board: Tuple[Tuple[str, str], ...]


def load_manifest(root):
    root = Path(root)
    path = root / "manifest.json"
    label = str(path)
    data = read_json(path)
    fields(data, ("schema_version", "images", "animations", "visuals", "board"), (), label)
    version(data, label)
    for key in ("images", "animations", "visuals", "board"):
        if not isinstance(data[key], dict):
            raise DataError(label + "." + key + ": expected an object")
    images = []
    for asset_id, record in data["images"].items():
        where = label + " images." + text(asset_id, label)
        fields(record, ("path", "display_size", "pivot", "optional"), (), where)
        image_path = rooted_path(root, record["path"], where)
        if image_path.suffix.lower() != ".png":
            raise DataError(where + ": only PNG files are supported")
        size, pivot = record["display_size"], record["pivot"]
        if not isinstance(size, list) or len(size) != 2 or not isinstance(pivot, list) or len(pivot) != 2:
            raise DataError(where + ": display_size/pivot must be pairs")
        for value in size:
            number(value, where + ".display_size", minimum=1, integer=True)
        for value in pivot:
            if number(value, where + ".pivot") > 1:
                raise DataError(where + ": pivot must be between 0 and 1")
        if type(record["optional"]) is not bool:
            raise DataError(where + ": optional must be boolean")
        images.append(ImageSpec(asset_id, image_path, tuple(size), tuple(pivot), record["optional"]))
    animations = []
    for asset_id, record in data["animations"].items():
        where = label + " animations." + text(asset_id, label)
        if asset_id in data["images"]:
            raise DataError(where + ": id also used by an image")
        fields(record, ("frames", "fps", "loop"), (), where)
        if not isinstance(record["frames"], list) or not record["frames"]:
            raise DataError(where + ": frames must be a nonempty array")
        for frame in record["frames"]:
            if text(frame, where + ".frames") not in data["images"]:
                raise DataError(where + ": unknown frame " + frame)
        if number(record["fps"], where + ".fps") <= 0 or type(record["loop"]) is not bool:
            raise DataError(where + ": fps must be positive and loop boolean")
        animations.append(AnimationSpec(asset_id, tuple(record["frames"]), record["fps"], record["loop"]))
    by_animation = {item.asset_id: item for item in animations}
    visuals = []
    for visual_id, record in data["visuals"].items():
        where = label + " visuals." + text(visual_id, label)
        fields(record, (), ("idle", "attack", "death"), where)
        for state, asset_id in record.items():
            text(asset_id, where + "." + state)
            if state == "idle" and asset_id in data["images"]:
                continue
            clip = by_animation.get(asset_id)
            if clip is None or clip.loop != (state == "idle"):
                raise DataError(where + ": " + state + " needs a known " +
                                ("looping idle animation or image" if state == "idle" else "non-looping animation"))
        visuals.append((visual_id, tuple(record.items())))
    fields(data["board"], (), ("floor", "obstacle", "background"), label + ".board")
    for state, asset_id in data["board"].items():
        if text(asset_id, label + ".board." + state) not in data["images"]:
            raise DataError(label + ".board: unknown image " + asset_id)
        if state == "background" and data["images"][asset_id]["optional"]:
            raise DataError(label + ".board.background: background image must be required (optional=false)")
    return Manifest(tuple(images), tuple(animations), tuple(visuals), tuple(data["board"].items()))
