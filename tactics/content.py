"""Validated JSON unit definitions and scenario construction; standard library only."""

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .data_files import DataError, PROJECT_ROOT, fields, number, read_json, rooted_path, text, version
from .scenario import Scenario, UnitSpawn

STATS = ("max_health", "attack", "defense", "speed", "movement")


@dataclass(frozen=True)
class UnitDefinition:
    definition_id: str
    name: str
    role: str
    max_health: int
    attack: int
    defense: int
    speed: int
    movement: int
    visual_id: str


@dataclass(frozen=True)
class GameContent:
    scenario: Scenario
    definitions: Tuple[UnitDefinition, ...]


def load_content(root=None, scenario_file="scenarios/training_ground.json"):
    root = PROJECT_ROOT / "content" if root is None else Path(root)
    unit_path = root / "units.json"
    data = read_json(unit_path)
    label = str(unit_path)
    fields(data, ("schema_version", "units"), (), label)
    version(data, label)
    if not isinstance(data["units"], list) or not data["units"]:
        raise DataError(label + ": units must be a nonempty array")
    definitions = {}
    for index, record in enumerate(data["units"]):
        where = "{} units[{}]".format(unit_path, index)
        fields(record, ("id", "name", "role", "visual_id") + STATS, (), where)
        for key in ("id", "name", "role", "visual_id"):
            text(record[key], where + "." + key)
        for key in STATS:
            number(record[key], where + "." + key, minimum=1 if key == "max_health" else 0, integer=True)
        if record["id"] in definitions:
            raise DataError(where + ": duplicate definition id " + record["id"])
        definitions[record["id"]] = UnitDefinition(record["id"], record["name"], record["role"],
                                                *(record[key] for key in STATS), record["visual_id"])
    path = rooted_path(root, scenario_file, "scenario_file")
    data = read_json(path)
    label = str(path)
    fields(data, ("schema_version", "id", "cols", "rows", "spawns", "obstacles"), (), label)
    version(data, label)
    if not isinstance(data["spawns"], list) or not isinstance(data["obstacles"], list):
        raise DataError(label + ": spawns and obstacles must be arrays")
    spawns = []
    for index, record in enumerate(data["spawns"]):
        where = "{} spawns[{}]".format(path, index)
        fields(record, ("uid", "definition_id", "team", "cell"), ("overrides",), where)
        definition_id = text(record["definition_id"], where + ".definition_id")
        if definition_id not in definitions:
            raise DataError(where + ": unknown definition " + definition_id)
        definition = definitions[definition_id]
        overrides = record.get("overrides", {})
        fields(overrides, (), ("name", "health") + STATS, where + ".overrides")
        values = {key: getattr(definition, key) for key in ("name", "role") + STATS}
        values["health"] = overrides.get("max_health", definition.max_health)
        values.update(overrides)
        try:
            spawns.append(UnitSpawn(record["uid"], team=record["team"], cell=record["cell"],
                                    definition_id=definition_id, **values))
        except (TypeError, ValueError) as error:
            raise DataError(where + ": " + str(error)) from error
    try:
        scenario = Scenario(data["id"], data["cols"], data["rows"], tuple(spawns), data["obstacles"])
    except (TypeError, ValueError) as error:
        raise DataError(label + ": " + str(error)) from error
    return GameContent(scenario, tuple(definitions.values()))
