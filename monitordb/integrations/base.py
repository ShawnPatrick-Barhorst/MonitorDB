import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter
from fastmcp import FastMCP


@dataclass
class Integration:
    name: str
    build_schema: Callable[[sqlite3.Connection], None] | None = None
    router: APIRouter | None = None
    mcp: FastMCP | None = None
