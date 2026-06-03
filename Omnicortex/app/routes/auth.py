from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    summary="Register a new user",
    description="Create a new user account with bcrypt password hashing and JWT-ready identity data.",
)
async def register(payload: RegisterRequest) -> UserResponse:
    user = auth_service.register(payload.email, payload.password, payload.full_name)
    return UserResponse(id=user.id, email=user.email, full_name=user.full_name)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT",
    description="Validate user credentials and return a bearer token for protected OmniCortex routes.",
)
async def login(payload: LoginRequest) -> TokenResponse:
    token = auth_service.authenticate(payload.email, payload.password)
    return TokenResponse(access_token=token)
