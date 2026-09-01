"""
Mehfooz root entry point.
Re-exports `app` from `app.main` for backwards compatibility with `uvicorn main:app`.
"""
from app.main import app

__all__ = ["app"]
