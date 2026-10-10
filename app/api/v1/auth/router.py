from fastapi import APIRouter

from app.api.v1.auth.controller import forgot_password, get_profile, login, logout, refresh, resend_otp, reset_password, signup, social_login, verify_otp, verify_signup_otp


router = APIRouter()

router.post("/login")(login)
router.post("/signup")(signup)
router.post("/refresh")(refresh)
router.post("/logout")(logout)
router.post("/social_login")(social_login)
router.get("/profile")(get_profile)
router.post("/forgot-password")(forgot_password)
router.post("/reset-password")(reset_password)
router.post("/verify-otp")(verify_otp)
router.post("/verify-signup-otp")(verify_signup_otp)
router.post("/resend-otp")(resend_otp)



