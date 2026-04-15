"""Unit tests for point-in-polygon algorithm."""

from __future__ import annotations

import pytest

from striker.utils.point_in_polygon import point_in_polygon


_SQUARE = [(0, 0), (0, 1), (1, 1), (1, 0)]
_TRIANGLE = [(0, 0), (1, 0), (0.5, 1)]
_CONCAVE = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (2, 2), (2, 3), (0, 3)]


class TestPointInPolygon:
    def test_inside_square(self) -> None:
        assert point_in_polygon(0.5, 0.5, _SQUARE) is True

    def test_outside_square(self) -> None:
        assert point_in_polygon(1.5, 1.5, _SQUARE) is False

    def test_on_edge(self) -> None:
        assert point_in_polygon(0.5, 0, _SQUARE) is True

    def test_inside_triangle(self) -> None:
        assert point_in_polygon(0.4, 0.3, _TRIANGLE) is True

    def test_outside_triangle(self) -> None:
        assert point_in_polygon(0.8, 0.8, _TRIANGLE) is False

    def test_concave_inside(self) -> None:
        assert point_in_polygon(0.5, 0.5, _CONCAVE) is True

    def test_concave_outside(self) -> None:
        # In the concavity — should be outside
        assert point_in_polygon(1.5, 1.5, _CONCAVE) is False

    def test_less_than_3_vertices(self) -> None:
        assert point_in_polygon(0.5, 0.5, [(0, 0), (1, 1)]) is False
