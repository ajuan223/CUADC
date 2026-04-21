import { createDefaultFieldProfile, exportFieldProfile } from "../../src/field_editor/logic.mjs";

const field = createDefaultFieldProfile();
field.name = "Generated Sample";
field.boundary.description = "Generated boundary";
field.boundary.polygon = [
  { lat: 30.27, lon: 120.09 },
  { lat: 30.27, lon: 120.1 },
  { lat: 30.26, lon: 120.1 },
  { lat: 30.26, lon: 120.09 },
];
field.landing.description = "Landing";
field.landing.touchdown_point = { lat: 30.261, lon: 120.095, alt_m: 0.0 };
field.landing.heading_deg = 180.0;
field.landing.glide_slope_deg = 3.0;
field.landing.approach_alt_m = 30.0;
field.scan.description = "Scan";
field.scan.altitude_m = 80.0;
field.scan.spacing_m = 200.0;
field.scan.heading_deg = 0.0;
field.attack_run.approach_distance_m = 200.0;
field.attack_run.exit_distance_m = 200.0;
field.attack_run.release_acceptance_radius_m = 0.0;
field.safety_buffer_m = 50.0;

process.stdout.write(`${exportFieldProfile(field)}\n`);
