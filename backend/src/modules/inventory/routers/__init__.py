"""
Inventory routers.
"""

from src.modules.inventory.routers.inventory import router as inventory_router
from src.modules.inventory.routers.assets import router as assets_router

__all__ = [
    "inventory_router",
    "assets_router",
]
