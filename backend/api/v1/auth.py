from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from core.limiter import rate_limit
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    encrypt_value,
    hash_password,
    hash_token,
    verify_password,
)
from models.company import Company
from models.email_verification_token import EmailVerificationToken
from models.password_reset_token import PasswordResetToken
from models.refresh_token import RefreshToken
from models.trust_page import TrustPage, slugify
from models.user import User
from schemas.auth import ChangePasswordRequest, ForgotPasswordRequest, LoginRequest, RefreshRequest, RegisterRequest, ResetPasswordRequest, TokenResponse, TwoFABackupCodesRequest, TwoFADisableRequest, TwoFAEnableRequest, TwoFASetupResponse, TwoFAVerifyRequest, UpdateProfileRequest, UserResponse
from services.audit_service import log_action
from services.email_service import send_2fa_disabled_email, send_2fa_enabled_email, send_password_changed_email, send_password_reset_email, send_verification_email, send_welcome_email, send_partner_welcome_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    is_partner = body.account_type == "partner"
    company = Company(
        name=body.company_name,
        onboarding_completed=is_partner,  # partners skip onboarding flow
        is_partner_account=is_partner,
        plan="partner" if is_partner else "free",
    )
    db.add(company)
    await db.flush()

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        company_id=company.id,
        role="admin",
    )
    db.add(user)
    await db.flush()

    # Create the trust page so the public URL works immediately
    import secrets as _secrets
    _base_slug = slugify(body.company_name) or "my-company"
    _slug = _base_slug
    for _ in range(10):
        _existing = await db.execute(select(TrustPage).where(TrustPage.slug == _slug))
        if not _existing.scalar_one_or_none():
            break
        _slug = f"{_base_slug}-{_secrets.token_hex(3)}"
    db.add(TrustPage(company_id=company.id, slug=_slug))

    access_token = create_access_token(str(user.id), str(company.id))
    raw_refresh, refresh_hash = create_refresh_token()

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token)
    await db.commit()

    # Send verification email
    raw_verify, verify_hash = create_refresh_token()
    verify_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=verify_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verify_token)
    await db.commit()

    verify_url = f"{settings.app_frontend_url}/verify-email?token={raw_verify}"
    try:
        send_verification_email(user.email, verify_url)
        if is_partner:
            send_partner_welcome_email(user.email, company.name)
        else:
            send_welcome_email(user.email, company.name)
    except Exception:
        pass

    await log_action(db, company.id, "user.login", user_id=user.id, user_email=user.email)
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/login", response_model=TokenResponse)
@rate_limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # If 2FA is enabled, return a short-lived totp_token instead of full tokens
    if user.totp_enabled:
        totp_token = create_access_token(str(user.id), str(user.company_id), expire_minutes=5)
        return TokenResponse(
            access_token="",
            refresh_token="",
            requires_2fa=True,
            totp_token=totp_token,
        )

    access_token = create_access_token(str(user.id), str(user.company_id))
    raw_refresh, refresh_hash = create_refresh_token()

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token)
    await db.commit()

    await log_action(db, user.company_id, "user.login", user_id=user.id, user_email=user.email)
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one()

    await db.delete(stored)

    access_token = create_access_token(str(user.id), str(user.company_id))
    raw_refresh, refresh_hash = create_refresh_token()

    new_refresh = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(new_refresh)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(body.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored:
        await db.delete(stored)
        await db.commit()


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit("10/minute")
async def verify_email(request: Request, token: str, db: AsyncSession = Depends(get_db)):
    """Mark email as verified using the token from the verification email."""
    token_hash = hash_token(token)
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.expires_at > datetime.now(timezone.utc),
            EmailVerificationToken.used.is_(False),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one()
    user.email_verified = True
    stored.used = True
    await db.commit()
    await log_action(db, user.company_id, "user.email_verified", user_id=user.id, user_email=user.email)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit("3/minute")
async def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a new verification email to the current user."""
    if current_user.email_verified:
        return  # already verified, no-op

    raw_verify, verify_hash = create_refresh_token()
    verify_token = EmailVerificationToken(
        user_id=current_user.id,
        token_hash=verify_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(verify_token)
    await db.commit()

    verify_url = f"{settings.app_frontend_url}/verify-email?token={raw_verify}"
    try:
        send_verification_email(current_user.email, verify_url)
    except Exception:
        pass


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send a password reset email. Always returns 204 to avoid email enumeration."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        return  # silent — don't reveal whether email exists

    raw_token, token_hash = create_refresh_token()  # reuse same secure token generator
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    await db.commit()

    reset_url = f"{settings.app_frontend_url}/reset-password?token={raw_token}"
    try:
        send_password_reset_email(user.email, reset_url)
    except Exception:
        pass  # log but don't fail the request


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit("5/minute")
async def reset_password(request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using a token from the reset email."""
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    token_hash = hash_token(body.token)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
            PasswordResetToken.used.is_(False),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one()

    user.password_hash = hash_password(body.new_password)
    stored.used = True
    await db.commit()
    await log_action(db, user.company_id, "user.password_changed", user_id=user.id, user_email=user.email)

    try:
        send_password_changed_email(user.email)
    except Exception:
        pass


@router.patch("/me", response_model=UserResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    current_user.password_hash = hash_password(body.new_password)
    await db.commit()
    await db.refresh(current_user)
    try:
        send_password_changed_email(current_user.email)
    except Exception:
        pass
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name or None
    await db.commit()
    await db.refresh(current_user)
    return current_user


# ── 2FA / TOTP ────────────────────────────────────────────────────────────────

@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import json
    import secrets as _secrets
    import pyotp
    from core.security import encrypt_value

    # Generate a new TOTP secret
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(name=current_user.email, issuer_name="TraceLayer")

    # Generate 8 backup codes
    backup_codes = [_secrets.token_hex(4).upper() for _ in range(8)]

    # Encrypt and store (not yet enabled)
    current_user.totp_secret_enc = encrypt_value(secret)
    current_user.totp_backup_codes_enc = encrypt_value(json.dumps(backup_codes))
    await db.commit()

    return TwoFASetupResponse(secret=secret, qr_uri=qr_uri, backup_codes=backup_codes)


@router.post("/2fa/enable", status_code=204)
async def enable_2fa(
    body: TwoFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import pyotp
    from core.security import decrypt_value

    if not current_user.totp_secret_enc:
        raise HTTPException(status_code=400, detail="Run /2fa/setup first")

    secret = decrypt_value(current_user.totp_secret_enc)
    totp = pyotp.TOTP(secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    current_user.totp_enabled = True
    await db.commit()
    await log_action(db, current_user.company_id, "user.2fa_enabled", user_id=current_user.id, user_email=current_user.email)
    try:
        send_2fa_enabled_email(current_user.email)
    except Exception:
        pass


@router.post("/2fa/disable", status_code=204)
async def disable_2fa(
    body: TwoFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    current_user.totp_enabled = False
    current_user.totp_secret_enc = None
    current_user.totp_backup_codes_enc = None
    await db.commit()
    await log_action(db, current_user.company_id, "user.2fa_disabled", user_id=current_user.id, user_email=current_user.email)
    try:
        send_2fa_disabled_email(current_user.email)
    except Exception:
        pass


@router.post("/2fa/verify", response_model=TokenResponse)
@rate_limit("10/minute")
async def verify_2fa(request: Request, body: TwoFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    import json
    import pyotp
    from core.security import decrypt_value

    try:
        payload = decode_access_token(body.totp_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired 2FA token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.totp_enabled or not user.totp_secret_enc:
        raise HTTPException(status_code=401, detail="Invalid 2FA state")

    secret = decrypt_value(user.totp_secret_enc)
    totp = pyotp.TOTP(secret)
    code = body.code.strip().upper()

    # Check TOTP code
    if totp.verify(code, valid_window=1):
        pass  # valid
    else:
        # Check backup codes
        if user.totp_backup_codes_enc:
            backup_codes: list[str] = json.loads(decrypt_value(user.totp_backup_codes_enc))
            if code in backup_codes:
                # Consume the backup code
                backup_codes.remove(code)
                user.totp_backup_codes_enc = encrypt_value(json.dumps(backup_codes))
            else:
                raise HTTPException(status_code=401, detail="Invalid authentication code")
        else:
            raise HTTPException(status_code=401, detail="Invalid authentication code")

    access_token = create_access_token(str(user.id), str(user.company_id))
    raw_refresh, refresh_hash = create_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token)
    await db.commit()

    await log_action(db, user.company_id, "user.login", user_id=user.id, user_email=user.email)
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/2fa/backup-codes", response_model=TwoFASetupResponse)
async def regenerate_backup_codes(
    body: TwoFABackupCodesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import json
    import secrets as _secrets
    import pyotp
    from core.security import decrypt_value, encrypt_value

    if not verify_password(body.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if not current_user.totp_enabled or not current_user.totp_secret_enc:
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    secret = decrypt_value(current_user.totp_secret_enc)
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(name=current_user.email, issuer_name="TraceLayer")

    backup_codes = [_secrets.token_hex(4).upper() for _ in range(8)]
    current_user.totp_backup_codes_enc = encrypt_value(json.dumps(backup_codes))
    await db.commit()

    return TwoFASetupResponse(secret=secret, qr_uri=qr_uri, backup_codes=backup_codes)
