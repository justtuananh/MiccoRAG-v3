#!/bin/bash
# NexusRAG Backend — start FastAPI server (port 8080)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/backend"

# Activate NexusRAG's own venv
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "ERROR: venv not found. Create it first:"
    echo "  cd $SCRIPT_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

echo "Starting NexusRAG backend on port 8080..."
uvicorn app.main:app --reload --port 8080
