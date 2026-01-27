"""
Autonomous Data Quality Agent (ADQA) Library.

Disables telemetry tracking for all dependencies e.g. (PyAirbyte)
by setting the DO_NOT_TRACK environment variable.
"""

import os

# Disable telemetry for all dependencies that respect DO_NOT_TRACK
os.environ["DO_NOT_TRACK"] = "1"
