from fastapi import HTTPException


class ApiError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, meta: dict | None = None):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "meta": meta or {},
            },
        )