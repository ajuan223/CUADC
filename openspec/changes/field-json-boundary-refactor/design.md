## Context

The current `field.json` contains a mix of Striker runtime parameters (e.g., `safety_buffer_m`, `boundary.polygon`) and planning-only parameters (e.g., `scan.spacing_m`, `landing.glide_slope_deg`). Since the Web-based Field Editor now takes full responsibility for planning and `.waypoints` generation, Striker's Python runtime no longer reads or needs these planning fields.

Keeping these fields in `field.json` creates a false assumption that modifying them will alter the UAV's flight behavior. Our goal is to strictly define the capability boundary of `field.json`, accurately classify the remaining fields, and delete the unused "ghost sections" entirely.

## Goals / Non-Goals

**Goals:**
- Delete all ghost (planning-only) fields from `FieldProfile` and `field.json`.
- Add JSONC support (inline `//` comments) so we can annotate the remaining fields as `// runtime` or `// shared`.
- Field Editor logic must adapt to output these comments and not rely on `field.json` for persistent storage of planning-only fields (they will be managed separately or via Web LocalStorage/planning.json).

**Non-Goals:**
- Refactoring the entire Field Editor logic beyond extracting the ghost fields.
- Introducing a heavyweight TOML/YAML parser. We will use simple regex-based JSONC parsing.

## Decisions

### 1. Hard Deletion of Ghost Fields
**Decision:** We will completely remove `scan.spacing_m`, `scan.heading_deg`, `scan.boundary_margin_m`, and `landing` trajectory fields (`glide_slope_deg`, `approach_alt_m`, `runway_length_m`, `use_do_land_start`) from the `FieldProfile` Pydantic model.
**Rationale:** The cleanest way to enforce a boundary is data deletion. If they are not in the model, they cannot be accidentally used.

### 2. JSONC Phase Annotation
**Decision:** We will use `//` comments in `field.json` for precise classification of the remaining fields (e.g., `// shared: boundaries`, `// runtime: fallback drop`).
**Rationale:** As requested, classifying with comments in JSON is readable and preserves the single-file simplicity for runtime context.

### 3. Python JSONC Parsing
**Decision:** Use a regex `re.sub(r'(?m)^\s*//.*$|//.*$', '', raw_json)` to strip comments before `json.loads`.
**Rationale:** Keeps the dependency tree small. Our JSON fields do not contain `//` inside string literals (e.g., URLs), so a simple regex is safe.

### 4. Field Editor Separation
**Decision:** Field Editor will handle planning fields via a separate `planning.json` or LocalStorage. `exportFieldProfile` will only export the exact schema of `FieldProfile` with appended `// runtime` or `// shared` comments.
**Rationale:** Decouples the planning data structure from the runtime context file.

## Risks / Trade-offs

- **Risk:** Existing `.waypoints` might be hard to regenerate if the planning fields are lost.
  **Mitigation:** The Field Editor will export them as a separate `planning.json` bundle during the workflow to ensure they are not lost.
- **Risk:** Python regex comment stripping is naive and might break on edge cases.
  **Mitigation:** The data in `field.json` is highly structured (floats, coordinates) without complex text payloads.
