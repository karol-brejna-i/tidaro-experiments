# Build System & Procedures

## Overview

Tidarator uses [Hatch](https://hatch.pypa.io/) as its build system, defined in `pyproject.toml`. The project produces a Python wheel package that gets installed inside a Docker image.

## Version Management

The version is derived automatically from **git tags** using [`hatch-vcs`](https://github.com/ofek/hatch-vcs) (which wraps `setuptools-scm`).

**How it works:**

1. You create a git tag like `v0.3.0`
2. `hatch-vcs` reads the tag and generates the version string
3. During build, a `tidarator/_version.py` file is generated with the version
4. At runtime, `tidarator.__version__` exposes the version (from `_version.py` or `importlib.metadata`)

**Configuration** (in `pyproject.toml`):
```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]

[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
fallback-version = "0.0.0-dev"

[tool.hatch.build.hooks.vcs]
version-file = "tidarator/_version.py"
```

**Version tag format:** `v<MAJOR>.<MINOR>.<PATCH>` (e.g., `v0.3.0`, `v1.0.0`)

**To release a new version:**
```bash
git tag v0.3.0
git push origin v0.3.0
hatch build
```

**Between tags**, the version includes a dev suffix based on commit distance from the last tag, e.g. `0.3.0.dev4+gabcdef0`.

**Check the version at runtime:**
```bash
tidarator --version
# or
python -c "from tidarator import __version__; print(__version__)"
```

> **Note:** `tidarator/_version.py` is auto-generated and listed in `.gitignore`. Do not edit it manually.

## Building the Package Locally

```bash
# Install hatch if not already available
pip install hatch

# Build the wheel and sdist
hatch build
```

This produces files in `dist/`:
```
dist/
  tidarator-0.1.2-py3-none-any.whl
  tidarator-0.1.2.tar.gz
```

## Building the Docker Image

The Dockerfile is a multi-stage build:
1. **Builder stage**: installs `hatch`, copies source, runs `hatch build`
2. **Runtime stage**: copies the built `.whl` from builder, pip-installs it

```bash
docker build -t tidarator:latest .
```

To tag with a specific version:
```bash
docker build -t tidarator:0.1.2 -t tidarator:latest .
```

## Running (Docker)

See [dockerization/build_and_run.md](dockerization/build_and_run.md) for full details.

Quick reference:
```bash
docker run --env-file my.env \
    -v $(pwd)/secret:/app/secret \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/logs:/app/logs \
    -e LOGGING_CONFIG_PATH=/app/config/logging.toml \
    tidarator:latest book-free -f 2026-02-14
```

## Running from IDE / Source (no Docker)

Useful for quick iteration and debugging:

```bash
cd /path/to/tidaro-experiments
pip install -e .                              # editable install
export $(grep -v '^#' .env | xargs)           # load env vars
tidarator show-spots -d 2026-02-15            # run any command
```

## Running Tests

```bash
hatch run test:run          # run all tests
hatch run test:cov          # run with coverage
# or directly:
python -m pytest tests/ -v
```

---

## Issues Found & Fixes Applied

### 1. Hardcoded version in Dockerfile (FIXED)

**Problem**: The Dockerfile had:
```dockerfile
RUN pip install --no-cache-dir /dist/tidarator-0.1.2-py3-none-any.whl
```
Every version bump in `pyproject.toml` required a matching edit in the Dockerfile. If forgotten, the Docker build would fail.

**Fix applied**: Changed to a wildcard:
```dockerfile
RUN pip install --no-cache-dir /dist/*.whl
```

This is safe because the builder stage produces exactly one wheel.

### ~~2. Version drift between source, dist, and Docker~~ ✅ RESOLVED

**Resolved by:** `hatch-vcs` — the version is now always derived from git tags, so source, dist, and Docker image are guaranteed to be in sync as long as builds happen from tagged commits.

---

## Suggested Improvements

### A. Add a build script

A simple shell script to eliminate manual mistakes:

```bash
#!/bin/bash
# build.sh — build package and Docker image
set -e

VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
echo "Building tidarator v${VERSION}"

# Clean old artifacts
rm -rf dist/

# Build Python package
hatch build

# Build Docker image
docker build -t "tidarator:${VERSION}" -t tidarator:latest .

echo "Done. Image: tidarator:${VERSION}"
```

### ~~B. Use hatch-vcs or dynamic versioning~~ ✅ IMPLEMENTED

The project now uses `hatch-vcs` for git-tag-based versioning. See "Version Management" above.

### ~~C. Make the version accessible at runtime~~ ✅ IMPLEMENTED

`tidarator/__init__.py` exposes `__version__` and the CLI has a `--version` flag.

```bash
tidarator --version
```

### D. Add `.dockerignore`

Avoid copying unnecessary files into the Docker build context:

```
__pycache__/
*.pyc
dist/
.git/
.env
docs/
tests/
*.log
```

### E. Clean `dist/` in Dockerfile builder stage

Ensure no stale wheels leak in:

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --upgrade pip hatch
COPY . .
RUN rm -rf dist/ && hatch build
```
