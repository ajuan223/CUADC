"""Landing sequence generation for fixed-wing aircraft."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from striker.flight.navigation import make_do_land_start, make_nav_land, make_nav_waypoint

if TYPE_CHECKING:
    from striker.config.field_profile import FieldProfile

logger = structlog.get_logger(__name__)


def generate_landing_sequence(field_profile: FieldProfile, mav: Any) -> list[Any]:
    """Generate a fixed-wing landing sequence from field profile.

    Sequence: DO_LAND_START → approach waypoint → NAV_LAND

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
    seq = 0

    # Validate landing parameters
    if approach.alt_m <= touchdown.alt_m:
        logger.warning(
            "Approach altitude should be higher than touchdown",
            approach_alt=approach.alt_m,
            touchdown_alt=touchdown.alt_m,
        )

    # DO_LAND_START marker
    items.append(make_do_land_start(seq, mav))
    seq += 1

    # Approach waypoint
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
