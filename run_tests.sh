#!/usr/bin/env bash
# Use python3 if available else python
if command -v python3 &>/dev/null; then
    py=$(which python3)
else
    py=$(which python)
fi
"$py" -m unittest discover
