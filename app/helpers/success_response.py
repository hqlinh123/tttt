from app.helpers.api_response import APIResponse


def success_response(message: str, data=None):
    return APIResponse(
        success=True,
        message=message,
        data=data
    )