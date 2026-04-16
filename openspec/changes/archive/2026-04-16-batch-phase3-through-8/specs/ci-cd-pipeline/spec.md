# ci-cd-pipeline

## Requirements

- REQ-CI-001: GitHub Actions workflow with multi-stage pipeline
- REQ-CI-002: Stage 1: ruff check lint
- REQ-CI-003: Stage 2: mypy --strict type check
- REQ-CI-004: Stage 3: pytest unit tests (no SITL)
- REQ-CI-005: Stage 4: Registry lint + pkg version check scripts
- REQ-CI-006: Stage 5: SITL integration tests (scheduled, not on every push)
- REQ-CI-007: Python 3.13 in CI environment
- REQ-CI-008: uv for dependency installation in CI
