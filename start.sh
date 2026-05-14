#!/bin/bash
set -e

export DATA_SERVER_PORT=${DATA_SERVER_PORT:-8000}

cd "$(dirname "$0")"

if [ ! -d "web/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd web && npm install && cd ..
fi

echo "Starting data server..."
uvicorn server.app:app --host 0.0.0.0 --port "$DATA_SERVER_PORT" --reload --reload-dir server &
DATA_SERVER_PID=$!

echo "Starting opencode serve..."
opencode serve --cors http://localhost:8080 &
OPENCODE_PID=$!

echo "Starting frontend dev server..."
cd web
npm run dev &

trap "kill $DATA_SERVER_PID $OPENCODE_PID 2>/dev/null" EXIT
wait $OPENCODE_PID
kill $DATA_SERVER_PID 2>/dev/null