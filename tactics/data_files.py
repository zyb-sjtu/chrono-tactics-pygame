"""Small strict JSON helpers shared by content and asset-manifest loaders."""

import json
import math
from pathlib import Path, PureWindowsPath

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DataError(ValueError):
    pass


def read_json(path):
    path = Path(path)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DataError("duplicate key: " + key)
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)
    except (OSError, ValueError) as error:
        raise DataError("{}: {}".format(path, error)) from error


def fields(value, required, optional, label):
    if not isinstance(value, dict):
        raise DataError(label + ": expected an object")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        raise DataError("{}: missing {}, unknown {}".format(label, sorted(missing), sorted(unknown)))
    return value


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise DataError(label + ": expected a nonempty string")
    return value


def number(value, label, minimum=0, integer=False):
    valid = type(value) is int if integer else type(value) in (int, float)
    if not valid or (type(value) is float and not math.isfinite(value)) or value < minimum:
        raise DataError(label + ": invalid number")
    return value


def version(data, label):
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise DataError(label + ": schema_version must be 1")


def rooted_path(root, value, label):
    text(value, label)
    if "\\" in value or PureWindowsPath(value).drive or Path(value).is_absolute():
        raise DataError(label + ": expected a relative forward-slash path")
    root = Path(root).resolve()
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise DataError(label + ": path escapes root: " + value)
    return path
