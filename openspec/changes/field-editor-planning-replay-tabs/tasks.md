## 1. Add top-level tab structure

- [x] 1.1 Update `src/field_editor/index.html` to add distinct planning and replay tab controls while keeping the existing shared workspace shell.
- [x] 1.2 Group the sidebar DOM into planning-only and replay-only sections so each tab shows the correct controls without navigating away from the editor.
- [x] 1.3 Update `src/field_editor/styles.css` for the new tab navigation, active-state styling, and tab-scoped panel visibility.

## 2. Gate editor behavior by active tab

- [x] 2.1 Add top-level tab state in `src/field_editor/app.js` and wire tab-switch handlers that toggle the correct sidebar content inside the shared page.
- [x] 2.2 Keep planning interactions and summaries available only in the planning tab without changing existing field export and preview behavior.
- [x] 2.3 Keep replay import, playback controls, and replay summaries available only in the replay tab while preserving the existing replay data state.

## 3. Preserve shared map and overlay behavior

- [x] 3.1 Update overlay rendering in `src/field_editor/app.js` so the shared map instance survives tab switches and shows planning or replay emphasis based on the active tab.
- [x] 3.2 Ensure replay mode still overlays trajectory, planned geometry, and drop markers together for post-flight comparison.
- [x] 3.3 Ensure hidden controls cannot keep driving the wrong workflow after a tab switch, including replay playback state and planning-only actions.

## 4. Verify planning/replay tab workflow

- [x] 4.1 Add or update web logic/UI tests to cover default active tab, tab switching, and tab-scoped control availability.
- [x] 4.2 Re-run existing replay/planning automated checks and adjust fixtures or assertions only where the tab split changes expected UI structure.
- [x] 4.3 Manually verify in a browser that planning and replay share the same overall layout, switch without page navigation, and keep the map/replay workflow usable.