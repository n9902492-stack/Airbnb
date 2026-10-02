from pydantic import BaseModel, Field


class HostProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=2000)
    avatar_url: str | None = Field(default=None, max_length=500)
    languages: list[str] = []
    interests: list[str] = []
    work: str | None = Field(default=None, max_length=180)
