## ADDED Requirements

### Requirement: Isolate obsolete documents
The system SHALL isolate obsolete historical documents into an archive folder to prevent them from causing confusion.

#### Scenario: Move obsolete documents
- **WHEN** performing documentation maintenance
- **THEN** documents such as `HIL愿景.md`, `docs/user_manual_testrez.md`, and `docs/sitl_integration_results.md` are moved to `docs/archive/`
