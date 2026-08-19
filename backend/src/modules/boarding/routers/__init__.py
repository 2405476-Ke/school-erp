"""Boarding routers package."""

from src.modules.boarding.routers.boarding import router as boarding_router
from src.modules.boarding.routers.discipline import router as discipline_router

__all__ = [
    "boarding_router",
    "discipline_router",
]
