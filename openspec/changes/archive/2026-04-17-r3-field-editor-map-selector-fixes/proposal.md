## Why

The current field editor is not usable for real mission planning: the page layout stretches with the left-side form instead of fitting the browser viewport, the rectangle selector behaves unreliably, the displayed coordinates do not match Mission Planner after export, and the tool does not yet compute the approach/landing outputs operators need while selecting a field. These issues block trust in both the UI and the generated planning data, so they need to be fixed together as one field-editor workflow correction.

## What Changes

- Redesign the field editor layout so the browser viewport remains map-sized while the left-side control area scrolls internally as one large panel.
- Add selectable AMap base styles for at least satellite and terrain-oriented views.
- Correct the north/south coordinate offset between the web editor display/export path and Mission Planner.
- Replace or rework the rectangle selection interaction so it does not stick to the cursor, freeze, or enter inconsistent states.
- Extend the selector workflow to calculate planning outputs in real time, including approach distance and selectable landing point / touchdown-related outputs based on the project algorithm.
- Show explicit safety warnings when predicted descent angle or climb angle is unsafe.

## Capabilities

### New Capabilities
- `field-editor-planning-workflow`: Interactive field selection workflow that continuously derives planning outputs, lets the operator choose landing-related points, and surfaces unsafe climb/descent conditions during editing.

### Modified Capabilities
- `field-editor-layout`: The field editor page layout and scrolling behavior must keep the map fitted to the browser viewport while the left control panel scrolls independently.
- `field-editor-map-basemap`: The field editor map must support operator-selectable satellite and terrain-style basemaps.
- `field-editor-coordinate-consistency`: Field editor coordinates and exported outputs must match the geospatial position consumed by Mission Planner without systematic north/south offset.
- `field-editor-selection-interaction`: Rectangle selection must behave deterministically without sticky pointer capture, freezes, or ambiguous drag state.

## Impact

- Affected areas: `src/field_editor/` frontend layout and interaction code, map integration, coordinate conversion/export logic, and related tests in `tests/web/` or field-editor test coverage
- External integration impact: output compatibility with Mission Planner geospatial interpretation
- Operator impact: field selection becomes trustworthy, scrollable, viewport-stable, and immediately useful for planning approach and landing geometry
