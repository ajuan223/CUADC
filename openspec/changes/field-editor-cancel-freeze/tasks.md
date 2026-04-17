## 1. Harden interaction lifecycle

- [x] 1.1 Trace the current boundary-draw lifecycle in `src/field_editor/app.js` and identify every exit path where a cancelled rectangle draw can leave the editor stuck
- [x] 1.2 Refactor boundary-draw cleanup into an explicit, idempotent reset path that clears active handlers, closes tools, and restores idle mode when no draw result is committed
- [x] 1.3 Ensure switching to another tool or clearing overlays during an active boundary draw goes through the same recovery path without destroying previously committed geometry

## 2. Add regression coverage

- [x] 2.1 Add targeted automated coverage for cancelled or interrupted boundary drawing in field-editor tests
- [x] 2.2 Run the focused field-editor test suite covering the new recovery path

## 3. Validate in browser

- [ ] 3.1 Start the field editor, reproduce the old cancel-draw freeze path, and verify the page stays responsive after the fix
- [ ] 3.2 Exercise at least boundary redraw, runway placement, loiter placement, and clear-overlays after a cancelled draw to confirm no follow-on regression
