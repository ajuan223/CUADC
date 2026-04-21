import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

import {
  MAX_SAFE_CLIMB_ANGLE_DEG,
  MAX_SAFE_GLIDE_SLOPE_DEG,
  closePolygon,
  createDefaultFieldProfile,
  densityToScanSpacing,
  deriveLandingFromRunwayEndpoints,
  deriveRunwayEndpoints,
  deriveTakeoffPreview,
  exportFieldProfile,
  fieldEditorInteractionTab,
  fieldEditorOverlayVisibility,
  fieldEditorPanelVisibility,
  FIELD_EDITOR_TAB_PLANNING,
  FIELD_EDITOR_TAB_REPLAY,
  findNearestPolygonEdgeIndex,
  formatGeofencePoly,
  gcj02ToWgs84,
  generateBoustrophedonScan,
  generateWaypointFile,
  importFieldProfile,
  insertVertexIntoPolygon,
  parseBoundaryText,
  parseFlightLogCsv,
  replayIndexFromProgress,
  replayProgressForIndex,
  scanSpacingToDensity,
  syncLandingFromRunway,
  validateFieldProfile,
  wgs84ToGcj02,
} from "../../src/field_editor/logic.mjs";

const SAMPLE_WGS = { lat: 30.261, lon: 120.095 };
const SAMPLE_BOUNDARY_GCJ = [
  { lat: 30.27, lon: 120.09 },
  { lat: 30.27, lon: 120.1 },
  { lat: 30.26, lon: 120.1 },
  { lat: 30.26, lon: 120.09 },
];
const FIXTURE_DIR = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "fixtures",
  "replay",
);

test("runway endpoints derive touchdown heading and runway length", () => {
  const start = { lat: 30.261, lon: 120.095 };
  const end = { lat: 30.2625, lon: 120.095 };
  const derived = deriveLandingFromRunwayEndpoints(start, end, 12);
  assert.equal(derived.touchdown_point.alt_m, 12);
  assert.equal(derived.touchdown_point.lat, start.lat);
  assert.equal(derived.touchdown_point.lon, start.lon);
  assert.ok(derived.heading_deg >= 0 && derived.heading_deg <= 360);
  assert.ok(derived.runway_length_m > 100);
});

test("syncLandingFromRunway updates field profile landing facts", () => {
  const field = createDefaultFieldProfile();
  syncLandingFromRunway(field, { lat: 30.261, lon: 120.095 }, { lat: 30.262, lon: 120.096 });
  const runway = deriveRunwayEndpoints(field);
  assert.ok(Math.abs(runway.start.lat - field.landing.touchdown_point.lat) < 1e-9);
  assert.ok(Math.abs(runway.start.lon - field.landing.touchdown_point.lon) < 1e-9);
  assert.ok(field.landing.runway_length_m > 0);
});

test("scan density maps inversely to scan spacing", () => {
  assert.equal(densityToScanSpacing(0), 400);
  assert.equal(densityToScanSpacing(100), 40);
  assert.equal(scanSpacingToDensity(400), 0);
  assert.equal(scanSpacingToDensity(40), 100);
  assert.ok(densityToScanSpacing(80) < densityToScanSpacing(20));
});

test("coordinate conversion round trip stays within 2m", () => {
  const gcj = wgs84ToGcj02(SAMPLE_WGS.lat, SAMPLE_WGS.lon);
  const wgs = gcj02ToWgs84(gcj.lat, gcj.lon);
  const latMeters = Math.abs(wgs.lat - SAMPLE_WGS.lat) * 111_320;
  const lonMeters =
    Math.abs(wgs.lon - SAMPLE_WGS.lon) *
    111_320 *
    Math.cos((SAMPLE_WGS.lat * Math.PI) / 180);
  assert.ok(latMeters < 2.0, `lat drift ${latMeters}`);
  assert.ok(lonMeters < 2.0, `lon drift ${lonMeters}`);
});

test("parseBoundaryText parses lat lon rows", () => {
  const points = parseBoundaryText("30.27, 120.09\n30.26, 120.10");
  assert.deepEqual(points, [
    { lat: 30.27, lon: 120.09 },
    { lat: 30.26, lon: 120.1 },
  ]);
});

test("generateBoustrophedonScan yields waypoint pairs", () => {
  const waypoints = generateBoustrophedonScan(SAMPLE_BOUNDARY_GCJ, 80, 300, 0);
  assert.ok(waypoints.length > 0);
  assert.equal(waypoints.length % 2, 0);
  assert.ok(waypoints.every((point) => point.alt_m === 80));
});

test("findNearestPolygonEdgeIndex picks the nearest boundary edge", () => {
  const index = findNearestPolygonEdgeIndex(SAMPLE_BOUNDARY_GCJ, { lat: 30.27, lon: 120.095 });
  assert.equal(index, 0);
});

test("insertVertexIntoPolygon inserts a new point after the nearest edge", () => {
  const inserted = insertVertexIntoPolygon(SAMPLE_BOUNDARY_GCJ, { lat: 30.27, lon: 120.095 });
  assert.equal(inserted.length, 5);
  assert.deepEqual(inserted[1], { lat: 30.27, lon: 120.095 });
});

test("validateFieldProfile reports derived geometry previews", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;
  field.landing.touchdown_point.lat = 30.261;
  field.landing.touchdown_point.lon = 120.095;
  field.scan.spacing_m = 200;
  field.landing.approach_alt_m = 30;
  field.landing.touchdown_point.alt_m = 0;
  const validation = validateFieldProfile(field);
  assert.equal(validation.blocking.length, 0);
  assert.ok(validation.derivedApproach);
  assert.ok(validation.derivedTakeoff);
  assert.ok(validation.scanPreview.length > 0);
});

test("exportFieldProfile closes polygon and writes WGS84", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;
  const exported = exportFieldProfile(field);
  assert.equal(exported.coordinate_system, "WGS84");
  assert.equal(exported.boundary.polygon.length, 5);
  assert.deepEqual(
    exported.boundary.polygon[0],
    exported.boundary.polygon[exported.boundary.polygon.length - 1],
  );
});

test("importFieldProfile converts WGS84 sample to internal GCJ-02 map coordinates", () => {
  const imported = importFieldProfile({
    name: "Imported Field",
    coordinate_system: "WGS84",
    boundary: {
      description: "sample",
      polygon: closePolygon([
        { lat: 30.27, lon: 120.09 },
        { lat: 30.27, lon: 120.1 },
        { lat: 30.26, lon: 120.1 },
        { lat: 30.26, lon: 120.09 },
      ]),
    },
    landing: {
      description: "landing",
      touchdown_point: { lat: 30.261, lon: 120.095, alt_m: 0 },
      heading_deg: 180,
      glide_slope_deg: 3,
      approach_alt_m: 30,
      runway_length_m: 200,
      use_do_land_start: true,
    },
    scan: {
      description: "scan",
      altitude_m: 80,
      spacing_m: 200,
      heading_deg: 0,
    },
    attack_run: {
      approach_distance_m: 200,
      exit_distance_m: 200,
      release_acceptance_radius_m: 0,
    },
    safety_buffer_m: 50,
  });
  assert.equal(imported.coordinate_system, "GCJ-02");
  assert.equal(imported.boundary.polygon.length, 4);
  assert.notEqual(imported.landing.touchdown_point.lat, 30.261);
});

test("importFieldProfile preserves GCJ-02 samples without applying another shift", () => {
  const imported = importFieldProfile({
    name: "GCJ Field",
    coordinate_system: "GCJ-02",
    boundary: {
      description: "sample",
      polygon: closePolygon(SAMPLE_BOUNDARY_GCJ),
    },
    landing: {
      description: "landing",
      touchdown_point: { lat: 30.261, lon: 120.095, alt_m: 0 },
      heading_deg: 180,
      glide_slope_deg: 3,
      approach_alt_m: 30,
      runway_length_m: 200,
      use_do_land_start: true,
    },
    scan: {
      description: "scan",
      altitude_m: 80,
      spacing_m: 200,
      heading_deg: 0,
    },
    attack_run: {
      approach_distance_m: 200,
      exit_distance_m: 200,
      release_acceptance_radius_m: 0,
    },
    safety_buffer_m: 50,
  });
  assert.equal(imported.coordinate_system, "GCJ-02");
  assert.deepEqual(imported.boundary.polygon, SAMPLE_BOUNDARY_GCJ);
  assert.equal(imported.landing.touchdown_point.lat, 30.261);
  assert.equal(imported.landing.touchdown_point.lon, 120.095);
});

test("deriveTakeoffPreview mirrors runway-aligned takeoff geometry", () => {
  const field = createDefaultFieldProfile();
  field.landing.touchdown_point = { lat: 30.261, lon: 120.095, alt_m: 0 };
  field.landing.heading_deg = 180;
  field.landing.runway_length_m = 200;
  field.scan.altitude_m = 80;
  const takeoff = deriveTakeoffPreview(field);
  assert.equal(takeoff.heading_deg, 0);
  assert.ok(takeoff.start_lat > 30.261);
  assert.ok(takeoff.climbout_lat > 30.261);
  assert.ok(takeoff.climb_angle_deg > 0);
});

test("validateFieldProfile emits advisory warnings for unsafe climb and descent", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;
  field.landing.touchdown_point = { lat: 30.261, lon: 120.095, alt_m: 0 };
  field.landing.glide_slope_deg = MAX_SAFE_GLIDE_SLOPE_DEG + 1;
  field.landing.approach_alt_m = 45;
  field.landing.runway_length_m = 120;
  field.scan.altitude_m = 40;
  const validation = validateFieldProfile(field);
  assert.equal(validation.blocking.length, 0);
  assert.ok(validation.advisory.some((message) => message.includes("descent angle")));
  assert.ok(validation.advisory.some((message) => message.includes("climb angle")));
  assert.ok(validation.derivedTakeoff.climb_angle_deg > MAX_SAFE_CLIMB_ANGLE_DEG);
});

test("generateWaypointFile emits QGC WPL mission sequence in WGS84", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;
  field.landing.touchdown_point.lat = 30.261;
  field.landing.touchdown_point.lon = 120.095;
  field.scan.spacing_m = 300;
  field.scan.altitude_m = 80;
  field.landing.approach_alt_m = 30;
  const validation = validateFieldProfile(field);

  const content = generateWaypointFile(field, validation);
  const lines = content.split("\n");
  assert.equal(lines[0], "QGC WPL 110");
  assert.equal(lines.length, validation.scanPreview.length + 7);

  const rows = lines.slice(1).map((line) => line.split("\t"));
  assert.ok(rows.every((row) => row.length === 12));
  assert.deepEqual(rows.map((row) => Number(row[3])), [
    16,
    22,
    ...validation.scanPreview.map(() => 16),
    17,
    189,
    16,
    21,
  ]);
  assert.deepEqual(rows.map((row) => Number(row[0])), rows.map((_, index) => index));
  const touchdownWgs = gcj02ToWgs84(field.landing.touchdown_point.lat, field.landing.touchdown_point.lon);
  assert.ok(Math.abs(Number(rows[0][8]) - touchdownWgs.lat) < 1e-9);
  assert.ok(Math.abs(Number(rows[0][9]) - touchdownWgs.lon) < 1e-9);
});

test("generateWaypointFile uses custom loiter point when provided", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;
  field.landing.touchdown_point.lat = 30.261;
  field.landing.touchdown_point.lon = 120.095;
  field.loiter_point = { lat: 30.265, lon: 120.095 };
  const validation = validateFieldProfile(field);

  const rows = generateWaypointFile(field, validation)
    .split("\n")
    .slice(1)
    .map((line) => line.split("\t"));
  const loiterRow = rows.find((row) => Number(row[3]) === 17);
  const loiterWgs = gcj02ToWgs84(field.loiter_point.lat, field.loiter_point.lon);
  assert.ok(Math.abs(Number(loiterRow[8]) - loiterWgs.lat) < 1e-9);
  assert.ok(Math.abs(Number(loiterRow[9]) - loiterWgs.lon) < 1e-9);
});

test("formatGeofencePoly writes closed WGS84 polygon", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;

  const lines = formatGeofencePoly(field).split("\n");
  assert.equal(Number(lines[0]), 5);
  assert.equal(lines.length, 6);
  assert.equal(lines[1], lines[5]);
  const firstWgs = gcj02ToWgs84(SAMPLE_BOUNDARY_GCJ[0].lat, SAMPLE_BOUNDARY_GCJ[0].lon);
  const [lat, lon] = lines[1].split(" ").map(Number);
  assert.ok(Math.abs(lat - firstWgs.lat) < 1e-9);
  assert.ok(Math.abs(lon - firstWgs.lon) < 1e-9);
});

test("field profile loiter point imports exports and validates", () => {
  const field = createDefaultFieldProfile();
  field.boundary.polygon = SAMPLE_BOUNDARY_GCJ;
  field.landing.touchdown_point.lat = 30.261;
  field.landing.touchdown_point.lon = 120.095;
  field.loiter_point = { lat: 30.265, lon: 120.095 };
  const exported = exportFieldProfile(field);
  const loiterWgs = gcj02ToWgs84(field.loiter_point.lat, field.loiter_point.lon);
  assert.ok(Math.abs(exported.loiter_point.lat - loiterWgs.lat) < 1e-9);
  assert.ok(Math.abs(exported.loiter_point.lon - loiterWgs.lon) < 1e-9);

  const imported = importFieldProfile(exported);
  assert.ok(Math.abs(imported.loiter_point.lat - field.loiter_point.lat) < 0.0001);
  assert.ok(Math.abs(imported.loiter_point.lon - field.loiter_point.lon) < 0.0001);

  field.loiter_point = { lat: 30.3, lon: 120.2 };
  const validation = validateFieldProfile(field);
  assert.ok(validation.blocking.some((message) => message.includes("loiter_point")));
});

test("field editor interaction tab includes loiter placement", () => {
  assert.equal(fieldEditorInteractionTab("setLoiterPoint"), FIELD_EDITOR_TAB_PLANNING);
});
test("field editor tab visibility defaults to planning and keeps planning geometry visible", () => {
  assert.deepEqual(fieldEditorPanelVisibility(undefined), {
    activeTab: FIELD_EDITOR_TAB_PLANNING,
    planning: true,
    replay: false,
  });
  assert.deepEqual(fieldEditorPanelVisibility(FIELD_EDITOR_TAB_REPLAY), {
    activeTab: FIELD_EDITOR_TAB_REPLAY,
    planning: false,
    replay: true,
  });
  assert.deepEqual(fieldEditorOverlayVisibility(FIELD_EDITOR_TAB_REPLAY), {
    activeTab: FIELD_EDITOR_TAB_REPLAY,
    planning: false,
    replay: true,
    planningGeometry: true,
    replayGeometry: true,
  });
});

test("planning-only interactions are mapped to the planning tab", () => {
  assert.equal(fieldEditorInteractionTab("idle"), null);
  assert.equal(fieldEditorInteractionTab("drawBoundary"), FIELD_EDITOR_TAB_PLANNING);
  assert.equal(fieldEditorInteractionTab("editBoundary"), FIELD_EDITOR_TAB_PLANNING);
  assert.equal(fieldEditorInteractionTab("setRunway"), FIELD_EDITOR_TAB_PLANNING);
  assert.equal(fieldEditorInteractionTab("setDropPoint"), FIELD_EDITOR_TAB_PLANNING);
});

test("parseFlightLogCsv derives replay trajectory and release metadata", () => {
  const csvText = readFileSync(path.join(FIXTURE_DIR, "mission_with_release.csv"), "utf8");
  const replay = parseFlightLogCsv(csvText);

  assert.equal(replay.sampleCount, 4);
  assert.equal(replay.releaseTimestamp, 101);
  assert.equal(replay.releaseSampleIndex, 1);
  assert.equal(replay.plannedDrop.source, "vision");
  assert.equal(replay.actualDrop.source, "vision");
  assert.ok(replay.durationS >= 3);
  assert.equal(replay.samples[0].relativeTimeS, 0);
  assert.equal(replay.samples[3].releaseTriggered, true);
});

test("parseFlightLogCsv keeps replay available without actual drop confirmation", () => {
  const csvText = readFileSync(path.join(FIXTURE_DIR, "mission_without_actual_drop.csv"), "utf8");
  const replay = parseFlightLogCsv(csvText);

  assert.equal(replay.sampleCount, 3);
  assert.equal(replay.releaseTimestamp, null);
  assert.equal(replay.releaseSampleIndex, -1);
  assert.equal(replay.plannedDrop.source, "fallback_midpoint");
  assert.equal(replay.actualDrop, null);
  assert.equal(replay.hasActualDropMetadata, true);
});

test("replay progress mapping is reversible across the sample range", () => {
  assert.equal(replayIndexFromProgress(0, 5), 0);
  assert.equal(replayIndexFromProgress(100, 5), 4);
  assert.equal(replayIndexFromProgress(49, 5), 2);
  assert.equal(replayProgressForIndex(0, 5), 0);
  assert.equal(replayProgressForIndex(4, 5), 100);
  assert.equal(replayProgressForIndex(2, 5), 50);
});
