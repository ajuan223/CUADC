"""Landing sequence generation for fixed-wing aircraft."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from striker.flight.mission_geometry import MissionGeometryResult
from striker.flight.navigation import make_do_land_start, make_nav_land, make_nav_waypoint

logger = structlog.get_logger(__name__)


def generate_landing_sequence(
    geometry: MissionGeometryResult,
    mav: Any,
    start_seq: int = 0,
) -> list[Any]:
    """Generate a fixed-wing landing sequence from procedural geometry.

    When ``use_do_land_start`` is ``True`` (default, real deployment):
        DO_LAND_START → approach (NAV_WAYPOINT) → NAV_LAND (3 items)

    When ``use_do_land_start`` is ``False`` (SITL fallback):
        approach (NAV_WAYPOINT) → NAV_LAND (2 items)

    Parameters
    ----------
    geometry:
        Mission geometry result with derived landing approach and touchdown.
    mav:
        pymavlink connection object.

    Returns
    -------
    list of MAVLink mission items.
    """
    approach_lat, approach_lon, approach_alt = geometry.landing_approach
    touchdown_lat, touchdown_lon, touchdown_alt = geometry.landing_touchdown

    items: list[Any] = []
    seq = start_seq

    # DO_LAND_START (real deployment only)
    if geometry.use_do_land_start:
        items.append(make_do_land_start(seq, mav))
        seq += 1

    # Landing approach waypoint
    items.append(make_nav_waypoint(seq, approach_lat, approach_lon, approach_alt, mav))
    seq += 1

    # NAV_LAND at touchdown
    items.append(make_nav_land(seq, touchdown_lat, touchdown_lon, touchdown_alt, mav))

    logger.info(
        "Landing sequence generated",
        approach_alt=approach_alt,
        touchdown_alt=touchdown_alt,
        use_do_land_start=geometry.use_do_land_start,
        items=len(items),
    )
    return items
