#!/usr/bin/env python3
"""Generate the three-color dataset and save cube positions outside its schema.

This is a thin wrapper around the existing three-color degree-based generator.
The LeRobot dataset remains unchanged. Human-readable CSV/JSON files record
every sampled attempt and every successfully saved episode, including sampled
drop coordinates and the three cubes' settled coordinates before motion.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path


def parse_wrapper_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--position_log_dir",
        type=Path,
        default=None,
        help="Default: DATASET_ROOT_cube_positions (a sibling of the dataset).",
    )
    parser.add_argument("--overwrite_position_logs", action="store_true")
    return parser.parse_known_args()


wrapper_args, generator_argv = parse_wrapper_args()
sys.argv = [sys.argv[0], *generator_argv]
import openarm_table_dual_realsense_ik_pick_place_make_dataset_three_color_random_cube_random_tilt_gripper_mapped_degree as generator  # noqa: E402


base = generator.base
torch = base.torch
dataset_root = Path(base.args_cli.dataset_root).expanduser().resolve()
log_dir = (
    wrapper_args.position_log_dir.expanduser().resolve()
    if wrapper_args.position_log_dir is not None
    else dataset_root.with_name(dataset_root.name + "_cube_positions")
)
overwrite_logs = wrapper_args.overwrite_position_logs or base.args_cli.overwrite_dataset
if log_dir.exists():
    if overwrite_logs:
        shutil.rmtree(log_dir)
    else:
        raise RuntimeError(
            f"Cube-position log directory already exists: {log_dir}. "
            "Use --overwrite_position_logs or choose another --position_log_dir."
        )
log_dir.mkdir(parents=True)
(log_dir / "attempts").mkdir()
(log_dir / "saved_episodes").mkdir()


ATTEMPT_FIELDS = [
    "attempt_index",
    "planned_episode_index",
    "target_color",
    "task",
    "status",
    "failure_reason",
    "red_sampled_x",
    "red_sampled_y",
    "red_sampled_z",
    "blue_sampled_x",
    "blue_sampled_y",
    "blue_sampled_z",
    "yellow_sampled_x",
    "yellow_sampled_y",
    "yellow_sampled_z",
    "red_settled_x",
    "red_settled_y",
    "red_settled_z",
    "blue_settled_x",
    "blue_settled_y",
    "blue_settled_z",
    "yellow_settled_x",
    "yellow_settled_y",
    "yellow_settled_z",
]
SAVED_FIELDS = ["episode_index", *ATTEMPT_FIELDS]
attempt_csv = log_dir / "attempts.csv"
saved_csv = log_dir / "saved_episodes.csv"


def initialize_csv(path: Path, fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        csv.DictWriter(file, fieldnames=fields).writeheader()


initialize_csv(attempt_csv, ATTEMPT_FIELDS)
initialize_csv(saved_csv, SAVED_FIELDS)

state: dict[str, object] = {"attempt_index": 0, "current": None, "recorder": None}


def xyz_fields(prefix: str, positions: dict[str, tuple[float, float, float]], suffix: str):
    values: dict[str, float] = {}
    for color in generator.COLORS:
        xyz = positions[color]
        values[f"{color}_{suffix}_x"] = float(xyz[0])
        values[f"{color}_{suffix}_y"] = float(xyz[1])
        values[f"{color}_{suffix}_z"] = float(xyz[2])
    return values


def append_csv(path: Path, fields: list[str], row: dict[str, object]) -> None:
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writerow({field: row.get(field, "") for field in fields})
        file.flush()
        os.fsync(file.fileno())


def save_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


original_reset = generator.reset_three_color_scene


def logged_reset(scene):
    positions = original_reset(scene)
    state["attempt_index"] = int(state["attempt_index"]) + 1
    recorder = state.get("recorder")
    saved_count = int(recorder.saved_episodes) if recorder is not None else 0
    state["current"] = {
        "attempt_index": state["attempt_index"],
        "planned_episode_index": saved_count,
        "target_color": generator.ACTIVE_COLOR,
        "task": base.args_cli.task,
        "sampled_positions": {
            color: [float(value) for value in positions[color]]
            for color in generator.COLORS
        },
        "settled_positions": {},
    }
    return positions


generator.reset_three_color_scene = logged_reset


original_controller_init = base.PickPlaceController.__init__


def logged_controller_init(self, robot, scene) -> None:
    original_controller_init(self, robot, scene)
    current = state.get("current")
    if current is None:
        return
    settled = {}
    for color, asset_name in generator.CUBE_ASSET_NAMES.items():
        xyz = scene[asset_name].data.root_pos_w[0].detach().cpu().tolist()
        settled[color] = [float(value) for value in xyz]
    current["settled_positions"] = settled


base.PickPlaceController.__init__ = logged_controller_init


original_recorder_init = base.MultiEpisodeLeRobotRecorder.__init__
original_save_episode = base.MultiEpisodeLeRobotRecorder.save_episode
original_discard_episode = base.MultiEpisodeLeRobotRecorder.discard_episode


def logged_recorder_init(self, *args, **kwargs) -> None:
    original_recorder_init(self, *args, **kwargs)
    state["recorder"] = self


def finalize_current(status: str, failure_reason: str = "", episode_index: int | None = None):
    current = state.get("current")
    if current is None:
        return
    sampled = current["sampled_positions"]
    settled = current.get("settled_positions") or sampled
    flat = {
        "attempt_index": current["attempt_index"],
        "planned_episode_index": current["planned_episode_index"],
        "target_color": current["target_color"],
        "task": current["task"],
        "status": status,
        "failure_reason": failure_reason,
        **xyz_fields("", sampled, "sampled"),
        **xyz_fields("", settled, "settled"),
    }
    payload = {
        **flat,
        "sampled_positions": sampled,
        "settled_positions": settled,
    }
    append_csv(attempt_csv, ATTEMPT_FIELDS, flat)
    save_json(
        log_dir / "attempts" / f"attempt_{int(current['attempt_index']):06d}.json",
        payload,
    )
    if episode_index is not None:
        saved_flat = {"episode_index": episode_index, **flat}
        append_csv(saved_csv, SAVED_FIELDS, saved_flat)
        save_json(
            log_dir / "saved_episodes" / f"episode_{episode_index:06d}.json",
            {"episode_index": episode_index, **payload},
        )
    state["current"] = None


def logged_save_episode(self) -> None:
    original_save_episode(self)
    # LeRobot episode indices are zero-based; saved_episodes was incremented.
    finalize_current("saved", episode_index=int(self.saved_episodes) - 1)


def logged_discard_episode(self, reason: str) -> None:
    original_discard_episode(self, reason)
    finalize_current("discarded", failure_reason=reason)


base.MultiEpisodeLeRobotRecorder.__init__ = logged_recorder_init
base.MultiEpisodeLeRobotRecorder.save_episode = logged_save_episode
base.MultiEpisodeLeRobotRecorder.discard_episode = logged_discard_episode

manifest = {
    "dataset_root": str(dataset_root),
    "position_log_dir": str(log_dir),
    "coordinate_frame": "world",
    "units": "metres",
    "colors": list(generator.COLORS),
    "note": "Position files are inspection-only and are not LeRobot training features.",
}
save_json(log_dir / "manifest.json", manifest)
print(f"[POSITION LOG] inspection logs: {log_dir}")
print(f"[POSITION LOG] attempts: {attempt_csv}")
print(f"[POSITION LOG] saved episodes: {saved_csv}")


if __name__ == "__main__":
    try:
        generator.main()
    finally:
        base.simulation_app.close()
