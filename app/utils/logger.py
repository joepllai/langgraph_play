import time
import json
import contextvars
import logging
import sys
from logging import StreamHandler

from functools import wraps

from app.config.logger import LoggerConfig
from app.config.constants import ContextVarKeys

opid_var = contextvars.ContextVar(ContextVarKeys.OPID)
user_var = contextvars.ContextVar(ContextVarKeys.USER)

# for initailize the context variables
opid_var.set("default")
user_var.set({})


class CustomLogger(logging.Logger):
    def info(self, msg, *args, **kwargs):
        extra = kwargs.get("extra", {})
        extra.setdefault("operation_id", opid_var.get())
        extra.setdefault("user", json.dumps(user_var.get()))
        kwargs["extra"] = {"custom_dimensions": extra}
        super().info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        extra = kwargs.get("extra", {})
        extra.setdefault("operation_id", opid_var.get())
        extra.setdefault("user", json.dumps(user_var.get()))
        kwargs["extra"] = {"custom_dimensions": extra}
        super().error(msg, *args, **kwargs)


logging.setLoggerClass(CustomLogger)
logger = logging.getLogger(__name__)

logger.setLevel(LoggerConfig.LOG_LEVEL)

# Add console log handler
console_handler = StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LoggerConfig.LOG_FORMAT))
logger.addHandler(console_handler)


def log_func_details(func, start_time, end_time):
    logger.info(
        f"{func.__name__}",
        extra={
            "func": func.__name__,
            "duration": end_time - start_time,
        },
    )


def log_func_elasped_time(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        log_func_details(func, start_time, end_time)
        return result

    return sync_wrapper


def log_async_func_elasped_time(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        log_func_details(func, start_time, end_time)
        return result

    return async_wrapper


def log_async_generator_func_elasped_time(func):
    @wraps(func)
    async def async_generator_wrapper(*args, **kwargs):
        start_time = time.time()
        async for result in func(*args, **kwargs):
            yield result
        end_time = time.time()
        log_func_details(func, start_time, end_time)

    return async_generator_wrapper
