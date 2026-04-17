## 1. Runtime Schema And Samples

- [x] 1.1 Remove `loiter_point` from `src/striker/config/field_profile.py` and update geofence validation accordingly.
- [x] 1.2 Update active `data/fields/*/field.json` samples to remove `loiter_point` while keeping the remaining mission fields valid.
- [x] 1.3 Update `tests/unit/test_field_profile.py` fixtures and assertions to match the new field profile schema.

## 2. Field Editor Contract

- [x] 2.1 Remove `loiter_point` defaults, import requirements, and import/export coordinate conversion from `src/field_editor/logic.mjs`.
- [x] 2.2 Update field editor web tests and sample generators so exported/imported payloads no longer include `loiter_point`.

## 3. Public Configuration And Docs

- [x] 3.1 Remove deprecated loiter/rescan/forced-strike settings from `config.example.json` and `.env.example`.
- [x] 3.2 Update operator-facing docs and field-profile documentation so the standard mission flow no longer mentions loiter as an active mission element.

## 4. Verification

- [x] 4.1 Re-run targeted repository searches to confirm active runtime/config/editor paths no longer require `loiter_point` or loiter/rescan mission settings.
- [x] 4.2 Run focused tests covering field profile loading and field editor logic after the schema cleanup.
