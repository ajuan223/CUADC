const DEFAULT_CENTER = Object.freeze({ lat: 30.27, lon: 120.095 });
const DEFAULT_ZOOM = 15;
const MIN_SCAN_SPACING_M = 40.0;
const MAX_SCAN_SPACING_M = 400.0;
const MAX_SAFE_GLIDE_SLOPE_DEG = 6.0;
const MAX_SAFE_CLIMB_ANGLE_DEG = 12.0;
const SCAN_BOUNDARY_MARGIN_M = 100.0;
const FIELD_EDITOR_TAB_PLANNING = "planning";
const FIELD_EDITOR_TAB_REPLAY = "replay";
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
    loiter_point: null,
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
      boundary_margin_m: 100.0,
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
  if (data.loiter_point === null) {
    merged.loiter_point = null;
  } else if (data.loiter_point && typeof data.loiter_point === "object") {
    merged.loiter_point = {
      lat: normalizeNumber(data.loiter_point.lat, DEFAULT_CENTER.lat),
      lon: normalizeNumber(data.loiter_point.lon, DEFAULT_CENTER.lon),
    };
  }
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

function parseCsvLine(line) {
  const cells = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      if (inQuotes && line[index + 1] === '"') {
        current += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (char === "," && !inQuotes) {
      cells.push(current);
      current = "";
      continue;
    }
    current += char;
  }

  cells.push(current);
  return cells.map((cell) => cell.trim());
}

function parseOptionalFloat(value) {
  const text = String(value ?? "").trim();
  if (text === "") {
    return null;
  }
  const numeric = Number(text);
  return Number.isFinite(numeric) ? numeric : null;
}

function formatQgcWplNumber(value) {
  const numeric = normalizeNumber(value);
  return String(numeric);
}

function formatQgcWplLine(item) {
  return [
    item.seq,
    item.current,
    item.frame,
    item.command,
    item.p1,
    item.p2,
    item.p3,
    item.p4,
    item.lat,
    item.lon,
    item.alt,
    item.autocontinue,
  ]
    .map((value) => formatQgcWplNumber(value))
    .join("\t");
}

function generateWaypointFile(fieldProfile, validation) {
  if (validation?.blocking?.length) {
    throw new Error("Cannot generate waypoints while validation has blocking errors");
  }
  const scanPreview = validation?.scanPreview ?? [];
  const derivedApproach = validation?.derivedApproach;
  if (!derivedApproach) {
    throw new Error("Cannot generate waypoints without a derived approach waypoint");
  }
  if (scanPreview.length === 0) {
    throw new Error("Cannot generate waypoints without scan preview waypoints");
  }

  const touchdown = gcj02ToWgs84(
    fieldProfile.landing.touchdown_point.lat,
    fieldProfile.landing.touchdown_point.lon,
  );
  const approach = gcj02ToWgs84(derivedApproach.lat, derivedApproach.lon);
  const loiterSource = fieldProfile.loiter_point ?? scanPreview[scanPreview.length - 1];
  const loiter = gcj02ToWgs84(loiterSource.lat, loiterSource.lon);

  const missionItems = [
    {
      seq: 0,
      current: 1,
      frame: 0,
      command: 16,
      p1: 0,
      p2: 0,
      p3: 0,
      p4: 0,
      lat: touchdown.lat,
      lon: touchdown.lon,
      alt: 0,
      autocontinue: 1,
    },
    {
      seq: 1,
      current: 0,
      frame: 3,
      command: 22,
      p1: 10,
      p2: 0,
      p3: 0,
      p4: 0,
      lat: 0,
      lon: 0,
      alt: fieldProfile.scan.altitude_m,
      autocontinue: 1,
    },
  ];

  for (const point of scanPreview) {
    const wgsPoint = gcj02ToWgs84(point.lat, point.lon);
    missionItems.push({
      seq: missionItems.length,
      current: 0,
      frame: 3,
      command: 16,
      p1: 0,
      p2: 0,
      p3: 0,
      p4: 0,
      lat: wgsPoint.lat,
      lon: wgsPoint.lon,
      alt: fieldProfile.scan.altitude_m,
      autocontinue: 1,
    });
  }

  missionItems.push({
    seq: missionItems.length,
    current: 0,
    frame: 3,
    command: 17,
    p1: 0,
    p2: 0,
    p3: 0,
    p4: 0,
    lat: loiter.lat,
    lon: loiter.lon,
    alt: fieldProfile.scan.altitude_m,
    autocontinue: 1,
  });
  missionItems.push({
    seq: missionItems.length,
    current: 0,
    frame: 3,
    command: 189,
    p1: 0,
    p2: 0,
    p3: 0,
    p4: 0,
    lat: 0,
    lon: 0,
    alt: 0,
    autocontinue: 1,
  });
  missionItems.push({
    seq: missionItems.length,
    current: 0,
    frame: 3,
    command: 16,
    p1: 0,
    p2: 0,
    p3: 0,
    p4: 0,
    lat: approach.lat,
    lon: approach.lon,
    alt: fieldProfile.landing.approach_alt_m,
    autocontinue: 1,
  });
  missionItems.push({
    seq: missionItems.length,
    current: 0,
    frame: 3,
    command: 21,
    p1: 0,
    p2: 0,
    p3: 0,
    p4: 0,
    lat: touchdown.lat,
    lon: touchdown.lon,
    alt: 0,
    autocontinue: 1,
  });

  return ["QGC WPL 110", ...missionItems.map((item) => formatQgcWplLine(item))].join("\n");
}

function formatGeofencePoly(fieldProfile) {
  const polygon = closePolygon(fieldProfile.boundary.polygon).map((point) => gcj02ToWgs84(point.lat, point.lon));
  return [String(polygon.length), ...polygon.map((point) => `${point.lat} ${point.lon}`)].join("\n");
}

function parseBooleanLike(value) {
  const normalized = String(value ?? "")
    .trim()
    .toLowerCase();
  return normalized === "true" || normalized === "1" || normalized === "yes";
}

function clampReplayIndex(index, sampleCount) {
  if (sampleCount <= 0) {
    return 0;
  }
  return Math.min(sampleCount - 1, Math.max(0, Math.round(normalizeNumber(index))));
}

function replayProgressForIndex(index, sampleCount) {
  if (sampleCount <= 1) {
    return 0;
  }
  return (clampReplayIndex(index, sampleCount) / (sampleCount - 1)) * 100;
}

function replayIndexFromProgress(progress, sampleCount) {
  if (sampleCount <= 1) {
    return 0;
  }
  const normalizedProgress = Math.min(100, Math.max(0, normalizeNumber(progress)));
  return clampReplayIndex((normalizedProgress / 100) * (sampleCount - 1), sampleCount);
}

function normalizeFieldEditorTab(tab) {
  return tab === FIELD_EDITOR_TAB_REPLAY ? FIELD_EDITOR_TAB_REPLAY : FIELD_EDITOR_TAB_PLANNING;
}

function fieldEditorPanelVisibility(tab) {
  const activeTab = normalizeFieldEditorTab(tab);
  return {
    activeTab,
    planning: activeTab === FIELD_EDITOR_TAB_PLANNING,
    replay: activeTab === FIELD_EDITOR_TAB_REPLAY,
  };
}

function fieldEditorOverlayVisibility(tab) {
  const panelVisibility = fieldEditorPanelVisibility(tab);
  return {
    ...panelVisibility,
    planningGeometry: true,
    replayGeometry: panelVisibility.replay,
  };
}

function fieldEditorInteractionTab(mode) {
  if (mode === "idle") {
    return null;
  }
  if (mode === "setRunway" || mode === "setDropPoint" || mode === "setLoiterPoint" || mode === "drawBoundary" || mode === "editBoundary") {
    return FIELD_EDITOR_TAB_PLANNING;
  }
  return null;
}

function shouldStopReplayWhenLeavingTab(previousTab, nextTab) {
  return normalizeFieldEditorTab(previousTab) === FIELD_EDITOR_TAB_REPLAY && normalizeFieldEditorTab(nextTab) !== FIELD_EDITOR_TAB_REPLAY;
}

function parseFlightLogCsv(text) {
  if (typeof text !== "string" || text.trim() === "") {
    throw new Error("Flight log is empty");
  }

  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) {
    throw new Error("Flight log must include a header and at least one data row");
  }

  const headers = parseCsvLine(lines[0]);
  const rows = lines.slice(1).map((line) => {
    const cells = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ""]));
  });

  const samples = [];
  let firstTimestamp = null;
  let releaseTimestamp = null;
  let plannedDrop = null;
  let actualDrop = null;

  for (const row of rows) {
    const timestamp = parseOptionalFloat(row.timestamp);
    const lat = parseOptionalFloat(row.lat);
    const lon = parseOptionalFloat(row.lon);
    const releaseTriggered = parseBooleanLike(row.release_triggered);
    const rowReleaseTimestamp = parseOptionalFloat(row.release_timestamp);
    const plannedDropLat = parseOptionalFloat(row.planned_drop_lat);
    const plannedDropLon = parseOptionalFloat(row.planned_drop_lon);
    const actualDropLat = parseOptionalFloat(row.actual_drop_lat);
    const actualDropLon = parseOptionalFloat(row.actual_drop_lon);

    if (rowReleaseTimestamp !== null && releaseTimestamp === null) {
      releaseTimestamp = rowReleaseTimestamp;
    }

    if (plannedDropLat !== null && plannedDropLon !== null) {
      const converted = wgs84ToGcj02(plannedDropLat, plannedDropLon);
      plannedDrop = {
        lat: converted.lat,
        lon: converted.lon,
        source: row.planned_drop_source || "",
      };
    }

    if (actualDropLat !== null && actualDropLon !== null) {
      const converted = wgs84ToGcj02(actualDropLat, actualDropLon);
      actualDrop = {
        lat: converted.lat,
        lon: converted.lon,
        source: row.actual_drop_source || "",
      };
    }

    if (lat === null || lon === null) {
      continue;
    }

    const converted = wgs84ToGcj02(lat, lon);
    if (timestamp !== null && firstTimestamp === null) {
      firstTimestamp = timestamp;
    }
    samples.push({
      timestamp,
      relativeTimeS:
        timestamp !== null && firstTimestamp !== null ? Math.max(0, timestamp - firstTimestamp) : samples.length,
      lat: converted.lat,
      lon: converted.lon,
      alt_m: parseOptionalFloat(row.alt_m),
      relative_alt_m: parseOptionalFloat(row.relative_alt_m),
      mode: row.mode || "",
      releaseTriggered,
    });
  }

  if (samples.length === 0) {
    throw new Error("Flight log does not contain any valid trajectory samples");
  }

  let releaseSampleIndex = -1;
  if (releaseTimestamp !== null) {
    let closestDistance = Number.POSITIVE_INFINITY;
    for (let index = 0; index < samples.length; index += 1) {
      const sampleTimestamp = samples[index].timestamp;
      if (sampleTimestamp === null) {
        continue;
      }
      const distance = Math.abs(sampleTimestamp - releaseTimestamp);
      if (distance < closestDistance) {
        closestDistance = distance;
        releaseSampleIndex = index;
      }
    }
  }
  if (releaseSampleIndex < 0) {
    releaseSampleIndex = samples.findIndex((sample) => sample.releaseTriggered);
  }

  return {
    headers,
    rowCount: rows.length,
    sampleCount: samples.length,
    samples,
    releaseTimestamp,
    releaseSampleIndex,
    plannedDrop,
    actualDrop,
    hasReleaseMetadata: headers.includes("release_triggered") || headers.includes("release_timestamp"),
    hasActualDropMetadata:
      headers.includes("actual_drop_lat") || headers.includes("actual_drop_lon") || headers.includes("actual_drop_source"),
    durationS: samples[samples.length - 1].relativeTimeS,
  };
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
  const takeoffHeading = fieldProfile.landing.heading_deg;
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
    fieldProfile.landing.runway_length_m * 0.5,
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

function shrinkPolygon(polygon, marginM) {
  if (marginM <= 0 || polygon.length < 3) {
    return polygon.slice();
  }
  const n = polygon.length;
  const cx = polygon.reduce((sum, p) => sum + (Array.isArray(p) ? p[0] : p.x || 0), 0) / n;
  const cy = polygon.reduce((sum, p) => sum + (Array.isArray(p) ? p[1] : p.y || 0), 0) / n;
  const shrunk = [];
  for (let i = 0; i < n; i += 1) {
    const px = Array.isArray(polygon[i]) ? polygon[i][0] : polygon[i].x || 0;
    const py = Array.isArray(polygon[i]) ? polygon[i][1] : polygon[i].y || 0;
    const ax = Array.isArray(polygon[(i - 1 + n) % n]) ? polygon[(i - 1 + n) % n][0] : (polygon[(i - 1 + n) % n].x || 0);
    const ay = Array.isArray(polygon[(i - 1 + n) % n]) ? polygon[(i - 1 + n) % n][1] : (polygon[(i - 1 + n) % n].y || 0);
    const bx = Array.isArray(polygon[(i + 1) % n]) ? polygon[(i + 1) % n][0] : (polygon[(i + 1) % n].x || 0);
    const by = Array.isArray(polygon[(i + 1) % n]) ? polygon[(i + 1) % n][1] : (polygon[(i + 1) % n].y || 0);
    const e1x = px - ax, e1y = py - ay;
    const e2x = bx - px, e2y = by - py;
    let nx = e1y + e2y;
    let ny = -e1x - e2x;
    let length = Math.hypot(nx, ny);
    if (length < 1e-12) {
      nx = cx - px;
      ny = cy - py;
      length = Math.hypot(nx, ny);
      if (length < 1e-12) {
        shrunk.push([px, py]);
        continue;
      }
    }
    nx /= length;
    ny /= length;
    const dot = nx * (cx - px) + ny * (cy - py);
    if (dot < 0) {
      nx = -nx;
      ny = -ny;
    }
    shrunk.push([px + nx * marginM, py + ny * marginM]);
  }
  const result = [];
  for (let i = 0; i < shrunk.length; i += 1) {
    const sx = shrunk[i][0], sy = shrunk[i][1];
    if (pointInPolygonXY(sx, sy, polygon)) {
      result.push([sx, sy]);
    } else {
      const ox = Array.isArray(polygon[i]) ? polygon[i][0] : (polygon[i].x || 0);
      const oy = Array.isArray(polygon[i]) ? polygon[i][1] : (polygon[i].y || 0);
      let dx = cx - ox, dy = cy - oy;
      const d = Math.hypot(dx, dy);
      if (d < 1e-12) {
        result.push([ox, oy]);
        continue;
      }
      dx /= d;
      dy /= d;
      let lo = 0, hi = d;
      for (let j = 0; j < 30; j += 1) {
        const mid = (lo + hi) / 2;
        if (pointInPolygonXY(ox + dx * mid, oy + dy * mid, polygon)) {
          hi = mid;
        } else {
          lo = mid;
        }
      }
      const safeD = Math.max(0, hi * 0.9);
      result.push([ox + dx * safeD, oy + dy * safeD]);
    }
  }
  return result;
}

function pointInPolygonXY(x, y, polygon) {
  const n = polygon.length;
  let inside = false;
  for (let i = 0; i < n; i += 1) {
    const x1 = Array.isArray(polygon[i]) ? polygon[i][0] : (polygon[i].x || 0);
    const y1 = Array.isArray(polygon[i]) ? polygon[i][1] : (polygon[i].y || 0);
    const x2 = Array.isArray(polygon[(i + 1) % n]) ? polygon[(i + 1) % n][0] : (polygon[(i + 1) % n].x || 0);
    const y2 = Array.isArray(polygon[(i + 1) % n]) ? polygon[(i + 1) % n][1] : (polygon[(i + 1) % n].y || 0);
    const cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1);
    if (Math.abs(cross) < 1e-9) {
      const minX = Math.min(x1, x2) - 1e-9;
      const maxX = Math.max(x1, x2) + 1e-9;
      const minY = Math.min(y1, y2) - 1e-9;
      const maxY = Math.max(y1, y2) + 1e-9;
      if (minX <= x && x <= maxX && minY <= y && y <= maxY) {
        return true;
      }
    }
    if (((y1 > y) !== (y2 > y)) && (y2 !== y1)) {
      const ix = (x2 - x1) * (y - y1) / (y2 - y1) + x1;
      if (x < ix) {
        inside = !inside;
      }
    }
  }
  return inside;
}

function generateBoustrophedonScan(boundaryPolygon, scanAltM, scanSpacingM, scanHeadingDeg, boundaryMarginM = 0) {
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
  const scanPolygon = boundaryMarginM > 0 ? shrinkPolygon(rotatedPolygon, boundaryMarginM) : rotatedPolygon;
  const ys = scanPolygon.map((point) => point[1]);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const waypoints = [];
  let sweepIndex = 0;
  let y = yMin + scanSpacingM / 2;
  while (y <= yMax - scanSpacingM / 4) {
    const intersections = linePolygonIntersections(y, scanPolygon);
    for (let index = 0; index < intersections.length - 1; index += 2) {
      let entryX = intersections[index];
      let exitX = intersections[index + 1];
      const midpointX = (entryX + exitX) / 2.0;
      if (!pointInPolygonXY(midpointX, y, scanPolygon)) continue;
      const segmentWidth = exitX - entryX;
      const insetM = Math.min(5.0, Math.max(segmentWidth / 10.0, 1.0));
      entryX = entryX + insetM;
      exitX = exitX - insetM;
      if (entryX > exitX) {
        entryX = midpointX;
        exitX = midpointX;
      }
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
    if (fieldProfile.loiter_point && !pointInPolygon(fieldProfile.loiter_point.lat, fieldProfile.loiter_point.lon, boundary)) {
      blocking.push(
        `loiter_point (${fieldProfile.loiter_point.lat}, ${fieldProfile.loiter_point.lon}) is outside the geofence boundary`,
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
          fieldProfile.scan.boundary_margin_m ?? 100.0,
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
  const coordinateSystem = "WGS84";
  const polygon = closePolygon(fieldProfile.boundary.polygon).map((point) => gcj02ToWgs84(point.lat, point.lon));
  const touchdown = gcj02ToWgs84(
    fieldProfile.landing.touchdown_point.lat,
    fieldProfile.landing.touchdown_point.lon,
  );

  let fallback_drop_point = null;
  if (fieldProfile.attack_run.fallback_drop_point) {
    const dp = gcj02ToWgs84(
      fieldProfile.attack_run.fallback_drop_point.lat,
      fieldProfile.attack_run.fallback_drop_point.lon,
    );
    fallback_drop_point = { lat: dp.lat, lon: dp.lon };
  }

  const leanProfile = {
    name: fieldProfile.name,
    description: fieldProfile.description,
    coordinate_system: coordinateSystem,
    boundary: {
      description: fieldProfile.boundary.description || "",
      polygon: polygon
    },
    landing: {
      description: fieldProfile.landing.description || "",
      touchdown_point: {
        lat: touchdown.lat,
        lon: touchdown.lon,
        alt_m: fieldProfile.landing.touchdown_point.alt_m
      },
      heading_deg: fieldProfile.landing.heading_deg
    },
    scan: {
      description: fieldProfile.scan.description || "",
      altitude_m: fieldProfile.scan.altitude_m
    },
    attack_run: {
      approach_distance_m: fieldProfile.attack_run.approach_distance_m,
      exit_distance_m: fieldProfile.attack_run.exit_distance_m,
      release_acceptance_radius_m: fieldProfile.attack_run.release_acceptance_radius_m,
      fallback_drop_point: fallback_drop_point
    },
    safety_buffer_m: fieldProfile.safety_buffer_m
  };

  let jsonString = JSON.stringify(leanProfile, null, 2);
  jsonString = jsonString.replace(/"name":\s*".*?",/, '$& // [shared]');
  jsonString = jsonString.replace(/"coordinate_system":\s*".*?",/, '$& // [shared]');
  jsonString = jsonString.replace(/"boundary":\s*\{/, '"boundary": { // [shared]');
  jsonString = jsonString.replace(/"landing":\s*\{/, '"landing": { // [shared]');
  jsonString = jsonString.replace(/"scan":\s*\{/, '"scan": { // [shared]');
  jsonString = jsonString.replace(/"attack_run":\s*\{/, '"attack_run": { // [runtime]');
  jsonString = jsonString.replace(/"safety_buffer_m":\s*[0-9.]+/, '$& // [runtime]');

  return jsonString;
}

function exportPlanningProfile(fieldProfile) {
  const planningProfile = {
    landing: {
      glide_slope_deg: fieldProfile.landing.glide_slope_deg,
      approach_alt_m: fieldProfile.landing.approach_alt_m,
      runway_length_m: fieldProfile.landing.runway_length_m,
      use_do_land_start: fieldProfile.landing.use_do_land_start,
    },
    scan: {
      spacing_m: fieldProfile.scan.spacing_m,
      heading_deg: fieldProfile.scan.heading_deg,
      boundary_margin_m: fieldProfile.scan.boundary_margin_m,
    },
    loiter_point: fieldProfile.loiter_point
      ? gcj02ToWgs84(fieldProfile.loiter_point.lat, fieldProfile.loiter_point.lon)
      : null
  };

  let jsonString = JSON.stringify(planningProfile, null, 2);
  jsonString = jsonString.replace(/"landing":\s*\{/, '"landing": { // [planning-only]');
  jsonString = jsonString.replace(/"scan":\s*\{/, '"scan": { // [planning-only]');
  jsonString = jsonString.replace(/"loiter_point":\s*(null|\{)/, '"loiter_point": $1 // [planning-only]');

  return jsonString;
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
    imported.loiter_point = merged.loiter_point
      ? {
        lat: merged.loiter_point.lat,
        lon: merged.loiter_point.lon,
      }
      : null;
    if (merged.attack_run.fallback_drop_point) {
      imported.attack_run.fallback_drop_point = {
        lat: merged.attack_run.fallback_drop_point.lat,
        lon: merged.attack_run.fallback_drop_point.lon,
      };
    }
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
  imported.loiter_point = merged.loiter_point
    ? wgs84ToGcj02(merged.loiter_point.lat, merged.loiter_point.lon)
    : null;
  if (merged.attack_run.fallback_drop_point) {
    const dpGcj = wgs84ToGcj02(merged.attack_run.fallback_drop_point.lat, merged.attack_run.fallback_drop_point.lon);
    imported.attack_run.fallback_drop_point = {
      lat: dpGcj.lat,
      lon: dpGcj.lon,
    };
  }
  return imported;
}

export {
  DEFAULT_CENTER,
  DEFAULT_ZOOM,
  MIN_SCAN_SPACING_M,
  MAX_SCAN_SPACING_M,
  MAX_SAFE_CLIMB_ANGLE_DEG,
  MAX_SAFE_GLIDE_SLOPE_DEG,
  SCAN_BOUNDARY_MARGIN_M,
  FIELD_EDITOR_TAB_PLANNING,
  FIELD_EDITOR_TAB_REPLAY,
  bearingBetweenPoints,
  closePolygon,
  clampReplayIndex,
  createDefaultFieldProfile,
  densityToScanSpacing,
  deriveLandingApproach,
  deriveLandingFromRunwayEndpoints,
  deriveRunwayEndpoints,
  deriveTakeoffPreview,
  destinationPoint,
  distinctVertexCount,
  exportFieldProfile,
  exportPlanningProfile,
  fieldEditorInteractionTab,
  fieldEditorOverlayVisibility,
  fieldEditorPanelVisibility,
  findNearestPolygonEdgeIndex,
  formatBoundaryPolygon,
  formatGeofencePoly,
  gcj02ToWgs84,
  generateBoustrophedonScan,
  generateWaypointFile,
  getByPath,
  haversineDistance,
  importFieldProfile,
  insertVertexIntoPolygon,
  nearestBoundaryDistance,
  parseBoundaryText,
  parseFlightLogCsv,
  parseOptionalFloat,
  pointInPolygon,
  replayIndexFromProgress,
  replayProgressForIndex,
  scanSpacingToDensity,
  setByPath,
  shouldStopReplayWhenLeavingTab,
  stripClosedPolygon,
  syncLandingFromRunway,
  validateFieldProfile,
  wgs84ToGcj02,
};
