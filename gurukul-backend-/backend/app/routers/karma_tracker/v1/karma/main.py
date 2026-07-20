from fastapi import APIRouter

# Import all route modules
from app.routers.karma_tracker.v1.karma.log_action import router as log_action_router
from app.routers.karma_tracker.v1.karma.appeal import router as appeal_router
from app.routers.karma_tracker.v1.karma.atonement import router as atonement_router
from app.routers.karma_tracker.v1.karma.death import router as death_router
from app.routers.karma_tracker.v1.karma.stats import router as stats_router
from app.routers.karma_tracker.v1.karma.event import router as event_router

router = APIRouter()

# Include all routers with appropriate prefixes
router.include_router(log_action_router, prefix="/log-action", tags=["Karma Actions"])
router.include_router(appeal_router, prefix="/appeal", tags=["Karma Appeal"])
router.include_router(atonement_router, prefix="/atonement", tags=["Atonement"])
router.include_router(death_router, prefix="/death", tags=["Death Events"])
router.include_router(stats_router, prefix="/stats", tags=["Karma Stats"])
router.include_router(event_router, prefix="/event", tags=["Unified Events"])