## ADDED Requirements

### Requirement: Procedural mission geometry derives landing approach from runway facts
The system SHALL derive the fixed-wing landing approach waypoint from field configuration facts instead of consuming a user-authored approach coordinate. The derived approach geometry SHALL use `touchdown_point`, `heading_deg`, `approach_alt_m`, and `glide_slope_deg` as the authoritative inputs.

**Algorithm — Glide Slope Reverse Projection:**

Given:
- `touchdown`: (lat, lon, alt_m) — the touchdown point on the runway
- `heading_deg`: runway landing direction (degrees, 0=N, 90=E, etc.)
- `approach_alt_m`: desired approach gate altitude (AGL)
- `glide_slope_deg`: glide slope angle (typically 2.5°–5°, standard 3°)

Steps:
1. Compute altitude delta: `delta_alt = approach_alt_m - touchdown.alt_m`
2. Validate: `delta_alt > 0`, else reject (non-descending)
3. Compute horizontal distance: `distance = delta_alt / tan(radians(glide_slope_deg))`
4. Validate: `distance >= MIN_APPROACH_DISTANCE` (default 200m for fixed-wing stability)
5. Compute reverse heading: `approach_heading = (heading_deg + 180) % 360`
6. Compute approach point: `approach = destination_point(touchdown.lat, touchdown.lon, approach_heading, distance)`
7. Validate approach point is inside geofence; reject if outside

```python
import math
from striker.utils.geo import destination_point, point_in_polygon

MIN_APPROACH_DISTANCE_M = 200.0

def derive_landing_approach(
    touchdown_lat: float, touchdown_lon: float, touchdown_alt_m: float,
    heading_deg: float, approach_alt_m: float, glide_slope_deg: float,
    geofence_polygon: list,
) -> tuple[float, float, float]:
    """Derive landing approach waypoint from touchdown + glide slope.

    Returns (lat, lon, alt_m) of the approach gate.
    Raises ValueError if geometry is invalid.
    """
    delta_alt = approach_alt_m - touchdown_alt_m
    if delta_alt <= 0:
        raise ValueError(
            f"Approach alt ({approach_alt_m}) must be above touchdown alt ({touchdown_alt_m})"
        )

    distance = delta_alt / math.tan(math.radians(glide_slope_deg))
    if distance < MIN_APPROACH_DISTANCE_M:
        raise ValueError(
            f"Derived approach distance ({distance:.1f}m) below minimum ({MIN_APPROACH_DISTANCE_M}m)"
        )

    reverse_heading = (heading_deg + 180.0) % 360.0
    approach_lat, approach_lon = destination_point(
        touchdown_lat, touchdown_lon, reverse_heading, distance
    )

    if not point_in_polygon(approach_lat, approach_lon, geofence_polygon):
        raise ValueError(
            f"Derived approach ({approach_lat:.6f}, {approach_lon:.6f}) is outside geofence"
        )

    return approach_lat, approach_lon, approach_alt_m
```

**Reference:** Standard ILS glide slope geometry. For a 3° glide slope and 30m altitude delta, the horizontal distance is `30 / tan(3°) ≈ 572.9m`.

#### Scenario: Derive approach waypoint from touchdown and glide slope
- **WHEN** the field profile provides touchdown point, heading 180°, touchdown altitude 0m, approach altitude 30m, and glide slope 3°
- **THEN** the system SHALL compute the landing approach waypoint at approximately 572m opposite the runway heading (i.e. heading 0°) from the touchdown point
- **AND** the computed waypoint altitude SHALL be 30m

#### Scenario: Approach geometry uses touchdown-relative altitude delta
- **WHEN** the touchdown altitude is non-zero (e.g. 5m above home)
- **THEN** the system SHALL compute horizontal approach distance from `(approach_alt_m - touchdown_alt_m) / tan(glide_slope_deg)`
- **AND** it SHALL NOT assume touchdown altitude is always zero

#### Scenario: Reject approach too close to touchdown
- **WHEN** the computed approach distance is less than `MIN_APPROACH_DISTANCE_M` (200m)
- **THEN** the system SHALL reject with a minimum distance validation error

### Requirement: Procedural mission geometry validates derived landing sequence
The system SHALL validate the computed landing geometry before mission generation. Invalid geometry MUST be rejected explicitly instead of silently using a bad approach point.

#### Scenario: Reject non-descending approach geometry
- **WHEN** `approach_alt_m` is less than or equal to touchdown altitude
- **THEN** the system SHALL reject landing geometry generation with an explicit validation error

#### Scenario: Reject out-of-bounds derived approach point
- **WHEN** the computed approach waypoint falls outside the field geofence
- **THEN** the system SHALL reject landing geometry generation with an explicit validation error that identifies the landing approach geometry as invalid

### Requirement: Procedural mission geometry generates scan path using Boustrophedon algorithm
The system SHALL generate scan mission waypoints using a deterministic Boustrophedon (lawnmower) coverage path planning algorithm from field boundary and scan constraint inputs, rather than requiring the field file to enumerate scan waypoints directly.

**Algorithm — Boustrophedon Coverage Path Planning (Coombes 2017/2018):**

Given:
- `boundary_polygon`: closed list of (lat, lon) vertices defining the ROI
- `scan_alt_m`: flight altitude for scan
- `scan_spacing_m`: distance between adjacent sweep lines (determines overlap)
- `scan_heading_deg`: direction of sweep lines (perpendicular to flight direction)
- `scan_speed_mps`: target groundspeed during scan (informational, affects turn strategy)

Steps:
1. **Rotate polygon** so sweep direction is horizontal (simplify intersection math).
2. **Generate parallel sweep lines** perpendicular to `scan_heading_deg`, spaced at `scan_spacing_m`, covering the full vertical extent of the rotated polygon.
3. **Clip each sweep line** against the polygon edges to get (entry, exit) intersection pairs.
4. **Build waypoint pairs**: for each sweep line that intersects the polygon, record the two intersection points.
5. **Connect sweeps in Boustrophedon order**: odd sweeps go entry→exit, even sweeps go exit→entry, minimizing turn distance.
6. **Rotate all waypoints back** to original geographic coordinates.

```python
import math
from typing import Sequence
from striker.utils.geo import destination_point, calculate_bearing, haversine_distance

def _rotate_point(lat: float, lon: float, center_lat: float, center_lon: float,
                  angle_rad: float) -> tuple[float, float]:
    """Rotate a geographic point around center by angle_rad (in local meter space)."""
    # Convert to local meters
    x = (lon - center_lon) * 111320.0 * math.cos(math.radians(center_lat))
    y = (lat - center_lat) * 110540.0  # approx meters per degree latitude
    # Rotate
    xr = x * math.cos(angle_rad) - y * math.sin(angle_rad)
    yr = x * math.sin(angle_rad) + y * math.cos(angle_rad)
    # Convert back
    rot_lon = center_lon + xr / (111320.0 * math.cos(math.radians(center_lat)))
    rot_lat = center_lat + yr / 110540.0
    return rot_lat, rot_lon

def _line_polygon_intersections(
    line_y: float, polygon: list[tuple[float, float]]
) -> list[float]:
    """Find x-intersections of a horizontal line y=line_y with polygon edges."""
    xs = []
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 <= line_y < y2) or (y2 <= line_y < y1):
            t = (line_y - y1) / (y2 - y1) if y2 != y1 else 0
            xs.append(x1 + t * (x2 - x1))
    xs.sort()
    return xs

def generate_boustrophedon_scan(
    boundary_polygon: list[tuple[float, float]],
    scan_alt_m: float,
    scan_spacing_m: float,
    scan_heading_deg: float,
) -> list[tuple[float, float, float]]:
    """Generate Boustrophedon scan waypoints over a polygon.

    Args:
        boundary_polygon: Closed list of (lat, lon) vertices.
        scan_alt_m: Flight altitude (added to each waypoint).
        scan_spacing_m: Spacing between sweep lines in meters.
        scan_heading_deg: Heading of sweep lines (flight goes perpendicular).

    Returns:
        List of (lat, lon, alt_m) waypoints in flyable order.
    """
    if len(boundary_polygon) < 3:
        raise ValueError("Polygon must have at least 3 vertices")

    # Compute centroid for rotation reference
    clat = sum(p[0] for p in boundary_polygon) / len(boundary_polygon)
    clon = sum(p[1] for p in boundary_polygon) / len(boundary_polygon)

    # Rotate polygon so scan_heading becomes "vertical" (sweeps go horizontal)
    rot_angle = -math.radians(scan_heading_deg - 90.0)  # sweep perpendicular to heading
    rot_poly = []
    for lat, lon in boundary_polygon:
        # Convert to local meters then rotate
        x = (lon - clon) * 111320.0 * math.cos(math.radians(clat))
        y = (lat - clat) * 110540.0
        xr = x * math.cos(rot_angle) - y * math.sin(rot_angle)
        yr = x * math.sin(rot_angle) + y * math.cos(rot_angle)
        rot_poly.append((xr, yr))

    # Find vertical extent of rotated polygon
    ys = [p[1] for p in rot_poly]
    y_min, y_max = min(ys), max(ys)

    # Generate sweep lines
    waypoints: list[tuple[float, float, float]] = []
    sweep_idx = 0
    y = y_min + scan_spacing_m / 2  # offset half-spacing from edge

    while y <= y_max - scan_spacing_m / 4:
        intersections = _line_polygon_intersections(y, rot_poly)
        # Pair up intersections (entry, exit)
        for i in range(0, len(intersections) - 1, 2):
            entry_x = intersections[i]
            exit_x = intersections[i + 1]
            # Alternate direction for Boustrophedon
            if sweep_idx % 2 == 1:
                entry_x, exit_x = exit_x, entry_x
            for wx in [entry_x, exit_x]:
                # Inverse rotate back to geographic
                ix = wx * math.cos(-rot_angle) - y * math.sin(-rot_angle)
                iy = wx * math.sin(-rot_angle) + y * math.cos(-rot_angle)
                lat = clat + iy / 110540.0
                lon = clon + ix / (111320.0 * math.cos(math.radians(clat)))
                waypoints.append((lat, lon, scan_alt_m))
        sweep_idx += 1
        y += scan_spacing_m

    return waypoints
```

**References:**
- Coombes et al., "Boustrophedon Coverage Path Planning for UAV Aerial Surveys in Wind" (ICUAS 2017)
- Coombes et al., "Optimal Polygon Decomposition for UAV Survey Coverage Path Planning in Wind" (Sensors 2018, DOI: 10.3390/s18072132)
- Baehnemann et al., "Revisiting Boustrophedon Coverage Path Planning as a Standard Framework" (2019)

**Future iteration opportunities:**
- Wind-aware sweep angle optimization (flying perpendicular to wind reduces flight time up to 25%)
- Concave polygon decomposition into convex sub-polygons (87% of real fields are non-convex)
- Minimum-turn-radius-aware turn point insertion between sweeps

#### Scenario: Generate deterministic lawnmower scan path
- **WHEN** the field profile provides a valid boundary polygon (1km x 1km), scan altitude 80m, scan spacing 100m, and scan heading 0° (north-south sweeps)
- **THEN** the system SHALL generate approximately 10 sweep lines with ~20 waypoints in Boustrophedon order
- **AND** the generated path SHALL be suitable for direct mission upload without additional hand-authored scan waypoints

#### Scenario: Scan path covers the entire polygon
- **WHEN** the Boustrophedon algorithm is applied to a convex polygon
- **THEN** every point inside the polygon SHALL be within `scan_spacing_m` of at least one sweep line

#### Scenario: Reject invalid polygon for scan generation
- **WHEN** the boundary polygon has fewer than 3 vertices
- **THEN** the system SHALL raise a validation error

### Requirement: Procedural mission geometry generates takeoff path from runway facts
The system SHALL generate fixed-wing takeoff mission geometry from runway/location facts instead of requiring users to pre-author takeoff mission points.

**Algorithm — Runway-Aligned Takeoff Geometry:**

Given:
- `touchdown`: (lat, lon, alt_m) — the runway touchdown point (shared with landing)
- `heading_deg`: runway takeoff direction (opposite of landing heading for bidirectional, or same for unidirectional)
- `runway_length_m`: runway length in meters
- `takeoff_alt_m`: target climb altitude (typically scan altitude)

Steps:
1. Compute runway midpoint: `midpoint = destination_point(touchdown, heading_deg, runway_length_m / 2)`
2. Compute takeoff start point: `start = destination_point(midpoint, reverse(heading_deg), runway_length_m * 0.4)`
   - Start at ~40% behind midpoint to ensure full takeoff roll within runway
3. Compute climb-out waypoint: `climbout = destination_point(touchdown, heading_deg, runway_length_m)`
   - Beyond the far end of the runway, at `takeoff_alt_m`
4. The takeoff mission sequence: `NAV_TAKEOFF(start → takeoff_alt_m)` followed by `NAV_WAYPOINT(climbout → takeoff_alt_m)`
   - ArduPlane handles the actual pitch/throttle schedule via `TKOFF_*` parameters

```python
def generate_takeoff_geometry(
    touchdown_lat: float, touchdown_lon: float, touchdown_alt_m: float,
    heading_deg: float, runway_length_m: float, takeoff_alt_m: float,
) -> dict:
    """Generate fixed-wing takeoff geometry from runway facts.

    Returns dict with keys:
        start_lat, start_lon: takeoff roll start position
        start_alt_m: takeoff start altitude (= touchdown altitude)
        climbout_lat, climbout_lon: climb-out waypoint
        climbout_alt_m: target altitude after takeoff
        heading_deg: takeoff direction
    """
    if runway_length_m <= 0:
        raise ValueError(f"Runway length must be positive, got {runway_length_m}")
    if takeoff_alt_m <= touchdown_alt_m:
        raise ValueError(
            f"Takeoff alt ({takeoff_alt_m}) must be above runway alt ({touchdown_alt_m})"
        )

    reverse_heading = (heading_deg + 180.0) % 360.0

    # Start point: 40% behind the midpoint along the runway
    mid_lat, mid_lon = destination_point(
        touchdown_lat, touchdown_lon, heading_deg, runway_length_m / 2
    )
    start_lat, start_lon = destination_point(
        mid_lat, mid_lon, reverse_heading, runway_length_m * 0.4
    )

    # Climb-out point: beyond far end of runway
    climbout_lat, climbout_lon = destination_point(
        touchdown_lat, touchdown_lon, heading_deg, runway_length_m
    )

    return {
        "start_lat": start_lat,
        "start_lon": start_lon,
        "start_alt_m": touchdown_alt_m,
        "climbout_lat": climbout_lat,
        "climbout_lon": climbout_lon,
        "climbout_alt_m": takeoff_alt_m,
        "heading_deg": heading_deg,
    }
```

#### Scenario: Takeoff follows runway axis
- **WHEN** the field profile provides touchdown at (30.261, 120.095), heading 180°, runway length 200m, takeoff alt 80m
- **THEN** the system SHALL compute a takeoff start point approximately 80m behind the runway midpoint along heading 0°
- **AND** the climb-out waypoint SHALL be 200m beyond the touchdown along heading 180° at 80m altitude

#### Scenario: Reject zero or negative runway length
- **WHEN** `runway_length_m` is 0 or negative
- **THEN** the system SHALL raise a validation error

#### Scenario: Reject takeoff altitude below runway
- **WHEN** `takeoff_alt_m` is less than or equal to the runway altitude
- **THEN** the system SHALL raise a validation error

### Requirement: Unified mission geometry result object
The procedural mission geometry module SHALL produce a unified result object that bundles all generated mission items and key sequence indices for consumption by the mission upload pipeline.

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class MissionGeometryResult:
    """Output of procedural mission geometry generation."""

    # Raw waypoint data (lat, lon, alt_m tuples)
    takeoff_start: tuple[float, float, float]
    takeoff_climbout: tuple[float, float, float]
    scan_waypoints: list[tuple[float, float, float]]
    landing_approach: tuple[float, float, float]
    landing_touchdown: tuple[float, float, float]

    # DO_LAND_START usage flag
    use_do_land_start: bool

    # Key sequence indices (populated during mission assembly)
    takeoff_start_seq: int = 0
    scan_start_seq: int = 0
    scan_end_seq: int = 0
    landing_start_seq: int = 0

    def compute_indices(self, include_dummy_home: bool = True) -> None:
        """Compute sequence indices based on mission item count."""
        seq = 1 if include_dummy_home else 0  # seq 0 = dummy HOME
        self.takeoff_start_seq = seq
        seq += 2  # takeoff + climbout
        self.scan_start_seq = seq
        seq += len(self.scan_waypoints)
        self.scan_end_seq = seq - 1
        self.landing_start_seq = seq
```

#### Scenario: MissionGeometryResult computes correct indices
- **WHEN** a result has 8 scan waypoints and `include_dummy_home=True`
- **THEN** `takeoff_start_seq` SHALL be 1
- **AND** `scan_start_seq` SHALL be 3
- **AND** `scan_end_seq` SHALL be 10
- **AND** `landing_start_seq` SHALL be 11
