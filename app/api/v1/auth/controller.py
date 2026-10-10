from datetime import timedelta

from fastapi import Depends, HTTPException, status

from app.core.deps import get_auth_service, get_current_user
from app.domain.schemas.auth import AuthResponse, EmailRequest, ForgotPasswordRequest, LoginRequest, RefreshTokenRequest, ResetPasswordRequest, SignupRequest, SocialLoginRequest, UserProfileResponse, VerifyOtpRequest
from app.helpers.api_response import APIResponse
from app.services.auth_service import AuthService



# ---------------- LOGIN ----------------
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> APIResponse[AuthResponse]:
    try:
        return await auth_service.login(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ---------------- SIGNUP ----------------

async def signup(
    payload: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        return await auth_service.signup(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ---------------- REFRESH TOKEN ----------------
async def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        return await auth_service.refresh_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ---------------- LOGOUT ----------------
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.logout()
    return {"message": "Logged out"}

async def social_login(
    payload: SocialLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> APIResponse[AuthResponse]:
    try:
        return await auth_service.social_login(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
async def get_profile(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_profile(current_user.id)

async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.forgot_password(payload.email)


async def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    
    return await auth_service.reset_password(
        payload.token,
        payload.new_password,
    )

async def verify_otp(
    payload: VerifyOtpRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.verify_otp(
        payload.email,
        payload.otp,
    )
async def verify_signup_otp(
    payload: VerifyOtpRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.verify_signup_otp(
        payload.email,
        payload.otp,
    )

async def resend_otp(
    payload: EmailRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.resend_otp(payload.email)
