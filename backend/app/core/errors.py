"""統一錯誤格式(AGENTS.md):{"error": {"code": ..., "message": ...}},message 為繁體中文。"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    """業務錯誤:帶 HTTP 狀態碼、錯誤代碼與繁中訊息。"""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(422, "VALIDATION_ERROR", "請求參數格式不正確")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = "找不到請求的資源" if exc.status_code == 404 else "請求無法處理"
        return _error_response(exc.status_code, f"HTTP_{exc.status_code}", message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request, _exc: Exception
    ) -> JSONResponse:
        # 不洩漏堆疊或內部路徑(AGENTS.md)
        return _error_response(500, "INTERNAL_ERROR", "伺服器發生未預期的錯誤,請稍後再試")
