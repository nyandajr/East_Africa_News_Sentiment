#!/bin/bash
# auto_update.sh: run the scheduler script with virtualenv
set -e
cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

python -m src.scheduler >> logs/scheduler.log 2>&1
