from app.core.scheduler import start_scheduler
from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    blacklist_refresh_scheduler_service,
)
from app.features.newsfeed.service.newsfeed_scheduler_service import register_newsfeed_scheduler
from app.features.ru_business_check.service.ru_business_check_retention_service import (
    register_ru_business_check_retention_scheduler,
)
from app.features.username_search.service.db_refresh_scheduler_service import (
    register_maigret_db_scheduler,
)


async def initialize_all_schedulers() -> None:
    """Register each feature's recurring job, then start the scheduler.

    The only place allowed to know about all features at once — core/scheduler.py
    knows nothing about them, see router_registry.py for the same pattern
    applied to routers.
    """
    await register_newsfeed_scheduler()
    await register_maigret_db_scheduler()
    await blacklist_refresh_scheduler_service.register_blacklist_scheduler()
    await register_ru_business_check_retention_scheduler()
    start_scheduler()
