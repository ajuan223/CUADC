## ADDED Requirements

### Requirement: JSONC support for configuration files
The system SHALL support parsing JSON configuration files that include JavaScript-style single-line comments (`//`) at the end of lines or on their own lines.

#### Scenario: Stripping comments before parsing
- **WHEN** a `field.json` file containing `// runtime` or `// shared` comments is passed to the loader
- **THEN** the loader MUST strip all comments via regex and successfully parse the JSON payload without raising a `json.decoder.JSONDecodeError`

### Requirement: Phase annotations on export
The Field Editor SHALL inject phase annotation comments (e.g., `// [runtime]`, `// [shared]`) into the serialized JSON string when exporting `field.json`.

#### Scenario: Appending comments on download
- **WHEN** the user clicks "Export field.json" in the Field Editor
- **THEN** the downloaded blob is a JSONC file containing phase annotations mapping exactly to the consumption capability boundaries
