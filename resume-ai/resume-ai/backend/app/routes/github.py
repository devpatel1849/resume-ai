from fastapi import APIRouter
from app.services.github_service import github_service
from app.models.request_models import GitHubRequest

router = APIRouter()

@router.post("/github")
def fetch_github(data: GitHubRequest):
    return github_service.get_repos(
        data.username,
        data.job_description,
        data.max_projects,
    )