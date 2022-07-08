"""Convenience functions for dealing with requests & endpoints"""
from fastapi import Request


def db_conn(request: Request):
    """Getter for this app's active database."""
    return request.app.state.db_path
