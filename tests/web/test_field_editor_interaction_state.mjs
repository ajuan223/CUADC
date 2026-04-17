import assert from "node:assert/strict";
import test from "node:test";

import {
  BOUNDARY_EDITOR_SYNC_EVENTS,
  attachBoundaryEditorSync,
  beginBoundaryDrawSession,
  completeBoundaryDrawSession,
  createInteractionSessionState,
  detachBoundaryEditorSync,
  resetBoundaryDrawSession,
} from "../../src/field_editor/interaction_state.mjs";

test("completed session clears active draw session", () => {
  const state = createInteractionSessionState();
  const sessionId = beginBoundaryDrawSession(state);

  assert.equal(completeBoundaryDrawSession(state, sessionId), true);
  assert.equal(state.activeBoundaryDrawSessionId, null);
});

test("stale completion does not revive or replace newer draw session", () => {
  const state = createInteractionSessionState();
  const firstSessionId = beginBoundaryDrawSession(state);
  const secondSessionId = beginBoundaryDrawSession(state);

  assert.equal(completeBoundaryDrawSession(state, firstSessionId), false);
  assert.equal(state.activeBoundaryDrawSessionId, secondSessionId);
  assert.equal(completeBoundaryDrawSession(state, secondSessionId), true);
  assert.equal(state.activeBoundaryDrawSessionId, null);
});

test("reset is idempotent for cancelled draw sessions", () => {
  const state = createInteractionSessionState();
  beginBoundaryDrawSession(state);

  resetBoundaryDrawSession(state);
  resetBoundaryDrawSession(state);

  assert.equal(state.activeBoundaryDrawSessionId, null);
});

test("new draw session can start after cancellation", () => {
  const state = createInteractionSessionState();
  beginBoundaryDrawSession(state);
  resetBoundaryDrawSession(state);

  const nextSessionId = beginBoundaryDrawSession(state);

  assert.equal(nextSessionId, 2);
  assert.equal(state.activeBoundaryDrawSessionId, 2);
});

test("polygon editor sync listeners attach once and detach cleanly", () => {
  const state = createInteractionSessionState();
  const events = [];
  const editor = {
    on(eventName, handler) {
      events.push(["on", eventName, handler]);
    },
    off(eventName, handler) {
      events.push(["off", eventName, handler]);
    },
  };
  const handler = () => {};

  assert.equal(attachBoundaryEditorSync(state, editor, handler), true);
  assert.equal(attachBoundaryEditorSync(state, editor, handler), false);
  assert.equal(detachBoundaryEditorSync(state, editor, handler), true);
  assert.equal(detachBoundaryEditorSync(state, editor, handler), false);

  assert.equal(
    events.filter(([action]) => action === "on").length,
    BOUNDARY_EDITOR_SYNC_EVENTS.length,
  );
  assert.equal(
    events.filter(([action]) => action === "off").length,
    BOUNDARY_EDITOR_SYNC_EVENTS.length,
  );
});
