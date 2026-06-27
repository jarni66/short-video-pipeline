#!/bin/bash
# Generate videos (key-free, generate-only) on macOS / Linux.
# Usage: ./make_videos.sh [path-to-concepts.json]   (defaults to sample_concepts.json)
set -e
cd "$(dirname "$0")"

JSON="${1:-sample_concepts.json}"

if [ ! -x "venv/bin/python" ]; then
  echo "[X] Environment not set up. Run ./setup.sh first."
  exit 1
fi
if [ ! -f "$JSON" ]; then
  echo "[X] Concepts file not found: $JSON"
  exit 1
fi

echo "=== Loading concepts from $JSON ==="
venv/bin/python -c "import json,pipeline_state as ps; ps.load_concepts_into_state(json.load(open('$JSON',encoding='utf-8')), replace=True); print('queued:', ps.counts(ps.load_state()))"

echo ""
echo "=== Generating videos (a few minutes each) ==="
venv/bin/python generate_pool.py

echo ""
echo "=== Done. Your videos are in: storage/tasks/<name>/final-1.mp4 ==="
