from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


from app.utils.apiHelper import ApiHelper
from app.utils.exceptions import (
    general_exception_handler,
    validation_exception_handler,
)
from app.api import register_api
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Clean up Tcp connection
    await ApiHelper().stop()


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "*",
]


def create_app():
    app = FastAPI(lifespan=lifespan)

    # add exception handler
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # middleware 先用CORS驗證 避免preflight被JWT auth擋下
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # register feature api
    register_api(app)

    return app


app = create_app()
