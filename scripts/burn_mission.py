#!/usr/bin/env python3
"""Generate a preburned QGC waypoint mission for SITL testing.

The helper reuses the field editor's validated procedural mission exporter by
searching a small planning-parameter grid (scan heading/spacing, landing
approach geometry) against the target field profile until it finds a mission
that fits the current field boundary.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def generate_waypoints(output_path: Path, field: str) -> dict[str, object]:
    """Generate a preburned mission and return metadata dict with takeoff heading."""
    project_root = Path(__file__).resolve().parent.parent
    field_file = project_root / "data" / "fields" / field / "field.json"
    logic_file = project_root / "src" / "field_editor" / "logic.mjs"

    if not field_file.exists():
        raise FileNotFoundError(f"Field profile not found: {field_file}")
    if not logic_file.exists():
        raise FileNotFoundError(f"Field editor logic not found: {logic_file}")

    node_script = r"""
import fs from 'node:fs';

const logicModule = await import(process.argv[1]);
const {
  importFieldProfile,
  validateFieldProfile,
  generateWaypointFile,
  haversineDistance,
  bearingBetweenPoints,
} = logicModule;
const fieldFile = process.argv[2];
const outputFile = process.argv[3];
const text = fs.readFileSync(fieldFile, 'utf8').replace(/^\s*\/\/.*$|\/\/.*$/gm, '');
const raw = JSON.parse(text);

const headings = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165];
const spacings = [40, 50, 60, 80, 100];
const runwayLengths = [180, 200, 220, 250];
const glideSlopes = [4, 5, 6, 7, 8];
const approachAlts = [8, 10, 12, 15];

function headingDeltaDeg(left, right) {
  return Math.abs((((left - right) + 540.0) % 360.0) - 180.0);
}

function scoreCandidate(field, validation, params) {
  const climbAngle = validation.derivedTakeoff?.climb_angle_deg ?? Number.POSITIVE_INFINITY;
  const approachDistance = validation.derivedApproach?.distance_m ?? Number.POSITIVE_INFINITY;
  const scanCount = validation.scanPreview.length;
  const descentAdvisory = validation.advisory.some((message) => message.includes('descent angle'));
  const scanLegs = [];
  for (let index = 1; index < validation.scanPreview.length; index += 1) {
    const previous = validation.scanPreview[index - 1];
    const current = validation.scanPreview[index];
    scanLegs.push(haversineDistance(previous.lat, previous.lon, current.lat, current.lon));
  }
  const minLeg = scanLegs.length ? Math.min(...scanLegs) : 0.0;
  const avgLeg = scanLegs.length
    ? scanLegs.reduce((sum, leg) => sum + leg, 0.0) / scanLegs.length
    : 0.0;
  const firstBearing = validation.scanPreview.length
    ? bearingBetweenPoints(field.landing.touchdown_point, validation.scanPreview[0])
    : validation.derivedTakeoff?.heading_deg ?? 0.0;
  const firstTurnDelta = headingDeltaDeg(firstBearing, validation.derivedTakeoff?.heading_deg ?? firstBearing);

  const climbPenalty = Math.abs(climbAngle - 10.0) * 5.0 + Math.max(0, climbAngle - 12.0) * 200.0;
  const approachPenalty =
    Math.abs(approachDistance - 100.0) * 0.5 +
    Math.max(0, 70.0 - approachDistance) * 50.0 +
    Math.max(0, approachDistance - 180.0) * 5.0;
  const shortLegPenalty = Math.max(0, 50.0 - minLeg) * 25.0;
  const averageLegPenalty = Math.max(0, 80.0 - avgLeg) * 4.0;
  const turnPenalty = firstTurnDelta * 2.0;
  const advisoryPenalty = descentAdvisory ? 40.0 : 0.0;
  const densityPenalty = Math.max(0, scanCount - 10) * 20.0;
  const scanBonus = Math.min(scanCount, 10) * 8.0;
  return (
    scanBonus
    - climbPenalty
    - approachPenalty
    - shortLegPenalty
    - averageLegPenalty
    - turnPenalty
    - advisoryPenalty
    - densityPenalty
  );
}

let best = null;
for (const heading of headings) {
  for (const spacing of spacings) {
    for (const runwayLength of runwayLengths) {
      for (const glideSlope of glideSlopes) {
        for (const approachAlt of approachAlts) {
          const field = importFieldProfile(raw);
          field.scan.heading_deg = heading;
          field.scan.spacing_m = spacing;
          field.scan.boundary_margin_m = 100.0;
          field.landing.runway_length_m = runwayLength;
          field.landing.glide_slope_deg = glideSlope;
          field.landing.approach_alt_m = approachAlt;
          const validation = validateFieldProfile(field);
          if (
            validation.blocking.length
            || validation.scanPreview.length === 0
            || !validation.derivedApproach
            || !validation.derivedTakeoff
          ) {
            continue;
          }
          const score = scoreCandidate(field, validation, { heading, spacing, runwayLength, glideSlope, approachAlt });
          if (!best || score > best.score) {
            best = {
              score,
              field,
              validation,
              params: { heading, spacing, runwayLength, glideSlope, approachAlt },
            };
          }
        }
      }
    }
  }
}

if (!best) {
  throw new Error(`No valid procedural mission candidate found for ${fieldFile}`);
}

const mission = generateWaypointFile(best.field, best.validation);
fs.writeFileSync(outputFile, `${mission}\n`, 'utf8');
const touchdown = best.field.landing.touchdown_point;
const firstScan = best.validation.scanPreview[0];
const takeoffHeadingDeg = firstScan
  ? bearingBetweenPoints(touchdown, firstScan)
  : (best.field.landing.heading_deg + 180.0) % 360.0;
console.log(JSON.stringify({
  field: raw.name,
  output: outputFile,
  selected: best.params,
  scanCount: best.validation.scanPreview.length,
  approachDistanceM: best.validation.derivedApproach.distance_m,
  climbAngleDeg: best.validation.derivedTakeoff.climb_angle_deg,
  takeoffHeadingDeg,
  advisory: best.validation.advisory,
}, null, 2));
"""

    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            node_script,
            str(logic_file),
            str(field_file),
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stderr.strip():
        print(result.stderr.strip())
    if result.stdout.strip():
        print(result.stdout.strip())
        import json

        return dict(json.loads(result.stdout.strip()))
    return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", default="test_mission.waypoints")
    parser.add_argument("--field", required=True)
    parser.add_argument("--takeoff-heading-output", default=None,
                        help="File path to write the computed takeoff heading")
    args = parser.parse_args()
    meta = generate_waypoints(Path(args.output), args.field)
    if args.takeoff_heading_output and "takeoffHeadingDeg" in meta:
        Path(args.takeoff_heading_output).write_text(
            str(meta["takeoffHeadingDeg"]), encoding="utf-8"
        )
