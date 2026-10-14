import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    status = 400
    code = "bad_request"

    def __init__(self, message: str, fields: dict[str, str] | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.fields = fields
        if code:
            self.code = code


class NotFound(AppError):
    status = 404
    code = "not_found"


class Conflict(AppError):
    status = 409
    code = "conflict"


class PayloadTooLarge(AppError):
    status = 413
    code = "payload_too_large"


def _body(code: str, message: str, cid: str, fields=None) -> dict:
    return {"code": code, "message": message, "correlation_id": cid, "fields": fields}


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        cid = uuid.uuid4().hex[:12]
        return JSONResponse(_body(exc.code, exc.message, cid, exc.fields), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        cid = uuid.uuid4().hex[:12]
        fields = {".".join(str(x) for x in e["loc"][1:]) or str(e["loc"][0]): e["msg"] for e in exc.errors()}
        return JSONResponse(_body("validation_error", "Invalid request.", cid, fields), status_code=422)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):  # never leak stack traces
        cid = uuid.uuid4().hex[:12]
        return JSONResponse(_body("internal_error", "Unexpected error.", cid), status_code=500)
