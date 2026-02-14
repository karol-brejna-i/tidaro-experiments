# Stage 1: Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install git (required by hatch-vcs to derive version from tags)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip hatch hatch-vcs

COPY . .

RUN rm -rf dist/ && hatch build


# Stage 2: Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Set default log directory
RUN mkdir -p /app/logs
ENV LOG_DIR=/app/logs

# Set default session secret  directory
RUN mkdir -p /app/secret
ENV SESSION_SECRETS_DIR=/app/secret

# Copy the built wheel from the builder stage
COPY --from=builder /app/dist/*.whl /dist/

# Install the app (wildcard to avoid hardcoding the version)
RUN pip install --no-cache-dir /dist/*.whl

# Default entrypoint for the container (from [project.scripts])
ENTRYPOINT ["tidarator"]
