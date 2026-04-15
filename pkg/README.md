# pkg/ — Vendor / Frozen Packages

This directory is the uv workspace member area for vendor packages.

## Rules

1. Each subdirectory is a separate uv workspace package: `pkg/{name}/`
2. Every package must have its own `pyproject.toml` with `[project] name + version`
3. Package changes must include version bumps and REGISTRY.md sync
4. No bidirectional circular dependencies between `src/striker` and `pkg/`
