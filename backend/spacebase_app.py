"""Compatibility import for older start commands.

Run either `backend.main:app` (preferred) or `backend.spacebase_app:app`.
The single application owns the routes; no duplicate route or mount insertion.
"""
from backend.main import app
