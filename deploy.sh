#!/usr/bin/env bash
# Redeploy the GradeWise stack: pull latest, rebuild, restart, and reclaim disk.
# Safe to run repeatedly. Run from anywhere — it cd's to the repo root itself.
#
#   ./deploy.sh
#
set -euo pipefail

# Repo root = the directory this script lives in.
cd "$(dirname "$0")"

echo "==> Pulling latest code..."
git pull

echo "==> Rebuilding images and recreating containers..."
docker compose up --build -d

# Reclaim disk from old builds. Plain -f only removes DANGLING/UNUSED items
# (dangling images, stopped containers, unused networks, dangling build cache) —
# the running stack and its images are untouched. Do NOT add -a here: that would
# delete cached base layers and force a slow cold rebuild next time.
echo "==> Pruning dangling images / stopped containers / build cache..."
docker system prune -f

echo "==> Current status:"
docker compose ps
