"""
Main API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, recipes, cookbooks, extraction

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(recipes.router)
api_router.include_router(cookbooks.router)
api_router.include_router(extraction.router)
