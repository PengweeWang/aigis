#!/bin/bash
PORT=${1:-8001}
export MCP_PORT=$PORT
exec python3 -m mcps.server_sse
