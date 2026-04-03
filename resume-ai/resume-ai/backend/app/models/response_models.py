from pydantic import BaseModel


class ResumeResponse(BaseModel):
    resume: str


class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    mobile_no: str | None = None
    gender: str | None = None
    profile_photo_url: str | None = None
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserProfileResponse