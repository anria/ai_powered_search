#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting the Python wrapper script..."

# Optional: Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Python script and pass along all arguments ("$@")
# python3 main.py "$@"
python3 manage.py migrate   # (no models, but good practice)
python3 manage.py runserver 

echo "Run server completed successfully!"
