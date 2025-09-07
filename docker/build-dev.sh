#!/bin/bash

# Get current user's UID and the GID of the mcp-dev group
USER_UID=$(id -u)
MCP_DEV_GID=$(getent group mcp-dev | cut -d: -f3)

if [ -z "$MCP_DEV_GID" ]; then
    echo "Warning: Group 'mcp-dev' not found. Using default GID 1679."
    MCP_DEV_GID=1679
fi

echo "Building with USER_UID=$USER_UID and USER_GID=$MCP_DEV_GID"

docker build \
    --build-arg USER_UID=$USER_UID \
    --build-arg USER_GID=$MCP_DEV_GID \
    -f docker/Dockerfile.dev \
    -t mcpnp_dev:latest \
    .