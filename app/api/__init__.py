from app.api.v1.router import router as V1Router


def register_api(app):
    app.include_router(V1Router)
