#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -d "web/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd web && npm install && cd ..
fi

echo "Starting opencode serve..."
opencode serve --cors http://localhost:8080 &
OPENCODE_PID=$!

echo "Starting frontend dev server..."
cd web
npm run dev &

wait $OPENCODE_PID