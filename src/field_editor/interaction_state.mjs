export const BOUNDARY_EDITOR_SYNC_EVENTS = ["addnode", "removenode", "adjust", "move", "add", "end"];

export function createInteractionSessionState() {
  return {
    boundaryDrawSessionId: 0,
    activeBoundaryDrawSessionId: null,
    boundaryEditorSyncAttached: false,
  };
}

export function beginBoundaryDrawSession(state) {
  state.boundaryDrawSessionId += 1;
  state.activeBoundaryDrawSessionId = state.boundaryDrawSessionId;
  return state.activeBoundaryDrawSessionId;
}

export function completeBoundaryDrawSession(state, sessionId) {
  if (state.activeBoundaryDrawSessionId !== sessionId) {
    return false;
  }
  state.activeBoundaryDrawSessionId = null;
  return true;
}

export function resetBoundaryDrawSession(state) {
  state.activeBoundaryDrawSessionId = null;
}

export function attachBoundaryEditorSync(state, editor, handler) {
  if (state.boundaryEditorSyncAttached) {
    return false;
  }
  for (const eventName of BOUNDARY_EDITOR_SYNC_EVENTS) {
    editor.on?.(eventName, handler);
  }
  state.boundaryEditorSyncAttached = true;
  return true;
}

export function detachBoundaryEditorSync(state, editor, handler) {
  if (!state.boundaryEditorSyncAttached) {
    return false;
  }
  for (const eventName of BOUNDARY_EDITOR_SYNC_EVENTS) {
    editor.off?.(eventName, handler);
  }
  state.boundaryEditorSyncAttached = false;
  return true;
}
