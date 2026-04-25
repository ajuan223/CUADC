## ADDED Requirements

### Requirement: Update user manual
The user manual SHALL reflect the latest v0.0.3 changes including `cruise_speed_mps`, `boundary_margin_m`, `fallback_drop_point`, and the 3-tier fallback logic.

#### Scenario: Update user manual configuration
- **WHEN** a user refers to `docs/user_manual.md`
- **THEN** they see accurate configuration keys and updated mission logic.

### Requirement: Update data fields README
The field profiles documentation SHALL contain the correct JSON schema definition matching the current `field.json` fields.

#### Scenario: Update data fields README
- **WHEN** a user refers to `data/fields/README.md`
- **THEN** they see `fallback_drop_point` and `boundary_margin_m` properly explained.

### Requirement: Update architecture vision
The top-level `init愿景.md` SHALL have its fallback logic description synchronized with actual code priorities.

#### Scenario: Update init vision fallback logic
- **WHEN** a user reads `init愿景.md`'s vision section
- **THEN** they understand that vision is prioritized first, then `fallback_drop_point`, then centroid.
