from fastapi import APIRouter

from .ads import router as ads_router
from .assets import router as assets_router
from .brand import router as brand_router
from .core import router as core_router
from .credits import router as credits_router
from .generation import router as generation_router
from .profile import router as profile_router
from .subscription import router as subscription_router

# Create main router
router = APIRouter()

# Include all route modules
router.include_router(core_router, tags=["core"])
router.include_router(profile_router, prefix="/profile", tags=["profile"])
router.include_router(ads_router, prefix="/ads", tags=["ads"])
router.include_router(credits_router, prefix="/credits", tags=["credits"])
router.include_router(assets_router, prefix="/assets", tags=["assets"])
router.include_router(brand_router, prefix="/brand-identity", tags=["brand"])
router.include_router(subscription_router, tags=["subscription"])

# Include ad generation routes at root level (they have their own prefixes)
router.include_router(generation_router, tags=["generation"]) 
