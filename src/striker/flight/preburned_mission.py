"""Preburned mission structures and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from striker.comms.messages import (
    MAV_CMD_DO_LAND_START,
    MAV_CMD_NAV_LAND,
    MAV_CMD_NAV_LOITER_UNLIM,
)
from striker.exceptions import ConfigError

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PreburnedMissionInfo:
    """Critical sequence numbers parsed from a preburned mission."""

    loiter_seq: int
    slot_start_seq: int
    slot_end_seq: int
    landing_start_seq: int
    total_count: int


def parse_preburned_mission(items: list[Any]) -> PreburnedMissionInfo:
    """Parse critical sequence numbers from a downloaded mission.

    Raises
    ------
    ConfigError
        If the mission structure is invalid (missing LOITER_UNLIM,
        insufficient slots, or missing landing sequence).
    """
    total_count = len(items)
    loiter_seq = -1
    landing_start_seq = -1

    for item in items:
        if item.command == MAV_CMD_NAV_LOITER_UNLIM:
            loiter_seq = item.seq
        elif (
            item.command in (MAV_CMD_DO_LAND_START, MAV_CMD_NAV_LAND)
            and landing_start_seq == -1
        ):
            landing_start_seq = item.seq

    if loiter_seq == -1:
        raise ConfigError("Preburned mission must contain a NAV_LOITER_UNLIM hold point.")

    if landing_start_seq == -1:
        raise ConfigError("Preburned mission must contain a DO_LAND_START or NAV_LAND sequence.")

    slot_start_seq = loiter_seq + 1
    # We require 5 reserved slots between loiter and landing
    expected_slots = 5
    slot_end_seq = slot_start_seq + expected_slots - 1

    if slot_end_seq >= landing_start_seq:
        raise ConfigError(
            f"Preburned mission has insufficient reserved slots. "
            f"Expected {expected_slots} slots between loiter_seq={loiter_seq} "
            f"and landing_start_seq={landing_start_seq}."
        )

    return PreburnedMissionInfo(
        loiter_seq=loiter_seq,
        slot_start_seq=slot_start_seq,
        slot_end_seq=slot_end_seq,
        landing_start_seq=landing_start_seq,
        total_count=total_count,
    )
