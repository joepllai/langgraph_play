import sqlalchemy


from functools import wraps
from sqlalchemy.exc import SQLAlchemyError


def handle_sqlalchemy_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError:
            db = kwargs.get("db")
            if db:
                db.rollback()
            raise

    return wrapper


def handle_async_sqlalchemy_error(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SQLAlchemyError:
            db = kwargs.get("db")
            if db:
                await db.rollback()
            raise

    return async_wrapper


def is_table_exist(engine, table_name):
    return sqlalchemy.inspect(engine).has_table(table_name)
