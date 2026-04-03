from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.request_models import LoginRequest, RegisterRequest, UpdateProfileRequest
from app.models.response_models import AuthResponse, UserProfileResponse
from app.services.auth_service import auth_service

router = APIRouter()
security = HTTPBearer()


def _get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    email = payload.get("sub")
    user = auth_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user, token


@router.post("/register", response_model=AuthResponse)
def register(data: RegisterRequest):
    if len(data.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")

    user = auth_service.create_user(data.full_name, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    token = auth_service.create_access_token(user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest):
    user = auth_service.authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = auth_service.create_access_token(user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/profile", response_model=UserProfileResponse)
def profile(current=Depends(_get_current_user)):
    user, _ = current
    return user


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(data: UpdateProfileRequest, current=Depends(_get_current_user)):
    user, _ = current

    full_name = data.full_name.strip()
    email = data.email.strip().lower()
    mobile_no = data.mobile_no.strip() if data.mobile_no else None
    gender = data.gender.strip().title() if data.gender else None

    if not full_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full name is required")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    allowed_genders = {"Male", "Female", "Other", "Prefer Not To Say"}
    if gender and gender not in allowed_genders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gender must be Male, Female, Other, or Prefer Not To Say",
        )

    updated, error = auth_service.update_user_profile(
        user_id=user["id"],
        full_name=full_name,
        email=email,
        mobile_no=mobile_no,
        gender=gender,
    )
    if error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated


@router.post("/profile/photo", response_model=UserProfileResponse)
async def upload_profile_photo(file: UploadFile = File(...), current=Depends(_get_current_user)):
    user, _ = current

    if not file.content_type or file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use JPG, PNG, or WEBP image")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image is empty")

    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image must be 2MB or smaller")

    updated = auth_service.update_profile_photo(user["id"], content, file.content_type)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated


@router.post("/logout")
def logout(current=Depends(_get_current_user)):
    _, token = current
    auth_service.revoke_token(token)
    return {"message": "Logged out successfully"}