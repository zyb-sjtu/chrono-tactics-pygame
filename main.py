"""Run the offline tactics prototype."""

from tactics.game import Game
from tactics.data_files import DataError
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="scenarios/training_ground.json",
                        help="JSON path relative to content root")
    parser.add_argument("--content-root", help="unit definitions and scenarios root")
    parser.add_argument("--assets", help="asset root containing manifest.json")
    parser.add_argument("--geometry", action="store_true", help="use geometry without loading asset files")
    args = parser.parse_args()
    try:
        Game(content_root=args.content_root, scenario_file=args.scenario,
             asset_root=args.assets, geometric=args.geometry).run()
    except DataError as error:
        parser.exit(2, "Configuration error: {}\n".format(error))
