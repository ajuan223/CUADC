"""Landing sequence generation for fixed-wing aircraft."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from striker.flight.navigation import make_do_land_start, make_nav_land, make_nav_waypoint

if TYPE_CHECKING:
    from striker.config.field_profile import FieldProfile

logger = structlog.get_logger(__name__)


def generate_landing_sequence(
    field_profile: FieldProfile,
    mav: Any,
    start_seq: int = 0,
) -> list[Any]:
    """Generate a fixed-wing landing sequence from field profile.

    Sequence: NAV_WAYPOINT (approach) → NAV_LAND (touchdown)

    Note: We use NAV_WAYPOINT instead of DO_LAND_START because ArduPlane
    SITL rejects DO_LAND_START (cmd 189) when re-uploading a mission while
    armed in AUTO mode. Since we use MISSION_SET_CURRENT to jump to the
    landing start index, a plain waypoint works just as well.

    Parameters
    ----------
    field_profile:
        Field configuration with landing parameters.
    mav:
        pymavlink connection object.

    Returns
    -------
    list of MAVLink mission items.
    """
    landing = field_profile.landing
    approach = landing.approach_waypoint
    touchdown = landing.touchdown_point

    items: list[Any] = []
    seq = start_seq

    # Validate landing parameters
    if approach.alt_m <= touchdown.alt_m:
        logger.warning(
            "Approach altitude should be higher than touchdown",
            approach_alt=approach.alt_m,
            touchdown_alt=touchdown.alt_m,
        )

    # Landing approach waypoint (replaces DO_LAND_START)
    items.append(make_nav_waypoint(seq, approach.lat, approach.lon, approach.alt_m, mav))
    seq += 1

    # NAV_LAND at touchdown
    items.append(make_nav_land(seq, touchdown.lat, touchdown.lon, touchdown.alt_m, mav))

    logger.info(
        "Landing sequence generated",
        approach_alt=approach.alt_m,
        touchdown_alt=touchdown.alt_m,
        items=len(items),
    )
    return items
