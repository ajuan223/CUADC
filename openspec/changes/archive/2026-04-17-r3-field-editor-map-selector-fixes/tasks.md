## 1. Spec and geometry alignment

- [x] 1.1 Mirror the current Python mission-geometry assumptions in the field editor planning summary
- [x] 1.2 Respect imported `coordinate_system` metadata so GCJ-02 files are not double-shifted before export

## 2. UI and interaction fixes

- [x] 2.1 Refactor the layout so the sidebar scrolls independently and the map remains viewport-stable
- [x] 2.2 Add basemap switching for standard, satellite, and terrain-oriented views
- [x] 2.3 Replace sticky boundary drawing with a rectangle-first selection flow plus polygon refinement
- [x] 2.4 Reset map interactions cleanly when switching tools

## 3. Validation and regression coverage

- [x] 3.1 Add or update field-editor logic tests for coordinate handling and derived planning outputs
- [x] 3.2 Run targeted field-editor/editor-export tests after implementation
