## ADDED Requirements

### Requirement: Boundary drawing cancellation SHALL recover the editor
The field editor MUST return to a usable idle interaction state when an operator cancels, interrupts, or abandons an in-progress boundary rectangle draw before a polygon is committed.

#### Scenario: Operator cancels boundary drawing before completion
- **WHEN** the operator starts boundary drawing and then cancels the rectangle selection before a boundary polygon is created
- **THEN** the editor returns to idle mode
- **AND** the page continues responding to later map and form interactions
- **AND** no partial draw session remains registered as the active interaction

#### Scenario: Operator switches tools during active boundary drawing
- **WHEN** the operator starts boundary drawing and then activates a different map interaction tool before the rectangle draw completes
- **THEN** the unfinished boundary draw is cancelled
- **AND** the newly selected tool becomes active normally
- **AND** later interactions do not require a page reload to recover

### Requirement: Boundary draw teardown SHALL be idempotent
The field editor MUST tear down mouse-tool handlers, transient draw state, and editor-owned interaction flags in a way that is safe to call multiple times.

#### Scenario: Cleanup runs after an already-closed draw session
- **WHEN** the editor runs interaction cleanup for a boundary draw session that is already closed or partially cleaned up
- **THEN** cleanup completes without throwing errors
- **AND** the editor remains usable for the next interaction

### Requirement: Cancelled boundary draws SHALL preserve prior stable state
The field editor MUST NOT replace the previously committed boundary polygon or other stable map overlays when a new boundary draw is started and then cancelled before completion.

#### Scenario: Existing boundary survives a cancelled redraw
- **WHEN** the operator already has a committed boundary polygon and starts a new boundary draw but cancels it before completion
- **THEN** the previously committed boundary polygon remains available for editing and export
- **AND** the cancelled redraw does not leave behind a partial overlay
- **AND** the editor remains responsive
