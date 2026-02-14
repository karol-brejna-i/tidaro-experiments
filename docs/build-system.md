# Build System & Procedures

## Overview

Tidarator uses [Hatch](https://hatch.pypa.io/) as its build system, defined in `pyproject.toml`. The project produces a Python wheel package that gets installed inside a Docker image.

## Version Management

The version is defined in a single place:

```toml
# pyproject.toml
[project]
version = "0.1.2"
```

**To bump the version**, edit the `version` field in `pyproject.toml`. There are no other files that need updating — the Dockerfile now uses a wildcard to install the wheel (see fix below).

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

### 2. Version drift between source, dist, and Docker

**Problem observed**: At the time of analysis:
- `pyproject.toml` says version `0.1.2`
- Local `dist/` contains stale `0.1.0` artifacts
- Docker image is tagged `0.3.0`

These are all out of sync, making it unclear what code is actually running.

**Recommendation**: Clean `dist/` before building and always tag Docker images to match the source version (see suggestions below).

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

### B. Use hatch-vcs or dynamic versioning

Instead of manually editing `pyproject.toml`, derive the version from git tags:

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
```

Then simply `git tag v0.2.0 && hatch build` — version is derived automatically.

### C. Make the version accessible at runtime

Add the version to `tidarator/__init__.py` for runtime inspection:

```python
# tidarator/__init__.py
from importlib.metadata import version
__version__ = version("tidarator")
```

Then add a `--version` flag to the CLI:

```python
@click.group()
@click.version_option(package_name="tidarator")
def cli(ctx):
    ...
```

This lets users verify what version is running inside Docker:
```bash
docker run tidarator:latest --version
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
