"""Middleware для обработки запросов."""
from middlewares.database import DatabaseMiddleware

__all__ = [
    "DatabaseMiddleware",
]
