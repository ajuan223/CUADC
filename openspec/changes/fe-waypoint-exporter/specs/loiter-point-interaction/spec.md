## ADDED Requirements

### Requirement: Default loiter point at last scan waypoint
When `fieldProfile.loiter_point` is `null` or absent, the LOITER_UNLIM waypoint in the generated mission SHALL use the position of the last scan waypoint from `scanPreview`.

#### Scenario: Default loiter point
- **WHEN** `loiter_point` is null and scanPreview has waypoints
- **THEN** the LOITER_UNLIM mission item SHALL be placed at the last scanPreview point's WGS84 coordinates

### Requirement: Custom loiter point via map interaction
The system SHALL provide a "设置盘旋点" map interaction mode that allows the user to click the map to set a custom loiter point position. The loiter point SHALL be stored in `fieldProfile.loiter_point` as `{lat, lon}`.

#### Scenario: Set custom loiter point
- **WHEN** user activates "设置盘旋点" mode and clicks on the map
- **THEN** `fieldProfile.loiter_point` SHALL be set to the clicked GCJ-02 coordinate and a marker SHALL appear on the map

#### Scenario: Drag loiter point
- **WHEN** user drags the loiter point marker to a new position
- **THEN** `fieldProfile.loiter_point` SHALL update to the new GCJ-02 coordinate

### Requirement: Loiter point validation
When `fieldProfile.loiter_point` is non-null and the boundary polygon has 3+ vertices, `validateFieldProfile()` SHALL check that the loiter point is inside the geofence boundary.

#### Scenario: Loiter point outside geofence
- **WHEN** the custom loiter point is outside the boundary polygon
- **THEN** a blocking validation error SHALL be reported

#### Scenario: Loiter point inside geofence
- **WHEN** the custom loiter point is inside the boundary polygon
- **THEN** no blocking error SHALL be reported for the loiter point

### Requirement: Loiter point overlay rendering
A map marker labeled "盘旋等待点" SHALL be rendered when `fieldProfile.loiter_point` is non-null. The marker SHALL be draggable.

#### Scenario: Loiter marker visibility
- **WHEN** `loiter_point` is set (non-null)
- **THEN** a draggable marker SHALL appear at the loiter point coordinates on the map

#### Scenario: No loiter marker when default
- **WHEN** `loiter_point` is null (using default)
- **THEN** no dedicated loiter marker SHALL be shown (the last scan waypoint is the implicit loiter)

### Requirement: Loiter point export/import in field.json
The `loiter_point` field SHALL be included in `exportFieldProfile()` (with GCJ-02→WGS84 conversion) and parsed in `importFieldProfile()` (with WGS84→GCJ-02 conversion when source is WGS84). The field is optional; missing values default to `null`.

#### Scenario: Export with custom loiter point
- **WHEN** exporting field.json with a non-null loiter_point
- **THEN** the loiter_point coordinates SHALL be GCJ-02→WGS84 converted in the output

#### Scenario: Import WGS84 with loiter point
- **WHEN** importing a field.json (WGS84) that includes loiter_point
- **THEN** the loiter_point coordinates SHALL be WGS84→GCJ-02 converted
