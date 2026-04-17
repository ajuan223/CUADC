# field-editor-layout Specification

## Purpose
TBD - created by archiving change r3-field-editor-map-selector-fixes. Update Purpose after archive.
## Requirements
### Requirement: Field editor layout SHALL keep the map fitted to the viewport
The field editor page MUST keep the map panel aligned to the browser viewport while the control panel scrolls independently.

#### Scenario: Left-side form exceeds viewport height
- **WHEN** the control panel content is taller than the viewport
- **THEN** the sidebar MUST scroll internally without pushing the map panel below the fold

#### Scenario: Operator opens the editor on a desktop viewport
- **WHEN** the editor is rendered on a wide screen
- **THEN** the layout MUST present a fixed-height two-column workspace with the map remaining visible during form scrolling

#### Scenario: Operator opens the editor on a narrow viewport
- **WHEN** the viewport width is below the stacked-layout breakpoint
- **THEN** the layout MUST stack the control panel and map in a way that still preserves a usable map height

