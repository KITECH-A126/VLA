"""Inspect one or more Parquet files from the command line.

Examples:
    python inspect_parquet.py tasks.parquet episodes.parquet
    python inspect_parquet.py episodes.parquet --rows 20 --columns episode_index tasks
    python inspect_parquet.py tasks.parquet --all
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print Parquet schema and row contents.")
    parser.add_argument("paths", type=Path, nargs="+", help="Parquet file(s) to inspect.")
    parser.add_argument("--rows", type=int, default=10, help="Number of head rows to print.")
    parser.add_argument("--tail", type=int, default=0, help="Number of tail rows to print.")
    parser.add_argument("--columns", nargs="+", help="Only load and display these columns.")
    parser.add_argument("--all", action="store_true", help="Print every row.")
    parser.add_argument(
        "--commands-only",
        action="store_true",
        help="Print only task commands (and episode indices when present).",
    )
    parser.add_argument(
        "--no-schema", action="store_true", help="Do not print the Arrow schema and metadata."
    )
    args = parser.parse_args()
    if args.rows < 0 or args.tail < 0:
        parser.error("--rows and --tail must be non-negative")
    return args


def inspect_file(path: Path, args: argparse.Namespace) -> None:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise SystemExit(
            "pyarrow is required. Run this script with the project/Isaac Python environment."
        ) from exc

    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        print(f"\n[ERROR] File not found: {resolved}")
        return

    parquet = pq.ParquetFile(resolved)
    if args.commands_only:
        names = parquet.schema_arrow.names
        selected = [name for name in ("episode_index", "task_index", "task", "tasks") if name in names]
        if not selected:
            print(f"[ERROR] No task command column in: {resolved}")
            return
        records = parquet.read(columns=selected).to_pylist()
        for record in records:
            prefix_parts = []
            if "episode_index" in record:
                prefix_parts.append(f"episode={record['episode_index']}")
            if "task_index" in record:
                prefix_parts.append(f"task_index={record['task_index']}")
            command = record.get("task", record.get("tasks"))
            prefix = " ".join(prefix_parts)
            print(f"{prefix}: {command}" if prefix else str(command))
        return

    print("\n" + "=" * 100)
    print(f"FILE: {resolved}")
    print(f"ROWS: {parquet.metadata.num_rows}")
    print(f"COLUMNS: {parquet.metadata.num_columns}")
    print(f"ROW GROUPS: {parquet.metadata.num_row_groups}")
    print(f"CREATED BY: {parquet.metadata.created_by}")
    print("COLUMN NAMES:")
    for index, name in enumerate(parquet.schema_arrow.names):
        print(f"  [{index}] {name}")

    if not args.no_schema:
        print("SCHEMA:")
        print(parquet.schema_arrow)
        metadata = parquet.schema_arrow.metadata
        if metadata:
            print("SCHEMA METADATA:")
            for key, value in metadata.items():
                print(f"  {key.decode(errors='replace')}: {value.decode(errors='replace')}")

    try:
        table = parquet.read(columns=args.columns)
    except Exception as exc:
        print(f"[ERROR] Could not read requested columns: {exc}")
        return

    frame = table.to_pandas()
    # Keep wide LeRobot columns visible instead of silently replacing them with ellipses.
    try:
        import pandas as pd

        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_colwidth", 200)
        pd.set_option("display.width", 240)
    except ImportError:
        pass

    if args.all:
        print("DATA (all rows):")
        print(frame.to_string(index=False))
    elif args.rows:
        print(f"DATA (first {min(args.rows, len(frame))} rows):")
        print(frame.head(args.rows).to_string(index=False))

    if args.tail:
        print(f"DATA (last {min(args.tail, len(frame))} rows):")
        print(frame.tail(args.tail).to_string(index=False))


def main() -> None:
    args = parse_args()
    for path in args.paths:
        inspect_file(path, args)


if __name__ == "__main__":
    main()
