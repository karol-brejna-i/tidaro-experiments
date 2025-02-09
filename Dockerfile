# Stage 1: Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --upgrade pip hatch

COPY . .

RUN hatch build


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

# Install the app
RUN pip install --no-cache-dir /dist/tidarator-0.1.0-py3-none-any.whl

# Default entrypoint for the container (from [project.scripts])
ENTRYPOINT ["tidarator"]
