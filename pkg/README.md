# pkg/ — UV Workspace Isolation Zone

This directory hosts **internal library packages** managed by `uv workspace`.
The root `pyproject.toml` declares `members = ["pkg/*"]`, giving each sub-directory
its own dependency boundary.

## Purpose

Isolate reusable, cross-cutting utilities from the main `src/striker/` business logic.
This prevents circular imports and allows independent versioning.

## Rules

1. **No circular dependencies** — `pkg/` packages MUST NOT import from `src/striker/`.
   `src/striker/` MAY import from `pkg/` packages.
2. **No inter-package dependencies** — packages inside `pkg/` MUST NOT depend on
   each other unless explicitly documented and approved.
3. **Each package is self-contained** — every `pkg/<name>/` directory must include:
   - `pyproject.toml` with `[project]` metadata (name, version)
   - `src/<name>/__init__.py`
4. **Version bumps required** — any change to a `pkg/` package must increment its
   version in the corresponding `pyproject.toml`.

## Adding a New Package

```bash
mkdir -p pkg/my-lib/src/my_lib
cat > pkg/my-lib/pyproject.toml << 'EOF'
[project]
name = "my-lib"
version = "0.1.0"
requires-python = ">=3.13"

[build-system]
requires = ["uv_build>=0.11.6,<0.12.0"]
build-backend = "uv_build"
EOF

echo '"""my-lib package."""' > pkg/my-lib/src/my_lib/__init__.py
uv sync
```
