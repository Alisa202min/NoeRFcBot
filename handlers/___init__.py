from aiogram import Router
from .base_handlers import router as base_router
from .product_handlers import router as product_router
from .service_handlers import router as service_router
from .education_handlers import router as education_router
from .inquiry_handlers import router as inquiry_router
from .search_handlers import router as search_router
from .media_handlers import router as media_router

main_router = Router(name="main_router")
main_router.include_routers(
    base_router,
    product_router,
    service_router,
    education_router,
    inquiry_router,
    search_router,
    media_router
)