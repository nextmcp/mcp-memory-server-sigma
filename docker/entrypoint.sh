#! /bin/bash

APP_ARGS="--non-reloadable"

if [ -n "$PORT" ]; then
    APP_ARGS+=" --port $PORT"
fi

# Configure application startup with optional Datadog tracing
APP_START="python${PYTHON_VERSION}"
if [ "${DD_TRACE_ENABLED}" = "True" ]; then
    echo "Starting ${SERVICE_NAME:-openmemory} application with Datadog tracing enabled"
    export DD_AGENT_HOST=$(jq --raw-output '.HostPrivateIPv4Address' /opt/ecs/metadata/*/ecs-container-metadata.json 2>/dev/null || hostname -i)
    echo "Datadog agent host set to: $DD_AGENT_HOST"
    APP_START="ddtrace-run ${APP_START}"
else
    echo "Starting ${SERVICE_NAME:-openmemory} application with Datadog tracing disabled"
fi

# Run initial sync from PostgreSQL to Qdrant on startup (in background)
echo "Starting initial sync from PostgreSQL to Qdrant..."
cd /srv/openmemory && python${PYTHON_VERSION} sync_qdrant_from_postgres.py &
SYNC_PID=$!
echo "Initial sync started in background (PID: $SYNC_PID)"

# Run diagnostics after a brief delay to let sync complete
(sleep 300 && echo "Running Mem0 diagnostics..." && cd /srv/openmemory && python${PYTHON_VERSION} scripts/diagnose_mem0_get_all.py) &

# Start the application
exec ${APP_START} . $APP_ARGS
