#!/usr/bin/env python3
"""Burn pre-planned mission to waypoints file for SITL testing.

Generates a .waypoints file with:
1. Dummy Home
2. Takeoff
3. Nav WPs
4. Loiter Unlimited (blocking)
5. 5 empty slots (for attack geometry)
6. Landing sequence
"""

import argparse
from pathlib import Path


def generate_waypoints(output_path: Path) -> None:
    # Example coordinates around ZJG runway
    lat = 30.295
    lon = 120.015
    alt = 50.0

    lines = [
        "QGC WPL 110",
        f"0\t1\t0\t16\t0\t0\t0\t0\t{lat}\t{lon}\t0\t1", # HOME
        f"1\t0\t3\t22\t15\t0\t0\t0\t{lat}\t{lon}\t{alt}\t1", # TAKEOFF
        f"2\t0\t3\t16\t0\t0\t0\t0\t{lat+0.001}\t{lon}\t{alt}\t1", # WP1
        f"3\t0\t3\t16\t0\t0\t0\t0\t{lat+0.002}\t{lon+0.001}\t{alt}\t1", # WP2
        f"4\t0\t3\t17\t0\t0\t0\t0\t{lat+0.002}\t{lon+0.002}\t{alt}\t1", # LOITER UNLIM
        # 5 slots for attack
        "5\t0\t3\t16\t0\t0\t0\t0\t0\t0\t0\t1", # SLOT 0
        "6\t0\t3\t16\t0\t0\t0\t0\t0\t0\t0\t1", # SLOT 1
        "7\t0\t3\t183\t0\t0\t0\t0\t0\t0\t0\t1", # SLOT 2 (SERVO)
        "8\t0\t3\t16\t0\t0\t0\t0\t0\t0\t0\t1", # SLOT 3
        "9\t0\t3\t16\t0\t0\t0\t0\t0\t0\t0\t1", # SLOT 4
        # Landing sequence
        "10\t0\t3\t189\t0\t0\t0\t0\t0\t0\t0\t1", # DO_LAND_START
        f"11\t0\t3\t16\t0\t0\t0\t0\t{lat-0.001}\t{lon-0.001}\t{alt}\t1", # APPROACH
        f"12\t0\t3\t21\t0\t0\t0\t0\t{lat}\t{lon}\t0\t1", # LAND
    ]

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated waypoints file at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", default="test_mission.waypoints")
    args = parser.parse_args()
    generate_waypoints(Path(args.output))
