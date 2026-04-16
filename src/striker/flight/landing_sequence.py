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

    When ``use_do_land_start`` is ``True`` (default, real deployment):
        DO_LAND_START → approach (NAV_WAYPOINT) → NAV_LAND (3 items)

    When ``use_do_land_start`` is ``False`` (SITL fallback):
        approach (NAV_WAYPOINT) → NAV_LAND (2 items)

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

    # DO_LAND_START (real deployment only)
    if landing.use_do_land_start:
        items.append(make_do_land_start(seq, mav))
        seq += 1

    # Landing approach waypoint
    items.append(make_nav_waypoint(seq, approach.lat, approach.lon, approach.alt_m, mav))
    seq += 1

    # NAV_LAND at touchdown
    items.append(make_nav_land(seq, touchdown.lat, touchdown.lon, touchdown.alt_m, mav))

    logger.info(
        "Landing sequence generated",
        approach_alt=approach.alt_m,
        touchdown_alt=touchdown.alt_m,
        use_do_land_start=landing.use_do_land_start,
        items=len(items),
    )
    return items
