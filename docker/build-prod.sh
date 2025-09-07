#!/bin/bash

docker build \
    -f docker/Dockerfile.prod \
    -t mcpnp_prd:latest \
    .