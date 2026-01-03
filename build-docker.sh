#!/usr/bin/env bash

# ==============================================================================
# Build Superset with Multi-Stage Docker Build
# ==============================================================================
# This script now uses Dockerfile.superset-auto which generates constraints.txt
# internally, eliminating the need for local temporary files.
#
# The constraints generation and merging now happens inside Docker stages.
# ==============================================================================

set -e  # Exit on error

SUPERSET_VERSION=5.0.0
IMAGE_NAME="superset-trino"
DOCKERFILE="Dockerfile.superset"

echo "=============================================="
echo "Building Superset ${SUPERSET_VERSION}"
echo "Image name: ${IMAGE_NAME}"
echo "Dockerfile: ${DOCKERFILE}"
echo "=============================================="

# Build with multi-stage Dockerfile
echo ""
echo "Starting multi-stage build..."
docker build -t ${IMAGE_NAME} -f ${DOCKERFILE} .
