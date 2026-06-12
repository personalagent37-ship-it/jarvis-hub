#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
if [ -f "jarvis-env/bin/activate" ]; then
  source jarvis-env/bin/activate
fi

jarvis-env/bin/python3 main.py --mode wake
