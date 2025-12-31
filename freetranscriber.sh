#!/bin/bash

# FreeTranscriber Launch Script for Linux

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if DISPLAY is set (for X11/Wayland)
if [ -z "$DISPLAY" ]; then
    echo "⚠️  DISPLAY environment variable not set. Are you running in a terminal without GUI?"
    exit 1
fi

# Launch FreeTranscriber
freetranscriber "$@"
