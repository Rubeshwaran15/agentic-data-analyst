from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DatasetError(Exception):
    def __init__(self, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DatasetError)
    async def dataset_error_handler(request: Request, exc: DatasetError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "An unexpected internal server error occurred.",
                "details": {"type": type(exc).__name__, "reason": str(exc)},
            },
        )