## ADDED Requirements

### Requirement: Editor bootstrap with AMap credentials
The field editor SHALL initialize an AMap (高德地图) map instance only after the user provides the credentials required by the AMap JS API 2.0 initialization flow. The editor SHALL persist these credentials in localStorage and initialize the map centered on the Zijingang area (30.27, 120.095) at zoom level 15.

#### Scenario: First load without saved credentials
- **WHEN** the editor is opened and no AMap credentials are stored
- **THEN** the editor shows a credential form instead of an interactive map
- **AND** the map is not initialized until valid credentials are submitted

#### Scenario: Reuse saved credentials
- **WHEN** valid AMap credentials are already stored in localStorage
- **THEN** the editor initializes the map immediately without prompting again

#### Scenario: Invalid credentials or map bootstrap failure
- **WHEN** map initialization fails because the provided credentials are rejected or required map resources cannot be loaded
- **THEN** the editor shows a visible initialization error
- **AND** the user can update or clear the stored credentials and retry initialization

---

### Requirement: Schema-backed field profile editing
The editor SHALL expose editable state matching the current `FieldProfile` schema used by the Python backend. The editable fields SHALL include:

- `name`
- `description`
- `coordinate_system` (exported as `WGS84`)
- `boundary.description`
- `boundary.polygon`
- `landing.description`
- `landing.touchdown_point.lat`
- `landing.touchdown_point.lon`
- `landing.touchdown_point.alt_m`
- `landing.heading_deg`
- `landing.glide_slope_deg`
- `landing.approach_alt_m`
- `landing.runway_length_m`
- `landing.use_do_land_start`
- `scan.description`
- `scan.altitude_m`
- `scan.spacing_m`
- `scan.heading_deg`
- `loiter_point.description`
- `loiter_point.lat`
- `loiter_point.lon`
- `loiter_point.alt_m`
- `loiter_point.radius_m`
- `attack_run.approach_distance_m`
- `attack_run.exit_distance_m`
- `attack_run.release_acceptance_radius_m`
- `safety_buffer_m`

#### Scenario: Start a new field profile
- **WHEN** the user creates a new field profile in the editor
- **THEN** the editor initializes a complete in-memory state object covering the current `FieldProfile` schema
- **AND** fields with backend defaults use the same defaults as the Python model where applicable

#### Scenario: Form edits update editor state
- **WHEN** the user edits any supported numeric or text field in the sidebar form
- **THEN** the in-memory field profile state updates immediately
- **AND** any affected map previews or validation messages are recomputed

---

### Requirement: Boundary polygon drawing and editing
The editor SHALL allow users to draw, edit, and review the geofence boundary as a polygon on the map. Users SHALL be able to create a new polygon, drag vertices, and inspect the coordinate list in the form.

#### Scenario: Draw a new boundary polygon
- **WHEN** the user enters boundary drawing mode and completes a polygon on the map
- **THEN** the editor renders the polygon as the active geofence boundary
- **AND** the boundary coordinate list in editor state is updated from the drawn geometry

#### Scenario: Edit an existing boundary polygon
- **WHEN** the user selects an existing boundary polygon for editing
- **THEN** the editor enables vertex-level edits on that polygon
- **AND** dragging, adding, or removing vertices updates the rendered polygon and the coordinate list in real time

#### Scenario: Boundary export is closed
- **WHEN** the user exports a field profile with a valid boundary polygon
- **THEN** the written `boundary.polygon` is closed so that the first and last vertices are equal

#### Scenario: Boundary has too few vertices
- **WHEN** the boundary has fewer than 3 distinct vertices
- **THEN** the editor shows a blocking validation error
- **AND** export is disabled

---

### Requirement: Landing configuration with draggable runway centerline and derived approach preview
The editor SHALL allow users to define the landing runway directly on the map using a draggable runway centerline with two endpoints. The editor SHALL derive and synchronize `landing.touchdown_point`, `landing.heading_deg`, and `landing.runway_length_m` from that centerline, while still allowing numeric parameter edits for altitude, glide slope, and approach configuration. The editor SHALL also render a derived landing approach preview using the same parameter semantics as the backend landing geometry.

#### Scenario: Drag runway endpoints to define touchdown, heading, and length
- **WHEN** the user creates or drags the two runway endpoints on the map
- **THEN** the editor updates the rendered runway centerline immediately
- **AND** `landing.touchdown_point.lat/lon`, `landing.heading_deg`, and `landing.runway_length_m` in editor state are recomputed from the centerline geometry

#### Scenario: Edit landing numeric parameters while keeping runway visualization
- **WHEN** the user changes `glide_slope_deg`, `approach_alt_m`, or touchdown altitude in the form
- **THEN** the editor keeps the runway centerline visible
- **AND** recomputes any derived landing previews using the current runway geometry and numeric values

#### Scenario: Show derived landing approach preview
- **WHEN** runway geometry, touchdown altitude, `glide_slope_deg`, and `approach_alt_m` together define a valid derived approach
- **THEN** the editor shows the derived approach point and approach segment on the map
- **AND** the preview uses the same reverse-heading and glide-slope distance semantics as the backend

#### Scenario: Derived landing approach is invalid
- **WHEN** `approach_alt_m` is not above touchdown altitude, or `glide_slope_deg` does not produce a valid positive descent geometry, or the derived approach point falls outside the geofence
- **THEN** the editor shows a blocking validation error describing the landing geometry problem
- **AND** export is disabled until the problem is corrected

#### Scenario: Runway touchdown point outside boundary
- **WHEN** the runway touchdown point derived from the centerline is outside the boundary polygon
- **THEN** the editor shows a blocking validation error for `landing.touchdown_point`
- **AND** export is disabled

---

### Requirement: Loiter point configuration with radius preview
The editor SHALL allow users to place and edit the loiter point and radius on the map. The editor SHALL render the loiter center as a marker and the loiter radius as a circle.

#### Scenario: Place or drag loiter point
- **WHEN** the user places or drags the loiter point marker on the map
- **THEN** the editor updates `loiter_point.lat/lon`
- **AND** redraws the loiter circle using the current radius

#### Scenario: Update loiter radius
- **WHEN** the user changes `loiter_point.radius_m`
- **THEN** the loiter circle radius on the map updates immediately

#### Scenario: Loiter center outside boundary
- **WHEN** the loiter point center is outside the boundary polygon
- **THEN** the editor shows a blocking validation error for `loiter_point`
- **AND** export is disabled

#### Scenario: Loiter circle crosses boundary
- **WHEN** the loiter point center is inside the boundary but the rendered loiter circle extends outside the boundary
- **THEN** the editor shows an advisory warning
- **AND** the warning does not by itself block export

---

### Requirement: Scan parameter editing with density control and boustrophedon preview
The editor SHALL allow users to edit scan parameters and preview the generated boustrophedon scan path on the map. The UI SHALL express scan density directly, while internally mapping that control to `scan.spacing_m`. The preview SHALL follow the same parameter semantics as the backend scan generation logic.

#### Scenario: Render scan preview from valid inputs
- **WHEN** the boundary polygon and `scan.altitude_m`, scan density control, and `scan.heading_deg` are all defined with valid values
- **THEN** the editor renders the generated scan path as a polyline on the map

#### Scenario: Update scan preview on density change
- **WHEN** the user changes the scan density control
- **THEN** the editor updates the underlying `scan.spacing_m`
- **AND** the scan preview is recomputed and redrawn immediately

#### Scenario: Density control reflects spacing semantics
- **WHEN** the user moves the density control toward “denser”
- **THEN** the resulting `scan.spacing_m` becomes smaller
- **AND** the visible scan lines become more closely spaced

#### Scenario: Invalid scan spacing
- **WHEN** `scan.spacing_m` is zero or negative
- **THEN** the editor shows a blocking validation error
- **AND** export is disabled until the spacing is corrected

---

### Requirement: Attack run parameter editing
The editor SHALL allow users to edit and preserve `attack_run.approach_distance_m`, `attack_run.exit_distance_m`, and `attack_run.release_acceptance_radius_m` as part of the field profile.

#### Scenario: Edit attack run parameters
- **WHEN** the user changes attack run numeric parameters in the form
- **THEN** the editor updates the in-memory `attack_run` object
- **AND** the new values are included in subsequent exports

#### Scenario: Explain runtime-dependent attack geometry
- **WHEN** the user reviews the attack run section
- **THEN** the editor shows that these parameters are stored field facts
- **AND** it does not claim to preview the final runtime attack route when runtime inputs are unavailable

---

### Requirement: Import existing field profiles
The editor SHALL allow users to import an existing `field.json` file, validate its structure, convert coordinates for map display, and populate the form and overlays from the imported data.

#### Scenario: Import a valid field profile
- **WHEN** the user selects a valid `field.json`
- **THEN** the editor populates all supported form fields from that file
- **AND** renders the boundary, touchdown marker, derived landing preview, loiter circle, and scan preview
- **AND** pans or fits the map to the imported field geometry

#### Scenario: Import invalid JSON or wrong schema
- **WHEN** the selected file is not valid JSON or does not match the expected `FieldProfile` structure
- **THEN** the editor shows an import error
- **AND** it does not replace the current editor state with partial invalid data

#### Scenario: Import WGS84 data for map display
- **WHEN** a valid `field.json` is imported
- **THEN** the editor converts WGS84 coordinates into the map display coordinate system before rendering overlays

---

### Requirement: Export valid field profiles to JSON
The editor SHALL export the current field profile as a `field.json` file that is structurally compatible with the Python backend `FieldProfile` model.

#### Scenario: Export valid field profile
- **WHEN** all blocking validations pass
- **THEN** the editor enables JSON export
- **AND** exporting writes a `field.json` that includes the current `FieldProfile` fields, including `attack_run`

#### Scenario: Export uses WGS84 coordinates
- **WHEN** the user exports a field profile
- **THEN** all geographic coordinates in the written file are converted from map coordinates to WGS84
- **AND** `coordinate_system` is written as `WGS84`

#### Scenario: Export blocked by validation errors
- **WHEN** one or more blocking validation errors exist
- **THEN** export remains disabled
- **AND** the editor lists the reasons that must be fixed before export

#### Scenario: Exported file passes backend validation
- **WHEN** the exported `field.json` is loaded by the Python backend
- **THEN** `FieldProfile.model_validate(json_data)` succeeds without schema or geofence validation errors

---

### Requirement: Validation reporting distinguishes blocking and advisory issues
The editor SHALL present validation output in a way that distinguishes export-blocking errors from advisory map-quality warnings.

#### Scenario: Blocking validation affects export
- **WHEN** a blocking validation error is present
- **THEN** the editor renders it in the blocking error area
- **AND** export is disabled

#### Scenario: Advisory warning does not affect export
- **WHEN** only advisory warnings are present and no blocking validation errors exist
- **THEN** the editor still allows export
- **AND** the warnings remain visible to the user for review
