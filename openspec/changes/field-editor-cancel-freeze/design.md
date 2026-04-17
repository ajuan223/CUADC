## Context

The field editor in `src/field_editor/app.js` manages all AMap interaction modes through shared mutable state: `appState.interactionMode`, `mapState.mouseTool`, `mapState.drawHandler`, and `mapState.polygonEditor`. Boundary drawing currently starts `MouseTool.rectangle()` and relies on the `draw` event to restore the editor to a stable state. If the user aborts rectangle drawing before `draw` fires, the code has no explicit cancel or recovery path, so the page can remain stuck in `drawBoundary` mode with a half-closed tool lifecycle and blocked follow-up interactions.

This is a focused frontend interaction bug rather than a broad architecture change, but it still benefits from a short design because the fix must define one consistent lifecycle for starting, cancelling, interrupting, and replacing map tools. The editor is buildless, plain JS, and tightly bound to AMap runtime objects, so the safest fix is to harden the existing state machine instead of introducing a framework or abstraction layer.

## Goals / Non-Goals

**Goals:**
- Guarantee that cancelling or interrupting boundary rectangle drawing always returns the editor to a usable idle state.
- Centralize cleanup for `MouseTool`, transient draw handlers, and polygon-editor state so one aborted interaction cannot poison later ones.
- Ensure switching to another tool while a draw is active is treated as a cancellation and leaves the page responsive.
- Add regression coverage for the interaction-recovery path around cancelled boundary drawing.

**Non-Goals:**
- Reworking unrelated field-editor geometry, import/export, or layout behavior.
- Replacing AMap or changing the overall buildless frontend structure.
- Adding new operator-visible tools beyond what is required to recover safely from cancellation.

## Decisions

- Treat boundary drawing as an explicit lifecycle with start, finish, and cancel/reset transitions instead of assuming every draw attempt ends with a successful `draw` event.
  - Alternative considered: only add more defensive null checks around the existing `draw` callback. Rejected because the freeze is caused by a missing lifecycle transition, not by one missing guard.
- Add a dedicated interaction-reset helper that clears the active mouse tool, unregisters the current draw handler, closes the polygon editor, resets mode-specific transient state, and updates the interaction mode back to idle.
  - Alternative considered: continue calling `closeActiveMapTools()` opportunistically from each button handler. Rejected because it does not model cancellation clearly and is easy to bypass when an interaction ends abnormally.
- Detect cancellation or interruption from more than one path: explicit user cancellation, map-tool replacement, and any aborted draw that leaves the editor in `drawBoundary` without a resulting overlay.
  - Alternative considered: rely on AMap to always emit a uniform cancel event. Rejected because the current bug suggests the runtime contract is not sufficient on its own for robust recovery.
- Keep the fix local to `src/field_editor/app.js` and cover the state transitions with targeted tests around extracted logic or integration-facing helpers where possible.
  - Alternative considered: defer testing because AMap browser interactions are awkward to automate. Rejected because this is a regression-prone UI state bug and needs executable coverage.

## Risks / Trade-offs

- [AMap cancellation semantics differ across versions or user gestures] → Build recovery around our own reset path and call it whenever a draw session ends unexpectedly, instead of depending on one vendor event.
- [Aggressive cleanup closes tools the operator wanted to keep open] → Limit the new reset behavior to boundary-draw lifecycle transitions and explicit tool switches.
- [Regression tests cannot exercise full browser map behavior] → Cover the internal interaction-state transitions directly and keep any browser-facing test narrow and deterministic.

## Migration Plan

1. Refactor field-editor interaction cleanup so boundary drawing has a single reset path.
2. Update boundary-draw start/cancel/switch logic to call that reset path on every exit condition.
3. Add targeted regression coverage for cancelled boundary drawing.
4. Validate the field editor manually in browser by starting a boundary draw, cancelling it, and then exercising the other tools.

## Open Questions

- Which AMap event or observable state best signals an aborted rectangle draw in the current runtime version.
- Whether the UI should expose an explicit cancel action or rely only on implicit recovery when the operator switches tools or aborts the drag.
