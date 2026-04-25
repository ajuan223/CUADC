from __future__ import annotations

from pathlib import Path

from scripts.burn_mission import generate_waypoints


def test_generate_waypoints_for_zjg2_writes_preburned_mission(tmp_path: Path) -> None:
    output_path = tmp_path / "mission.waypoints"

    generate_waypoints(output_path, "zjg2")

    content = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert content[0] == "QGC WPL 110"

    rows = [line.split("\t") for line in content[1:]]
    commands = [int(row[3]) for row in rows]

    assert commands[0] == 16
    assert commands[1] == 22
    assert commands.count(17) == 1
    assert commands.count(189) == 1
    assert commands[-1] == 21
    assert len(rows) > 10

    loiter_index = commands.index(17)
    land_start_index = commands.index(189)
    assert loiter_index < land_start_index < len(rows) - 1

    scan_rows = rows[2:loiter_index]
    assert len(scan_rows) >= 4
    assert all(float(row[10]) > 0 for row in scan_rows)
    assert all(float(row[8]) != 0 and float(row[9]) != 0 for row in scan_rows)
