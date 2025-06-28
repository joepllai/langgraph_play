from fastapi import APIRouter

from app.config.constants import Route

# Import endpoints to register them with the router
from app.api.v1.endpoints import ask, refresh_index, crawl_web

router = APIRouter(prefix=Route.V1, tags=["v1"])
