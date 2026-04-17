## Why

The field editor still has a fatal interaction bug: if the operator starts boundary rectangle selection and then cancels it, the page can become permanently unresponsive and stop reacting to further input. This blocks real use of the editor because one aborted selection can effectively force a page reload and risks losing in-browser edits.

## What Changes

- Fix the boundary selection cancellation flow so aborting an in-progress rectangle draw always returns the editor to a clean idle state.
- Ensure map tools, transient handlers, and editor state are torn down consistently when a selection is cancelled, replaced, or interrupted.
- Prevent the UI from entering a stuck mode where later clicks, drags, or tool activations no longer respond.
- Add coverage for the cancel-after-start interaction so the freeze regression is caught automatically.

## Capabilities

### New Capabilities
- `field-editor-interaction-recovery`: The field editor keeps responding after an operator cancels or interrupts boundary drawing, and all map interaction modes recover to a usable idle state.

### Modified Capabilities
- None.

## Impact

- Affected areas: `src/field_editor/` map interaction and state-management logic
- Test impact: `tests/web/` and any focused field-editor interaction coverage
- Operator impact: cancelling a boundary draw no longer requires reloading the page or losing unsaved changes
