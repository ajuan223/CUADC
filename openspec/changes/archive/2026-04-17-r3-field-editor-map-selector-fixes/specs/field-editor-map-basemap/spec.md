## ADDED Requirements

### Requirement: Field editor basemap control SHALL support operator-selectable planning views
The field editor MUST let the operator switch between standard, satellite, and terrain-oriented map views using supported AMap APIs.

#### Scenario: Satellite view is selected
- **WHEN** the operator chooses the satellite basemap option
- **THEN** the map MUST render satellite imagery with the associated road-network overlay when supported by AMap

#### Scenario: Terrain-oriented view is selected
- **WHEN** the operator chooses the terrain-oriented basemap option
- **THEN** the editor MUST initialize the map in a terrain-capable mode supported by the current AMap JavaScript API documentation

#### Scenario: Basemap mode changes after overlays exist
- **WHEN** the operator changes the basemap mode after creating or editing field geometry
- **THEN** the editor MUST preserve the current field profile state and redraw the overlays on the reinitialized map
