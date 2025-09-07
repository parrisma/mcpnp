#!/bin/sh

# Stop and remove existing container if it exists
echo "Stopping existing mcpnp_dev container..."
docker stop mcpnp_dev 2>/dev/null || true

echo "Removing existing mcpnp_dev container..."
docker rm mcpnp_dev 2>/dev/null || true

echo "Starting new mcpnp_dev container..."
echo "Mounting $HOME/devroot/mcpnp to /home/mcpnp/devroot/mcpnp in container"
echo "Mounting $HOME/.ssh to /home/mcpnp/.ssh (read-only) in container"

docker run -d \
--name mcpnp_dev \
-v "$HOME/devroot/mcpnp":/home/mcpnp/devroot/mcpnp \
-v "$HOME/.ssh:/home/mcpnp/.ssh:ro" \
mcpnp_dev:latest

if docker ps -q -f name=mcpnp_dev | grep -q .; then
    echo "Container mcpnp_dev is now running"
    echo ""
    echo "To connect from shell: docker exec -it mcpnp_dev /bin/bash"
    echo "To connect from VS Code: use container name 'mcpnp_dev'"
else
    echo "ERROR: Container mcpnp_dev failed to start"
    exit 1
fi