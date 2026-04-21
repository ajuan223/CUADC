"""Simplified attack geometry computation for preburned slot overwrite."""

from __future__ import annotations

from typing import TYPE_CHECKING

from striker.utils.geo import destination_point

if TYPE_CHECKING:
    pass

def compute_attack_geometry(
    drop_lat: float,
    drop_lon: float,
    approach_heading_deg: float,
    approach_distance_m: float,
    exit_distance_m: float,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Compute approach and exit coordinates based on drop point and heading.

    Returns:
        (approach_point, target_point, exit_point)
        where each point is a (lat, lon) tuple.
    """
    # Approach point is behind target
    approach_lat, approach_lon = destination_point(
        drop_lat, drop_lon, (approach_heading_deg + 180) % 360, approach_distance_m
    )
    # Exit point is ahead of target
    exit_lat, exit_lon = destination_point(
        drop_lat, drop_lon, approach_heading_deg, exit_distance_m
    )

    return (
        (approach_lat, approach_lon),
        (drop_lat, drop_lon),
        (exit_lat, exit_lon),
    )
