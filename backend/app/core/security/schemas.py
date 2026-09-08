from pydantic import BaseModel, Field


class AccessTokenRegenerateResponse(BaseModel):
    access_token: str = Field(..., description="The newly generated access token")
