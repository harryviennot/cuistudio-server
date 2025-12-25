"""
Main API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    recipes,
    cookbooks,
    extraction,
    upload,
    collections,
    discovery,
    credits,
    referrals,
    webhooks,
    categories,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(recipes.router)
api_router.include_router(cookbooks.router)
api_router.include_router(extraction.router)
api_router.include_router(upload.router)
api_router.include_router(collections.router)
api_router.include_router(discovery.router)
api_router.include_router(credits.router)
api_router.include_router(referrals.router)
api_router.include_router(webhooks.router)
api_router.include_router(categories.router)
