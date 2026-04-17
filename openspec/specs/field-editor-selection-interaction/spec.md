# field-editor-selection-interaction Specification

## Purpose
TBD - created by archiving change r3-field-editor-map-selector-fixes. Update Purpose after archive.
## Requirements
### Requirement: Boundary selection SHALL use a deterministic rectangle-first workflow
The field editor MUST support reliable rectangle-based boundary creation and MUST translate the result into the editor's polygon model for later refinement.

#### Scenario: Operator draws a new boundary rectangle
- **WHEN** the operator enters boundary-selection mode and completes a rectangle drag on the map
- **THEN** the editor MUST convert the resulting rectangle bounds into a four-corner polygon and update the field profile boundary

#### Scenario: Operator refines the rectangle-derived boundary
- **WHEN** a boundary polygon already exists and the operator enters boundary edit mode
- **THEN** the editor MUST open polygon editing on that polygon instead of leaving the rectangle tool active

### Requirement: Field editor interactions SHALL reset cleanly between modes
The field editor MUST close incompatible map tools before entering a new interaction mode so the cursor and editor state cannot remain stuck.

#### Scenario: Operator switches from boundary selection to runway placement
- **WHEN** the operator activates runway placement while a boundary drawing or polygon editing interaction is active
- **THEN** the editor MUST close the previous interaction before arming runway placement

#### Scenario: Boundary drawing completes
- **WHEN** the rectangle draw operation fires its completion event
- **THEN** the editor MUST close the draw tool, clear transient interaction state, and return to a stable follow-up mode

