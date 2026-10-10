
from fastapi import HTTPException

from app.helpers.api_response import APIResponse, ErrorDetail


def error_response(
    message: str,
    code: str = "BAD_REQUEST",
    status_code: int = 400,
    details=None,
):
    raise HTTPException(
        status_code=status_code,
        detail=APIResponse(
            success=False,
            message=message,
            error=ErrorDetail(code=code, details=details)
        ).dict()
    )

