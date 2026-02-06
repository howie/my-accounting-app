"""Shared rate limiter instance for the application."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter: used by main.py (app.state) and webhook routes
limiter = Limiter(key_func=get_remote_address)
