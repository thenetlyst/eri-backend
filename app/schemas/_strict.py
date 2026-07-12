from pydantic import BaseModel, ConfigDict

class StrictRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=False,
    )