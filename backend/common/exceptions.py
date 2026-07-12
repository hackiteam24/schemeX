from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler so every error response also
    exposes a top-level "message" string. The frontend's API helper reads
    `data.message` when a request fails (see frontend/static/js/main.js).
    """

    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    detail = response.data

    if isinstance(detail, dict):
        if "detail" in detail:
            message = str(detail["detail"])
        else:
            # Field validation errors: {"field": ["msg1", "msg2"], ...}
            first_key = next(iter(detail), None)
            first_val = detail.get(first_key) if first_key else None
            if isinstance(first_val, (list, tuple)) and first_val:
                message = f"{first_key}: {first_val[0]}" if first_key != "non_field_errors" else str(first_val[0])
            else:
                message = str(first_val) if first_val else "Something went wrong"
    elif isinstance(detail, list) and detail:
        message = str(detail[0])
    else:
        message = str(detail)

    if isinstance(response.data, dict):
        response.data.setdefault("message", message)
    else:
        response.data = {"message": message, "detail": response.data}

    return response
