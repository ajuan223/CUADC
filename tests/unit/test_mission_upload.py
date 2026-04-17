"""Unit tests for mission upload behavior."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from striker.comms.messages import MAV_CMD_DO_LAND_START, MAV_CMD_NAV_WAYPOINT
from striker.exceptions import CommsError
from striker.flight.landing_sequence import (
    LANDING_APPROACH_ACCEPTANCE_RADIUS_M,
    generate_landing_sequence,
)
from striker.flight.mission_upload import upload_attack_mission, upload_landing_mission, upload_mission
from striker.flight.navigation import (
    build_attack_run_mission,
    build_landing_only_mission,
    make_nav_waypoint,
)
from striker.utils.geo import calculate_bearing, destination_point, haversine_distance


class TestMissionUpload:
    @pytest.mark.asyncio
    async def test_upload_blocked_after_autonomy_relinquished(self) -> None:
        conn = MagicMock()
        conn.ensure_autonomy_allowed.side_effect = CommsError("Autonomy relinquished")

        with pytest.raises(CommsError, match="Autonomy relinquished"):
            await upload_mission(conn, items=[])

    @pytest.mark.asyncio
    async def test_upload_attack_mission_uses_explicit_attack_altitude(self) -> None:
        conn = MagicMock()
        conn.mav = MagicMock()
        field_profile = MagicMock()
        field_profile.attack_run.release_acceptance_radius_m = 0.0
        geometry = MagicMock()
        context = MagicMock()
        landing_items = [SimpleNamespace(seq=0)]
        built_items = [SimpleNamespace(seq=0)]

        with patch(
            "striker.flight.landing_sequence.generate_landing_sequence",
            return_value=landing_items,
        ) as generate_landing, patch(
            "striker.flight.navigation.build_attack_run_mission",
            return_value=(built_items, 2, 5),
        ) as build_attack, patch(
            "striker.flight.mission_upload.upload_mission",
            new=AsyncMock(),
        ) as upload:
            target_seq, landing_start_seq = await upload_attack_mission(
                conn=conn,
                field_profile=field_profile,
                geometry=geometry,
                context=context,
                target_lat=30.26,
                target_lon=120.09,
                approach_lat=30.27,
                approach_lon=120.08,
                exit_lat=30.25,
                exit_lon=120.10,
                attack_alt_m=21.4,
                dry_run=False,
                release_channel=6,
                release_pwm=2000,
            )

        generate_landing.assert_called_once_with(geometry, conn.mav, start_seq=0)
        build_attack.assert_called_once()
        assert build_attack.call_args.kwargs["attack_alt_m"] == pytest.approx(21.4)
        upload.assert_awaited_once_with(conn, built_items)
        assert context.landing_sequence_start_index == 5
        assert (target_seq, landing_start_seq) == (2, 5)
    @pytest.mark.asyncio
    async def test_upload_landing_mission_sets_new_landing_start_index(self) -> None:
        conn = MagicMock()
        conn.mav = MagicMock()
        geometry = MagicMock()
        context = MagicMock()
        landing_items = [SimpleNamespace(seq=0), SimpleNamespace(seq=1)]
        built_items = [SimpleNamespace(seq=0), SimpleNamespace(seq=1), SimpleNamespace(seq=2)]

        with patch(
            "striker.flight.landing_sequence.generate_landing_sequence",
            return_value=landing_items,
        ) as generate_landing, patch(
            "striker.flight.navigation.build_landing_only_mission",
            return_value=(built_items, 1),
        ) as build_landing, patch(
            "striker.flight.mission_upload.upload_mission",
            new=AsyncMock(),
        ) as upload:
            landing_start_seq = await upload_landing_mission(
                conn=conn,
                geometry=geometry,
                context=context,
            )

        generate_landing.assert_called_once_with(geometry, conn.mav, start_seq=0)
        build_landing.assert_called_once_with(
            geometry=geometry,
            boundary_polygon=context.field_profile.boundary.polygon,
            landing_items=landing_items,
            mav=conn.mav,
        )
        upload.assert_awaited_once_with(conn, built_items)
        assert context.landing_sequence_start_index == 1
        assert landing_start_seq == 1


class TestLandingSequence:
    def test_landing_approach_waypoint_uses_tight_acceptance_radius(self) -> None:
        mission_items: list[SimpleNamespace] = []

        def _encode(**kwargs):
            item = SimpleNamespace(**kwargs)
            mission_items.append(item)
            return item

        mav = SimpleNamespace(
            target_system=1,
            target_component=1,
            mav=SimpleNamespace(mission_item_int_encode=_encode),
        )
        geometry = SimpleNamespace(
            landing_approach=(30.30041700564638, 120.0720231438355, 21.4),
            landing_touchdown=(30.302079, 120.071133, 0.0),
            use_do_land_start=True,
        )

        items = generate_landing_sequence(geometry, mav, start_seq=0)

        assert len(items) == 3
        assert items[1].param2 == pytest.approx(LANDING_APPROACH_ACCEPTANCE_RADIUS_M)


    def test_build_landing_only_mission_restores_do_land_start_with_final_approach_gate(self) -> None:
        mission_items: list[SimpleNamespace] = []

        def _encode(**kwargs):
            item = SimpleNamespace(**kwargs)
            mission_items.append(item)
            return item

        mav = SimpleNamespace(
            target_system=1,
            target_component=1,
            mav=SimpleNamespace(mission_item_int_encode=_encode),
        )
        geometry = SimpleNamespace(
            landing_approach=(30.30041700564638, 120.0720231438355, 21.4),
            landing_touchdown=(30.302079, 120.071133, 0.0),
        )
        boundary_polygon = [
            SimpleNamespace(lat=30.300517, lon=120.072559),
            SimpleNamespace(lat=30.300291, lon=120.071395),
            SimpleNamespace(lat=30.302323, lon=120.070128),
            SimpleNamespace(lat=30.30275, lon=120.071421),
            SimpleNamespace(lat=30.300517, lon=120.072559),
        ]
        landing_items = [
            SimpleNamespace(seq=0, command=MAV_CMD_DO_LAND_START),
            SimpleNamespace(seq=1, command=MAV_CMD_NAV_WAYPOINT),
            SimpleNamespace(seq=2, command=21),
        ]

        items, landing_start_seq = build_landing_only_mission(
            geometry=geometry,
            boundary_polygon=boundary_polygon,
            landing_items=landing_items,
            mav=mav,
        )

        assert landing_start_seq == 3
        assert len(items) == 5
        assert items[1].command == MAV_CMD_DO_LAND_START
        assert items[2].command == MAV_CMD_NAV_WAYPOINT
        assert items[3].command == MAV_CMD_NAV_WAYPOINT
        assert items[4].command == 21
        assert items[3].z < geometry.landing_approach[2]
        assert items[3].z > 0.0

    def test_build_landing_only_mission_starts_landing_after_home_when_no_pre_approach_gate(self) -> None:
        mission_items: list[SimpleNamespace] = []

        def _encode(**kwargs):
            item = SimpleNamespace(**kwargs)
            mission_items.append(item)
            return item

        mav = SimpleNamespace(
            target_system=1,
            target_component=1,
            mav=SimpleNamespace(mission_item_int_encode=_encode),
        )
        geometry = SimpleNamespace(
            landing_approach=(30.30041700564638, 120.0720231438355, 21.4),
            landing_touchdown=(30.302079, 120.071133, 0.0),
        )
        boundary_polygon = [
            SimpleNamespace(lat=30.300430, lon=120.072050),
            SimpleNamespace(lat=30.300400, lon=120.072000),
            SimpleNamespace(lat=30.300450, lon=120.071950),
            SimpleNamespace(lat=30.300430, lon=120.072050),
        ]
        landing_items = [
            make_nav_waypoint(0, 30.30041700564638, 120.0720231438355, 21.4, mav),
            make_nav_waypoint(1, 30.302079, 120.071133, 0.0, mav),
        ]

        items, landing_start_seq = build_landing_only_mission(
            geometry=geometry,
            boundary_polygon=boundary_polygon,
            landing_items=landing_items,
            mav=mav,
        )

        assert landing_start_seq == 1
        assert len(items) == 3
        assert items[1].seq == 1
        assert items[2].seq == 2

    def test_target_waypoint_uses_acceptance_radius(self) -> None:
        mission_items: list[SimpleNamespace] = []

        def _encode(**kwargs):
            item = SimpleNamespace(**kwargs)
            mission_items.append(item)
            return item

        mav = SimpleNamespace(
            target_system=1,
            target_component=1,
            mav=SimpleNamespace(mission_item_int_encode=_encode),
        )
        landing_item = SimpleNamespace(seq=0)

        items, target_seq, landing_start_seq = build_attack_run_mission(
            approach_lat=30.263201,
            approach_lon=120.095,
            target_lat=30.260502367023822,
            target_lon=120.09718108499997,
            exit_lat=30.262209,
            exit_lon=120.096522,
            attack_alt_m=80.0,
            release_channel=6,
            release_pwm=2000,
            acceptance_radius_m=220.0,
            dry_run=False,
            landing_items=[landing_item],
            mav=mav,
        )

        assert target_seq == 2
        assert landing_start_seq == 5
        assert items[target_seq].param2 == pytest.approx(220.0)

    def test_attack_and_exit_legs_use_configured_attack_altitude(self) -> None:
        mission_items: list[SimpleNamespace] = []

        def _encode(**kwargs):
            item = SimpleNamespace(**kwargs)
            mission_items.append(item)
            return item

        mav = SimpleNamespace(
            target_system=1,
            target_component=1,
            mav=SimpleNamespace(mission_item_int_encode=_encode),
        )
        landing_item = SimpleNamespace(seq=0, z=21.4)

        items, target_seq, landing_start_seq = build_attack_run_mission(
            approach_lat=30.263201,
            approach_lon=120.095,
            target_lat=30.260502367023822,
            target_lon=120.09718108499997,
            exit_lat=30.262209,
            exit_lon=120.096522,
            attack_alt_m=21.4,
            release_channel=6,
            release_pwm=2000,
            acceptance_radius_m=0.0,
            dry_run=False,
            landing_items=[landing_item],
            mav=mav,
        )

        assert items[1].z == pytest.approx(21.4)
        assert items[target_seq].z == pytest.approx(21.4)
        assert items[4].z == pytest.approx(21.4)
        assert landing_start_seq == 5

    def test_near_approach_target_can_still_build_distinct_legs(self) -> None:
        landing_heading_deg = 155.18309494177925
        target_lat = 30.30041700564638
        target_lon = 120.0720231438355
        approach_heading = (landing_heading_deg + 180.0) % 360.0
        approach_lat, approach_lon = destination_point(
            target_lat,
            target_lon,
            (approach_heading + 180.0) % 360.0,
            100.0,
        )
        exit_lat, exit_lon = destination_point(
            target_lat,
            target_lon,
            approach_heading,
            100.0,
        )

        assert calculate_bearing(approach_lat, approach_lon, target_lat, target_lon) == pytest.approx(
            approach_heading,
            abs=0.1,
        )
        assert calculate_bearing(target_lat, target_lon, exit_lat, exit_lon) == pytest.approx(
            approach_heading,
            abs=0.1,
        )

    def test_build_attack_run_mission_keeps_landing_items_after_exit_waypoint(self) -> None:
        mission_items: list[SimpleNamespace] = []

        def _encode(**kwargs):
            item = SimpleNamespace(**kwargs)
            mission_items.append(item)
            return item

        mav = SimpleNamespace(
            target_system=1,
            target_component=1,
            mav=SimpleNamespace(mission_item_int_encode=_encode),
        )
        landing_items = [
            make_nav_waypoint(0, 30.30041700564638, 120.0720231438355, 21.4, mav),
            make_nav_waypoint(1, 30.302079, 120.071133, 0.0, mav),
        ]

        items, _, landing_start_seq = build_attack_run_mission(
            approach_lat=30.302735,
            approach_lon=120.071277,
            target_lat=30.30186889085492,
            target_lon=120.07155599218392,
            exit_lat=30.30186889085492,
            exit_lon=120.07155599218392,
            attack_alt_m=26.4,
            release_channel=6,
            release_pwm=2000,
            acceptance_radius_m=0.0,
            dry_run=False,
            landing_items=landing_items,
            mav=mav,
        )

        assert landing_start_seq == 5
        handoff_leg_m = haversine_distance(
            items[4].x / 1e7,
            items[4].y / 1e7,
            items[5].x / 1e7,
            items[5].y / 1e7,
        )
        assert handoff_leg_m == pytest.approx(167.6, abs=1.0)
