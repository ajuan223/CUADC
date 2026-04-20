## 1. Extend flight_log for replay data

- [x] 1.1 Add release-event and actual-drop columns to the default `FlightRecorder` header and snapshot output.
- [x] 1.2 Capture the first successful release trigger time in mission state and expose it to the recorder without breaking existing CSV consumers.
- [x] 1.3 Persist confirmed actual drop point coordinates and source into mission state so later recorder rows can include them.
- [x] 1.4 Update or add recorder-focused tests to cover flights with release, without release, and without confirmed actual drop results.

## 2. Build Field Editor post-flight replay workflow

- [x] 2.1 Add replay-mode UI controls in Field Editor for loading a historical flight log, playing, pausing, seeking, speed selection, and fitting the trajectory view.
- [x] 2.2 Implement browser-side parsing of replay-relevant `flight_log` fields and derive trajectory samples, release point timing, and actual drop result state.
- [x] 2.3 Render replay overlays on the existing map stack, including trajectory polyline, current replay aircraft marker, release indicator, and actual drop marker.
- [x] 2.4 Combine replay overlays with existing field planning overlays so operators can compare boundary, runway, scan, fallback drop point, and post-flight results together.
- [x] 2.5 Handle incomplete logs gracefully by keeping replay available when release or actual drop fields are absent and surfacing that absence in the UI.

## 3. Validate replay flow end to end

- [x] 3.1 Create or refresh representative sample replay data covering at least one mission with release and one without confirmed actual drop point.
- [x] 3.2 Add or update automated tests for replay parsing and UI state transitions in the web test suite.
- [x] 3.3 Manually verify the Field Editor replay workflow in a browser using a recorded flight log, confirming map playback and overlay alignment.
- [x] 3.4 Document any required operator workflow changes for preparing replay input artifacts if the final UI expects specific file combinations.