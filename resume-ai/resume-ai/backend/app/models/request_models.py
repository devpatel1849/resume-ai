from pydantic import BaseModel

class GitHubRequest(BaseModel):
    username: str
    job_description: str | None = None
    max_projects: int = 4

class ResumeRequest(BaseModel):
    text: str
    old_resume_text: str | None = None
    job_description: str | None = None
    template: str = "ATS Professional"


class ResumePdfRequest(BaseModel):
    resume_text: str
    template: str = "ATS Professional"
    file_name: str | None = None


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    full_name: str
    email: str
    mobile_no: str | None = None
    gender: str | None = None