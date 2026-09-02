"""Run the random-cube dataset generator with an episode-random TCP tilt.

This is a thin launcher around
``openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube.py``.
All arguments supported by that script can still be used.  The additional
arguments are::

    --tilt_deg_range MIN MAX
    --tilt_random_seed SEED

Example::

    python scripts/openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt.py \
        --num_episodes 100 \
        --tilt_deg_range 20 60 \
        --tilt_random_seed 123
"""

from __future__ import annotations

import argparse
import random
import sys


def _parse_random_tilt_args() -> tuple[argparse.Namespace, list[str]]:
    """Consume this launcher's arguments and leave the base script arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--tilt_deg_range",
        type=float,
        nargs=2,
        metavar=("MIN", "MAX"),
        default=(-45.0, 45.0),
        help="Sample the robot-base-y TCP tilt uniformly from this range for each attempt.",
    )
    parser.add_argument(
        "--tilt_random_seed",
        type=int,
        default=None,
        help="Seed for reproducible tilt sampling.",
    )
    return parser.parse_known_args()


random_tilt_args, base_argv = _parse_random_tilt_args()
tilt_min, tilt_max = random_tilt_args.tilt_deg_range
if tilt_min > tilt_max:
    raise SystemExit("--tilt_deg_range MIN must be less than or equal to MAX")

# The base module owns the rest of the CLI.  Remove the two launcher-only
# arguments before importing it so its ArgumentParser sees only known options.
sys.argv = [sys.argv[0], *base_argv]

import openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube as base  # noqa: E402


_tilt_rng = random.Random(random_tilt_args.tilt_random_seed)
_original_controller_init = base.PickPlaceController.__init__


def _random_tilt_controller_init(self, robot, scene) -> None:
    """Sample one tilt before constructing each episode controller."""
    sampled_tilt = _tilt_rng.uniform(tilt_min, tilt_max)
    base.args_cli.tilt_deg = sampled_tilt
    print(
        f"[EPISODE] Sampled TCP tilt={sampled_tilt:.2f} deg "
        f"from [{tilt_min:.2f}, {tilt_max:.2f}]"
    )
    _original_controller_init(self, robot, scene)


base.PickPlaceController.__init__ = _random_tilt_controller_init


if __name__ == "__main__":
    print(
        f"[INFO] TCP tilt randomization range=[{tilt_min:.2f}, {tilt_max:.2f}] deg, "
        f"seed={random_tilt_args.tilt_random_seed}"
    )
    base.main()
    base.simulation_app.close()
