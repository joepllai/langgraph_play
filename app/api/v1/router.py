from fastapi import APIRouter

from app.config.constants import Route


router = APIRouter(prefix=Route.V1, tags=["v1"])
