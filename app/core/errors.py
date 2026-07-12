from fastapi import status
from .api_error import ApiError
from .error_codes import ErrorCode


# -----------------------------
# AUTH
# -----------------------------
def unauthorized(message="Unauthorized", code=ErrorCode.UNAUTHORIZED):
    raise ApiError(status.HTTP_401_UNAUTHORIZED, code, message)


# -----------------------------
# NOT FOUND
# -----------------------------
def not_found(code, message):
    raise ApiError(status.HTTP_404_NOT_FOUND, code, message)


# -----------------------------
# FORBIDDEN
# -----------------------------
def forbidden(code, message, meta=None):
    raise ApiError(status.HTTP_403_FORBIDDEN, code, message, meta)


# -----------------------------
# CONFLICT
# -----------------------------
def conflict(code, message):
    raise ApiError(status.HTTP_409_CONFLICT, code, message)


# -----------------------------
# INTERNAL
# -----------------------------
def internal_error(message="Internal server error"):
    raise ApiError(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorCode.INTERNAL_SERVER_ERROR, message)

# -----------------------------
# BAD REQUEST
# -----------------------------
def bad_request(message="Bad request"):
    raise ApiError(status.HTTP_400_BAD_REQUEST, ErrorCode.BAD_REQUEST, message)