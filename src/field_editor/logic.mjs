const DEFAULT_CENTER = Object.freeze({ lat: 30.27, lon: 120.095 });
const DEFAULT_ZOOM = 15;
const MIN_SCAN_SPACING_M = 40.0;
const MAX_SCAN_SPACING_M = 400.0;
const MAX_SAFE_GLIDE_SLOPE_DEG = 6.0;
const MAX_SAFE_CLIMB_ANGLE_DEG = 12.0;
const EARTH_RADIUS_M = 6_371_000;
const PI = Math.PI;
const A = 6378245.0;
const EE = 0.00669342162296594323;

function clone(value) {
  return structuredClone(value);
}

function transformLat(x, y) {
  let ret =
    -100.0 +
    2.0 * x +
    3.0 * y +
    0.2 * y * y +
    0.1 * x * y +
    0.2 * Math.sqrt(Math.abs(x));
  ret +=
    ((20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0) /
    3.0;
  ret +=
    ((20.0 * Math.sin(y * PI) + 40.0 * Math.sin((y / 3.0) * PI)) * 2.0) /
    3.0;
  ret +=
    ((160.0 * Math.sin((y / 12.0) * PI) + 320.0 * Math.sin((y * PI) / 30.0)) * 2.0) /
    3.0;
  return ret;
}

function transformLon(x, y) {
  let ret =
    300.0 +
    x +
    2.0 * y +
    0.1 * x * x +
    0.1 * x * y +
    0.1 * Math.sqrt(Math.abs(x));
  ret +=
    ((20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0) /
    3.0;
  ret +=
    ((20.0 * Math.sin(x * PI) + 40.0 * Math.sin((x / 3.0) * PI)) * 2.0) /
    3.0;
  ret +=
    ((150.0 * Math.sin((x / 12.0) * PI) + 300.0 * Math.sin((x / 30.0) * PI)) * 2.0) /
    3.0;
  return ret;
}

function outOfChina(lat, lon) {
  return lon < 72.004 || lon > 137.8347 || lat < 0.8293 || lat > 55.8271;
}

function delta(lat, lon) {
  const dLat = transformLat(lon - 105.0, lat - 35.0);
  const dLon = transformLon(lon - 105.0, lat - 35.0);
  const radLat = (lat / 180.0) * PI;
  let magic = Math.sin(radLat);
  magic = 1 - EE * magic * magic;
  const sqrtMagic = Math.sqrt(magic);
  return {
    lat:
      (dLat * 180.0) /
      (((A * (1 - EE)) / (magic * sqrtMagic)) * PI),
    lon: (dLon * 180.0) / ((A / sqrtMagic) * Math.cos(radLat) * PI),
  };
}

function normalizeNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function getByPath(target, path) {
  return path.split(".").reduce((current, key) => current?.[key], target);
}

function setByPath(target, path, value) {
  const keys = path.split(".");
  const last = keys.pop();
  if (!last) {
    return;
  }
  let current = target;
  for (const key of keys) {
    if (current[key] === undefined || current[key] === null) {
      current[key] = {};
    }
    current = current[key];
  }
  current[last] = value;
}

function makePoint(lat, lon, extra = {}) {
  return { lat: normalizeNumber(lat), lon: normalizeNumber(lon), ...extra };
}

function stripClosedPolygon(polygon) {
  if (polygon.length >= 2) {
    const first = polygon[0];
    const last = polygon[polygon.length - 1];
    if (first.lat === last.lat && first.lon === last.lon) {
      return polygon.slice(0, -1);
    }
  }
  return polygon.slice();
}

function closePolygon(polygon) {
  const stripped = stripClosedPolygon(polygon);
  if (stripped.length === 0) {
    return [];
  }
  return [...stripped, clone(stripped[0])];
}

function distinctVertexCount(polygon) {
  return new Set(stripClosedPolygon(polygon).map((point) => `${point.lat.toFixed(7)},${point.lon.toFixed(7)}`)).size;
}

function ensureFinitePoint(point) {
  return Number.isFinite(point?.lat) && Number.isFinite(point?.lon);
}

function toTuplePolygon(polygon) {
  return closePolygon(polygon).map((point) => [point.lat, point.lon]);
}

function toRadians(degrees) {
  return (degrees * PI) / 180.0;
}

function toDegrees(radians) {
  return (radians * 180.0) / PI;
}

function haversineDistance(lat1, lon1, lat2, lon2) {
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.asin(Math.sqrt(a));
  return EARTH_RADIUS_M * c;
}

function destinationPoint(lat, lon, bearing, distance) {
  const latR = toRadians(lat);
  const lonR = toRadians(lon);
  const bearingR = toRadians(bearing);
  const d = distance / EARTH_RADIUS_M;
  const destLat = Math.asin(
    Math.sin(latR) * Math.cos(d) + Math.cos(latR) * Math.sin(d) * Math.cos(bearingR),
  );
  const destLon =
    lonR +
    Math.atan2(
      Math.sin(bearingR) * Math.sin(d) * Math.cos(latR),
      Math.cos(d) - Math.sin(latR) * Math.sin(destLat),
    );
  return { lat: toDegrees(destLat), lon: toDegrees(destLon) };
}

function bearingBetweenPoints(start, end) {
  const lat1 = toRadians(start.lat);
  const lat2 = toRadians(end.lat);
  const dLon = toRadians(end.lon - start.lon);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  return (toDegrees(Math.atan2(y, x)) + 360.0) % 360.0;
}

function deriveLandingFromRunwayEndpoints(start, end, altM = 0.0) {
  const runwayLengthM = haversineDistance(start.lat, start.lon, end.lat, end.lon);
  const headingDeg = bearingBetweenPoints(start, end);
  return {
    touchdown_point: {
      lat: start.lat,
      lon: start.lon,
      alt_m: normalizeNumber(altM),
    },
    heading_deg: headingDeg,
    runway_length_m: runwayLengthM,
  };
}

function deriveRunwayEndpoints(fieldProfile) {
  const touchdown = fieldProfile.landing.touchdown_point;
  const farEnd = destinationPoint(
    touchdown.lat,
    touchdown.lon,
    fieldProfile.landing.heading_deg,
    fieldProfile.landing.runway_length_m,
  );
  return {
    start: {
      lat: touchdown.lat,
      lon: touchdown.lon,
    },
    end: farEnd,
  };
}

function scanSpacingToDensity(scanSpacingM) {
  const clamped = Math.min(MAX_SCAN_SPACING_M, Math.max(MIN_SCAN_SPACING_M, scanSpacingM));
  const ratio = (MAX_SCAN_SPACING_M - clamped) / (MAX_SCAN_SPACING_M - MIN_SCAN_SPACING_M);
  return Math.round(ratio * 100);
}

function densityToScanSpacing(density) {
  const normalized = Math.min(100, Math.max(0, normalizeNumber(density)));
  return MAX_SCAN_SPACING_M - ((MAX_SCAN_SPACING_M - MIN_SCAN_SPACING_M) * normalized) / 100;
}

function pointInPolygon(lat, lon, polygon) {
  const closedPolygon = toTuplePolygon(polygon);
  if (closedPolygon.length < 4) {
    return false;
  }
  let inside = false;
  let j = closedPolygon.length - 1;
  for (let index = 0; index < closedPolygon.length; index += 1) {
    const [yi, xi] = closedPolygon[index];
    const [yj, xj] = closedPolygon[j];
    if (((yi > lat) !== (yj > lat)) && (lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi)) {
      inside = !inside;
    } else if (yi === lat && xi === lon) {
      return true;
    }
    j = index;
  }
  return inside;
}

function pointToSegmentDistance(lat, lon, lat1, lon1, lat2, lon2) {
  const latM = lat * 111_320;
  const lonM = lon * 111_320 * Math.cos(toRadians(lat));
  const lat1M = lat1 * 111_320;
  const lon1M = lon1 * 111_320 * Math.cos(toRadians(lat1));
  const lat2M = lat2 * 111_320;
  const lon2M = lon2 * 111_320 * Math.cos(toRadians(lat2));
  const dx = lon2M - lon1M;
  const dy = lat2M - lat1M;
  if (dx === 0 && dy === 0) {
    return Math.hypot(lonM - lon1M, latM - lat1M);
  }
  const t = Math.max(
    0,
    Math.min(1, ((lonM - lon1M) * dx + (latM - lat1M) * dy) / (dx * dx + dy * dy)),
  );
  const projX = lon1M + t * dx;
  const projY = lat1M + t * dy;
  return Math.hypot(lonM - projX, latM - projY);
}

function findNearestPolygonEdgeIndex(polygon, point) {
  const stripped = stripClosedPolygon(polygon);
  if (stripped.length < 2) {
    return Math.max(0, stripped.length - 1);
  }
  let minDistance = Number.POSITIVE_INFINITY;
  let insertAfterIndex = 0;
  for (let index = 0; index < stripped.length; index += 1) {
    const current = stripped[index];
    const next = stripped[(index + 1) % stripped.length];
    const distance = pointToSegmentDistance(
      point.lat,
      point.lon,
      current.lat,
      current.lon,
      next.lat,
      next.lon,
    );
    if (distance < minDistance) {
      minDistance = distance;
      insertAfterIndex = index;
    }
  }
  return insertAfterIndex;
}

function insertVertexIntoPolygon(polygon, point) {
  const stripped = stripClosedPolygon(polygon);
  if (stripped.length < 2) {
    return [...stripped, clone(point)];
  }
  const insertAfterIndex = findNearestPolygonEdgeIndex(stripped, point);
  return [
    ...stripped.slice(0, insertAfterIndex + 1),
    clone(point),
    ...stripped.slice(insertAfterIndex + 1),
  ];
}

function nearestBoundaryDistance(lat, lon, polygon) {
  const stripped = stripClosedPolygon(polygon);
  if (stripped.length < 2) {
    return Number.POSITIVE_INFINITY;
  }
  let minDistance = Number.POSITIVE_INFINITY;
  for (let index = 0; index < stripped.length; index += 1) {
    const current = stripped[index];
    const next = stripped[(index + 1) % stripped.length];
    minDistance = Math.min(
      minDistance,
      pointToSegmentDistance(lat, lon, current.lat, current.lon, next.lat, next.lon),
    );
  }
  return minDistance;
}

function linePolygonIntersections(lineY, polygon) {
  const intersections = [];
  for (let index = 0; index < polygon.length; index += 1) {
    const [x1, y1] = polygon[index];
    const [x2, y2] = polygon[(index + 1) % polygon.length];
    if ((y1 <= lineY && lineY < y2) || (y2 <= lineY && lineY < y1)) {
      if (y2 !== y1) {
        const t = (lineY - y1) / (y2 - y1);
        intersections.push(x1 + t * (x2 - x1));
      }
    }
  }
  intersections.sort((left, right) => left - right);
  return intersections;
}

function createDefaultFieldProfile() {
  return {
    name: "New Field",
    description: "",
    coordinate_system: "GCJ-02",
    boundary: {
      description: "",
      polygon: [],
    },
    landing: {
      description: "",
      touchdown_point: {
        lat: DEFAULT_CENTER.lat,
        lon: DEFAULT_CENTER.lon,
        alt_m: 0.0,
      },
      heading_deg: 180.0,
      glide_slope_deg: 3.0,
      approach_alt_m: 30.0,
      runway_length_m: 200.0,
      use_do_land_start: true,
    },
    scan: {
      description: "",
      altitude_m: 80.0,
      spacing_m: 200.0,
      heading_deg: 0.0,
    },
    attack_run: {
      approach_distance_m: 200.0,
      exit_distance_m: 200.0,
      release_acceptance_radius_m: 0.0,
      fallback_drop_point: null,
    },
    safety_buffer_m: 50.0,
  };
}

function mergeImportedProfile(data) {
  const merged = createDefaultFieldProfile();
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("Imported field.json must be a JSON object");
  }
  if (!data.boundary || !Array.isArray(data.boundary.polygon)) {
    throw new Error("Imported field.json must include boundary.polygon as an array");
  }
  if (!data.landing || !data.landing.touchdown_point) {
    throw new Error("Imported field.json must include landing.touchdown_point");
  }
  if (!data.scan || typeof data.scan !== "object") {
    throw new Error("Imported field.json must include scan settings");
  }
  if (typeof data.name === "string") {
    merged.name = data.name;
  }
  if (typeof data.description === "string") {
    merged.description = data.description;
  }
  if (typeof data.coordinate_system === "string") {
    merged.coordinate_system = data.coordinate_system;
  }
  Object.assign(merged.boundary, data.boundary ?? {});
  Object.assign(merged.landing, data.landing ?? {});
  Object.assign(merged.landing.touchdown_point, data.landing?.touchdown_point ?? {});
  Object.assign(merged.scan, data.scan ?? {});
  Object.assign(merged.attack_run, data.attack_run ?? {});
  if (data.safety_buffer_m !== undefined) {
    merged.safety_buffer_m = normalizeNumber(data.safety_buffer_m, merged.safety_buffer_m);
  }
  return merged;
}

function gcj02ToWgs84(lat, lon) {
  if (outOfChina(lat, lon)) {
    return { lat, lon };
  }
  const offset = delta(lat, lon);
  return {
    lat: lat - offset.lat,
    lon: lon - offset.lon,
  };
}

function wgs84ToGcj02(lat, lon) {
  if (outOfChina(lat, lon)) {
    return { lat, lon };
  }
  const offset = delta(lat, lon);
  return {
    lat: lat + offset.lat,
    lon: lon + offset.lon,
  };
}

function normalizeCoordinateSystemTag(coordinateSystem) {
  const normalized = String(coordinateSystem ?? "WGS84").trim().toUpperCase().replace(/_/g, "-");
  if (normalized === "GCJ02") {
    return "GCJ-02";
  }
  if (normalized === "WGS-84") {
    return "WGS84";
  }
  return normalized || "WGS84";
}

function formatBoundaryPolygon(polygon) {
  return stripClosedPolygon(polygon)
    .map((point) => `${point.lat.toFixed(6)}, ${point.lon.toFixed(6)}`)
    .join("\n");
}

function parseBoundaryText(text) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  return lines.map((line) => {
    const [latRaw, lonRaw] = line.split(",").map((segment) => segment.trim());
    const lat = Number(latRaw);
    const lon = Number(lonRaw);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      throw new Error(`Invalid boundary vertex: ${line}`);
    }
    return { lat, lon };
  });
}

function deriveLandingApproach(fieldProfile) {
  const touchdown = fieldProfile.landing.touchdown_point;
  const polygon = fieldProfile.boundary.polygon;
  const deltaAlt = fieldProfile.landing.approach_alt_m - touchdown.alt_m;
  if (deltaAlt <= 0) {
    throw new Error(
      `Approach alt (${fieldProfile.landing.approach_alt_m}) must be above touchdown alt (${touchdown.alt_m})`,
    );
  }
  const glideSlopeRadians = toRadians(fieldProfile.landing.glide_slope_deg);
  const tangent = Math.tan(glideSlopeRadians);
  if (!Number.isFinite(tangent) || tangent <= 0) {
    throw new Error(`Invalid glide slope (${fieldProfile.landing.glide_slope_deg})`);
  }
  const distance = deltaAlt / tangent;
  const reverseHeading = (fieldProfile.landing.heading_deg + 180.0) % 360.0;
  const approach = destinationPoint(
    touchdown.lat,
    touchdown.lon,
    reverseHeading,
    distance,
  );
  if (distinctVertexCount(polygon) >= 3 && !pointInPolygon(approach.lat, approach.lon, polygon)) {
    throw new Error(
      `Derived approach (${approach.lat.toFixed(6)}, ${approach.lon.toFixed(6)}) is outside geofence`,
    );
  }
  return {
    lat: approach.lat,
    lon: approach.lon,
    alt_m: fieldProfile.landing.approach_alt_m,
    distance_m: distance,
  };
}

function deriveTakeoffPreview(fieldProfile) {
  const touchdown = fieldProfile.landing.touchdown_point;
  const deltaAlt = fieldProfile.scan.altitude_m - touchdown.alt_m;
  if (deltaAlt <= 0) {
    throw new Error(
      `Scan altitude (${fieldProfile.scan.altitude_m}) must be above touchdown alt (${touchdown.alt_m})`,
    );
  }
  const takeoffHeading = (fieldProfile.landing.heading_deg + 180.0) % 360.0;
  const reverseHeading = (takeoffHeading + 180.0) % 360.0;
  const midpoint = destinationPoint(
    touchdown.lat,
    touchdown.lon,
    takeoffHeading,
    fieldProfile.landing.runway_length_m / 2,
  );
  const start = destinationPoint(
    midpoint.lat,
    midpoint.lon,
    reverseHeading,
    fieldProfile.landing.runway_length_m * 0.4,
  );
  const climbout = destinationPoint(
    touchdown.lat,
    touchdown.lon,
    takeoffHeading,
    fieldProfile.landing.runway_length_m,
  );
  return {
    start_lat: start.lat,
    start_lon: start.lon,
    start_alt_m: touchdown.alt_m,
    climbout_lat: climbout.lat,
    climbout_lon: climbout.lon,
    climbout_alt_m: fieldProfile.scan.altitude_m,
    heading_deg: takeoffHeading,
    climb_angle_deg: toDegrees(Math.atan2(deltaAlt, fieldProfile.landing.runway_length_m)),
  };
}

function generateBoustrophedonScan(boundaryPolygon, scanAltM, scanSpacingM, scanHeadingDeg) {
  const polygon = stripClosedPolygon(boundaryPolygon);
  if (polygon.length < 3) {
    throw new Error("Polygon must have at least 3 vertices");
  }
  if (scanSpacingM <= 0) {
    throw new Error(`Scan spacing must be positive, got ${scanSpacingM}`);
  }
  const centroidLat = polygon.reduce((sum, point) => sum + point.lat, 0) / polygon.length;
  const centroidLon = polygon.reduce((sum, point) => sum + point.lon, 0) / polygon.length;
  const rotation = -toRadians(scanHeadingDeg - 90.0);
  const metersPerDegreeLat = 110540.0;
  const metersPerDegreeLon = 111320.0 * Math.cos(toRadians(centroidLat));
  const rotatedPolygon = polygon.map((point) => {
    const x = (point.lon - centroidLon) * metersPerDegreeLon;
    const y = (point.lat - centroidLat) * metersPerDegreeLat;
    const xr = x * Math.cos(rotation) - y * Math.sin(rotation);
    const yr = x * Math.sin(rotation) + y * Math.cos(rotation);
    return [xr, yr];
  });
  const ys = rotatedPolygon.map((point) => point[1]);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const waypoints = [];
  let sweepIndex = 0;
  let y = yMin + scanSpacingM / 2;
  while (y <= yMax - scanSpacingM / 4) {
    const intersections = linePolygonIntersections(y, rotatedPolygon);
    for (let index = 0; index < intersections.length - 1; index += 2) {
      let entryX = intersections[index];
      let exitX = intersections[index + 1];
      if (sweepIndex % 2 === 1) {
        [entryX, exitX] = [exitX, entryX];
      }
      for (const waypointX of [entryX, exitX]) {
        const inverseX = waypointX * Math.cos(-rotation) - y * Math.sin(-rotation);
        const inverseY = waypointX * Math.sin(-rotation) + y * Math.cos(-rotation);
        waypoints.push({
          lat: centroidLat + inverseY / metersPerDegreeLat,
          lon: centroidLon + inverseX / metersPerDegreeLon,
          alt_m: scanAltM,
        });
      }
    }
    sweepIndex += 1;
    y += scanSpacingM;
  }
  return waypoints;
}

function validateFieldProfile(fieldProfile) {
  const blocking = [];
  const advisory = [];
  let derivedApproach = null;
  let derivedTakeoff = null;
  let scanPreview = [];

  const boundary = stripClosedPolygon(fieldProfile.boundary.polygon);
  const vertexCount = distinctVertexCount(boundary);
  if (vertexCount < 3) {
    blocking.push("Geofence polygon must have at least 3 distinct vertices");
  }
  if (fieldProfile.safety_buffer_m <= 0) {
    blocking.push(`safety_buffer_m must be positive, got ${fieldProfile.safety_buffer_m}`);
  }
  if (fieldProfile.landing.runway_length_m <= 0) {
    blocking.push(`runway_length_m must be positive, got ${fieldProfile.landing.runway_length_m}`);
  }
  if (fieldProfile.scan.spacing_m <= 0) {
    blocking.push(`scan.spacing_m must be positive, got ${fieldProfile.scan.spacing_m}`);
  }

  if (vertexCount >= 3) {
    const touchdown = fieldProfile.landing.touchdown_point;
    if (!pointInPolygon(touchdown.lat, touchdown.lon, boundary)) {
      blocking.push(
        `landing.touchdown_point (${touchdown.lat}, ${touchdown.lon}) is outside the geofence boundary`,
      );
    }
    try {
      derivedApproach = deriveLandingApproach(fieldProfile);
      if (fieldProfile.landing.glide_slope_deg > MAX_SAFE_GLIDE_SLOPE_DEG) {
        advisory.push(
          `Predicted descent angle ${fieldProfile.landing.glide_slope_deg.toFixed(1)}° exceeds the ${MAX_SAFE_GLIDE_SLOPE_DEG.toFixed(1)}° advisory threshold`,
        );
      }
    } catch (error) {
      blocking.push(error instanceof Error ? error.message : String(error));
    }
    try {
      derivedTakeoff = deriveTakeoffPreview(fieldProfile);
      if (derivedTakeoff.climb_angle_deg > MAX_SAFE_CLIMB_ANGLE_DEG) {
        advisory.push(
          `Predicted climb angle ${derivedTakeoff.climb_angle_deg.toFixed(1)}° exceeds the ${MAX_SAFE_CLIMB_ANGLE_DEG.toFixed(1)}° advisory threshold`,
        );
      }
    } catch (error) {
      blocking.push(error instanceof Error ? error.message : String(error));
    }
    if (fieldProfile.scan.spacing_m > 0) {
      try {
        scanPreview = generateBoustrophedonScan(
          boundary,
          fieldProfile.scan.altitude_m,
          fieldProfile.scan.spacing_m,
          fieldProfile.scan.heading_deg,
        );
      } catch (error) {
        blocking.push(error instanceof Error ? error.message : String(error));
      }
    }
  }

  advisory.push("GCJ-02 ↔ WGS84 conversion is approximate and may introduce meter-level offsets.");

  return {
    blocking,
    advisory,
    derivedApproach,
    derivedTakeoff,
    scanPreview,
  };
}

function exportFieldProfile(fieldProfile) {
  const exported = clone(fieldProfile);
  exported.coordinate_system = "WGS84";
  exported.boundary.polygon = closePolygon(fieldProfile.boundary.polygon).map((point) => gcj02ToWgs84(point.lat, point.lon));
  const touchdown = gcj02ToWgs84(
    fieldProfile.landing.touchdown_point.lat,
    fieldProfile.landing.touchdown_point.lon,
  );
  exported.landing.touchdown_point = {
    ...clone(fieldProfile.landing.touchdown_point),
    lat: touchdown.lat,
    lon: touchdown.lon,
  };
  return exported;
}

function syncLandingFromRunway(fieldProfile, runwayStart, runwayEnd) {
  const derived = deriveLandingFromRunwayEndpoints(
    runwayStart,
    runwayEnd,
    fieldProfile.landing.touchdown_point.alt_m,
  );
  fieldProfile.landing.touchdown_point = derived.touchdown_point;
  fieldProfile.landing.heading_deg = derived.heading_deg;
  fieldProfile.landing.runway_length_m = derived.runway_length_m;
}

function importFieldProfile(rawData) {
  const merged = mergeImportedProfile(rawData);
  const imported = clone(merged);
  const coordinateSystem = normalizeCoordinateSystemTag(merged.coordinate_system);
  imported.coordinate_system = "GCJ-02";

  if (coordinateSystem === "GCJ-02") {
    imported.boundary.polygon = stripClosedPolygon(merged.boundary.polygon ?? []).map((point) => ({
      lat: point.lat,
      lon: point.lon,
    }));
    imported.landing.touchdown_point = {
      ...merged.landing.touchdown_point,
      lat: merged.landing.touchdown_point.lat,
      lon: merged.landing.touchdown_point.lon,
    };
    return imported;
  }

  imported.boundary.polygon = stripClosedPolygon(merged.boundary.polygon ?? []).map((point) => {
    const gcj = wgs84ToGcj02(point.lat, point.lon);
    return { lat: gcj.lat, lon: gcj.lon };
  });
  const touchdown = wgs84ToGcj02(merged.landing.touchdown_point.lat, merged.landing.touchdown_point.lon);
  imported.landing.touchdown_point = {
    ...merged.landing.touchdown_point,
    lat: touchdown.lat,
    lon: touchdown.lon,
  };
  return imported;
}

export {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  MIN_SCAN_SPACING_M,
  MAX_SCAN_SPACING_M,
  MAX_SAFE_CLIMB_ANGLE_DEG,
  MAX_SAFE_GLIDE_SLOPE_DEG,
  bearingBetweenPoints,
  closePolygon,
  createDefaultFieldProfile,
  densityToScanSpacing,
  deriveLandingApproach,
  deriveLandingFromRunwayEndpoints,
  deriveRunwayEndpoints,
  deriveTakeoffPreview,
  destinationPoint,
  distinctVertexCount,
  exportFieldProfile,
  findNearestPolygonEdgeIndex,
  formatBoundaryPolygon,
  gcj02ToWgs84,
  generateBoustrophedonScan,
  getByPath,
  haversineDistance,
  importFieldProfile,
  insertVertexIntoPolygon,
  nearestBoundaryDistance,
  parseBoundaryText,
  pointInPolygon,
  scanSpacingToDensity,
  setByPath,
  stripClosedPolygon,
  syncLandingFromRunway,
  validateFieldProfile,
  wgs84ToGcj02,
};
