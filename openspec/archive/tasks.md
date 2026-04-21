## 1. Documentation & Policy Updates

- [x] 1.1 Update `.agent/skills/field-profile-rules/SKILL.md` to document the strict boundary (deletion of ghost fields) and the JSONC comment syntax for `// runtime` and `// shared`.

## 2. Python Backend Core Deletions & JSONC Parsing

- [x] 2.1 Update `src/striker/config/field_profile.py`: Delete `scan.spacing_m`, `scan.heading_deg`, `scan.boundary_margin_m`, `landing.glide_slope_deg`, `landing.approach_alt_m`, `landing.runway_length_m`, and `landing.use_do_land_start` from `FieldProfile` Pydantic models.
- [x] 2.2 Update `src/striker/config/field_profile.py`: Remove `_validate_landing_approach_inside_geofence()` since `FieldProfile` no longer has the approach parameters to compute this.
- [x] 2.3 Update `src/striker/config/field_profile.py`: Update `load_field_profile` to use regex to strip `//` inline and block comments from the raw string before `json.loads`.
- [x] 2.4 Run backend tests to verify parsing works, and any remaining tests relying on deleted fields are updated or removed.

## 3. Field Editor Output Separation

- [x] 3.1 Update `src/field_editor/logic.mjs`: Create a separate mechanism/state bundle for the "ghost fields" (planning parameters).
- [x] 3.2 Update `src/field_editor/logic.mjs`: Modify `exportFieldProfile` to generate a lean `field.json` (excluding deleted planning fields) and append `// [planning-only]`, `// [shared]`, and `// [runtime]` phase comments to the corresponding JSON strings.
- [x] 3.3 Update `src/field_editor/app.js`: Ensure the frontend still functions (generating waypoints properly) using the planning parameters stored in local state/UI instead of assuming they are always in `field.json`.

## 4. Existing Data Migration

- [x] 4.1 Update `data/fields/zjg2/field.json` (and others): Manually strip the ghost fields, and add the new JSONC phase annotations.
- [x] 4.2 Run SITL with the updated `zjg2` field to verify Striker boots and executes the `guided_strike` correctly with the lean profile.
