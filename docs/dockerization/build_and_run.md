# Building and running in Docker

## Building the image

Go to the project's main directory and:

```bash
docker build -t tidarator:latest .
```

The multistage [Dockerfile](../../Dockerfile) uses `hatch` to build the project and install resulting package.

It also creates `/app/log` and `/app/secret` directories and "instructs" the app to use them.

## Running the container

Navigate to [docs/dockerization/example](example), 
where you will find an example folder structure and config files:

- config/logging.toml - configuration for logging system ()
- my.env - 

If you run the app like this:
```
docker run -it --env-file my.env \
    -v $(pwd)/secret:/app/secret \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/logs:/app/logs \
    -e LOGGING_CONFIG_PATH=/app/config/logging.toml \
    tidarator show-bookings
```

Log file and sessions secrets will be created in a specified directory, mounted to the host directory.
This way, the secrets can be share between different container runs, and you'll be albe to analyze output of the app
by inspecting the logs.
