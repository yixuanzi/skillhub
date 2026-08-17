"""Aegis Portal OIDC client endpoints for SkillHub."""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from jose import JWTError, jwk, jwt
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from config import settings
from core.security import get_password_hash
from database import get_db
from models.oidc import OidcLoginTransaction, SsoLoginTicket
from models.user import Role, User
from services.auth_service import AuthService


router = APIRouter(prefix="/sso", tags=["Aegis Portal OIDC"])


class OidcUserError(ValueError):
    """Raised when trusted OIDC claims cannot be mapped safely."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _issuer() -> str:
    return settings.OIDC_ISSUER.rstrip("/")


def _backchannel() -> str:
    return (settings.OIDC_BACKCHANNEL_URL or settings.OIDC_ISSUER).rstrip("/")


def _configuration_error() -> HTTPException | None:
    required = {
        "OIDC_ISSUER": settings.OIDC_ISSUER,
        "OIDC_CLIENT_ID": settings.OIDC_CLIENT_ID,
        "OIDC_CLIENT_SECRET": settings.OIDC_CLIENT_SECRET,
        "OIDC_REDIRECT_URI": settings.OIDC_REDIRECT_URI,
    }
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        return HTTPException(
            status_code=503,
            detail=f"SkillHub OIDC 配置不完整：缺少 {', '.join(missing)}。",
        )
    return None


def _redirect_target() -> str:
    return settings.OIDC_POST_LOGIN_REDIRECT or "/sso/callback"


def _frontend_error(error: str, description: str) -> RedirectResponse:
    target = _redirect_target()
    separator = "&" if "?" in target else "?"
    location = f"{target}{separator}{urlencode({'error': error, 'error_description': description})}"
    return RedirectResponse(location, status_code=302, headers={"Cache-Control": "no-store"})


def _create_pkce_transaction(
    db: Session,
    *,
    organization_id: str | None,
    flow: str,
) -> tuple[OidcLoginTransaction, str]:
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    transaction = OidcLoginTransaction(
        state=state,
        nonce=nonce,
        code_verifier=verifier,
        client_id=settings.OIDC_CLIENT_ID,
        organization_id=organization_id,
        flow=flow,
        expires_at=_utcnow() + timedelta(seconds=settings.OIDC_TRANSACTION_TTL_SECONDS),
    )
    db.add(transaction)
    db.commit()
    return transaction, verifier


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _authorize_location(transaction: OidcLoginTransaction, verifier: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.OIDC_CLIENT_ID,
        "redirect_uri": settings.OIDC_REDIRECT_URI,
        "scope": "openid profile email",
        "state": transaction.state,
        "nonce": transaction.nonce,
        "code_challenge": _code_challenge(verifier),
        "code_challenge_method": "S256",
    }
    if transaction.flow == "sso":
        params["sso"] = "1"
    else:
        params["organization_id"] = str(transaction.organization_id)
    return f"{_issuer()}/oauth/authorize?{urlencode(params)}"


def _pending_transaction(db: Session, state: str) -> OidcLoginTransaction | None:
    transaction = db.query(OidcLoginTransaction).filter(
        OidcLoginTransaction.state == state,
        OidcLoginTransaction.consumed_at.is_(None),
    ).first()
    if not transaction:
        return None
    if _as_utc(transaction.expires_at) <= _utcnow():
        transaction.consumed_at = _utcnow()
        db.commit()
        return None
    return transaction


def _discard_transaction(db: Session, state: str) -> None:
    transaction = db.query(OidcLoginTransaction).filter(
        OidcLoginTransaction.state == state,
        OidcLoginTransaction.consumed_at.is_(None),
    ).first()
    if transaction:
        transaction.consumed_at = _utcnow()
        db.commit()


def _jwk_for_token(id_token: str, document: dict) -> object:
    header = jwt.get_unverified_header(id_token)
    key_id = header.get("kid")
    for candidate in document.get("keys", []):
        if candidate.get("kid") == key_id:
            return jwk.construct(candidate)
    raise OidcUserError("OIDC 签名密钥不存在。")


def _verify_id_token(id_token: str, jwks: dict, transaction: OidcLoginTransaction) -> dict:
    try:
        claims = jwt.decode(
            id_token,
            _jwk_for_token(id_token, jwks),
            algorithms=["RS256"],
            audience=settings.OIDC_CLIENT_ID,
            issuer=_issuer(),
            options={"require": ["iss", "sub", "aud", "exp", "iat", "nonce"]},
        )
    except (JWTError, ValueError, KeyError) as exc:
        raise OidcUserError("ID Token 验证失败。") from exc
    issued_at = int(claims["iat"])
    if issued_at > int(_utcnow().timestamp()) + 60:
        raise OidcUserError("ID Token 的 iat 无效。")
    if not secrets.compare_digest(str(claims.get("nonce", "")), transaction.nonce):
        raise OidcUserError("OIDC nonce 校验失败。")
    if not claims.get("sub"):
        raise OidcUserError("ID Token 缺少 subject。")
    return claims


async def _exchange_code(transaction: OidcLoginTransaction, code: str) -> tuple[dict, dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            f"{_backchannel()}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.OIDC_REDIRECT_URI,
                "code_verifier": transaction.code_verifier,
            },
            auth=(settings.OIDC_CLIENT_ID, settings.OIDC_CLIENT_SECRET),
        )
        if token_response.status_code != 200:
            raise OidcUserError("OIDC 授权码兑换失败。")
        token_payload = token_response.json()
        id_token = token_payload.get("id_token")
        access_token = token_payload.get("access_token")
        if not id_token or not access_token:
            raise OidcUserError("OIDC Token 响应缺少必要字段。")

        jwks_response = await client.get(f"{_backchannel()}/.well-known/jwks.json")
        if jwks_response.status_code != 200:
            raise OidcUserError("OIDC 公钥获取失败。")
        claims = _verify_id_token(id_token, jwks_response.json(), transaction)

        userinfo_response = await client.get(
            f"{_backchannel()}/oauth/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_response.status_code != 200:
            raise OidcUserError("OIDC UserInfo 获取失败。")
        userinfo = userinfo_response.json()

    if str(userinfo.get("sub", "")) != str(claims.get("sub", "")):
        raise OidcUserError("ID Token 与 UserInfo 的 subject 不一致。")
    if not userinfo.get("organization_id") or not claims.get("organization_id"):
        raise OidcUserError("OIDC 响应缺少 organization_id。")
    if str(userinfo["organization_id"]) != str(claims["organization_id"]):
        raise OidcUserError("ID Token 与 UserInfo 的组织声明不一致。")
    if transaction.flow == "direct" and str(transaction.organization_id) != str(userinfo["organization_id"]):
        raise OidcUserError("OIDC 返回的组织与 Portal 服务入口不一致。")
    if not userinfo.get("email") and not claims.get("email"):
        raise OidcUserError("OIDC 响应缺少 email。")
    return claims, userinfo


def _viewer_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == "viewer").first()
    if role:
        return role
    role = Role(name="viewer", description="OIDC provisioned SkillHub viewer")
    db.add(role)
    db.flush()
    return role


def _new_username(db: Session, subject: str) -> str:
    prefix = f"oidc_{hashlib.sha256(subject.encode('utf-8')).hexdigest()[:16]}"
    username = prefix
    suffix = 1
    while db.query(User).filter(User.username == username).first():
        suffix += 1
        username = f"{prefix}_{suffix}"
    return username


def _upsert_local_user(db: Session, claims: dict, userinfo: dict) -> User:
    subject = str(claims["sub"])
    email = str(userinfo.get("email") or claims.get("email") or "").strip().lower()
    display_name = str(userinfo.get("name") or claims.get("name") or email).strip()
    if not email:
        raise OidcUserError("OIDC 用户 email 为空。")

    user = db.query(User).options(joinedload(User.roles)).filter(User.oidc_subject == subject).first()
    email_user = db.query(User).options(joinedload(User.roles)).filter(func.lower(User.email) == email).first()
    if user and email_user and user.id != email_user.id:
        raise OidcUserError("OIDC subject 与本地 email 绑定冲突。")
    if user is None and email_user is not None:
        if email_user.oidc_subject:
            raise OidcUserError("该 email 已绑定其他 OIDC 用户。")
        user = email_user
        user.oidc_subject = subject
    if user is not None:
        if not user.is_active:
            raise OidcUserError("SkillHub 本地账号已停用。")
        if user.email != email:
            conflicting = db.query(User).filter(
                func.lower(User.email) == email,
                User.id != user.id,
            ).first()
            if conflicting:
                raise OidcUserError("OIDC email 与其他本地账号冲突。")
            user.email = email
        db.add(user)
        db.flush()
        return user

    user = User(
        username=_new_username(db, subject),
        email=email,
        oidc_subject=subject,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
        is_active=True,
    )
    user.roles = [_viewer_role(db)]
    db.add(user)
    db.flush()
    return user


def _validate_transaction_identity(
    transaction: OidcLoginTransaction,
    claims: dict,
    userinfo: dict,
) -> None:
    """Re-check callback context even when the exchange implementation is mocked or replaced."""
    if str(claims.get("sub", "")) != str(userinfo.get("sub", "")):
        raise OidcUserError("ID Token 与 UserInfo 的 subject 不一致。")
    if not claims.get("organization_id") or not userinfo.get("organization_id"):
        raise OidcUserError("OIDC 响应缺少 organization_id。")
    if str(claims["organization_id"]) != str(userinfo["organization_id"]):
        raise OidcUserError("ID Token 与 UserInfo 的组织声明不一致。")
    if transaction.flow == "direct" and str(transaction.organization_id) != str(userinfo["organization_id"]):
        raise OidcUserError("OIDC 返回的组织与 Portal 服务入口不一致。")


@router.get("/start")
def start(
    organization_id: str = "",
    client_id: str = "",
    sso: str = "",
    db: Session = Depends(get_db),
):
    configuration_error = _configuration_error()
    if configuration_error:
        raise configuration_error

    sso_flow = sso == "1"
    if not sso_flow and not client_id:
        raise HTTPException(status_code=400, detail="Portal 服务入口缺少 client_id。")
    if client_id and client_id != settings.OIDC_CLIENT_ID:
        raise HTTPException(status_code=400, detail="OIDC client_id 与 SkillHub 配置不一致。")
    if sso_flow and organization_id:
        raise HTTPException(status_code=400, detail="SSO 请求不能携带 organization_id。")
    if not sso_flow and not organization_id:
        raise HTTPException(status_code=400, detail="Portal 服务入口缺少 organization_id。")

    transaction, verifier = _create_pkce_transaction(
        db,
        organization_id=organization_id or None,
        flow="sso" if sso_flow else "direct",
    )
    return RedirectResponse(_authorize_location(transaction, verifier), status_code=302, headers={"Cache-Control": "no-store"})


@router.get("/callback")
async def callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
    error_description: str = "",
    db: Session = Depends(get_db),
):
    if error:
        if state:
            _discard_transaction(db, state)
        return _frontend_error(error, error_description or "Portal OIDC 授权失败。")
    if not state or not code:
        return _frontend_error("invalid_request", "OIDC 回调缺少 state 或授权码。")

    transaction = _pending_transaction(db, state)
    if not transaction:
        return _frontend_error("invalid_request", "OIDC 登录事务不存在、已使用或已过期。")
    try:
        claims, userinfo = await _exchange_code(transaction, code)
        _validate_transaction_identity(transaction, claims, userinfo)
        user = _upsert_local_user(db, claims, userinfo)
        raw_ticket = secrets.token_urlsafe(48)
        ticket = SsoLoginTicket(
            ticket_digest=hashlib.sha256(raw_ticket.encode("utf-8")).hexdigest(),
            user_id=str(user.id),
            expires_at=_utcnow() + timedelta(seconds=settings.OIDC_TICKET_TTL_SECONDS),
        )
        transaction.consumed_at = _utcnow()
        db.add(ticket)
        db.commit()
    except (httpx.HTTPError, OidcUserError, JWTError, KeyError, ValueError) as exc:
        db.rollback()
        _discard_transaction(db, state)
        description = str(exc) if isinstance(exc, OidcUserError) else "OIDC 回调校验失败。"
        return _frontend_error("access_denied", description)
    except Exception:
        db.rollback()
        _discard_transaction(db, state)
        return _frontend_error("server_error", "SkillHub OIDC 登录处理失败。")

    response = RedirectResponse(_redirect_target(), status_code=302, headers={"Cache-Control": "no-store"})
    response.set_cookie(
        "skillhub_sso_ticket",
        raw_ticket,
        max_age=settings.OIDC_TICKET_TTL_SECONDS,
        httponly=True,
        secure=settings.OIDC_SECURE_COOKIE,
        samesite="lax",
        path="/api/v1/sso",
    )
    return response


@router.post("/exchange")
def exchange(request: Request, db: Session = Depends(get_db)):
    raw_ticket = request.cookies.get("skillhub_sso_ticket")
    if not raw_ticket:
        return JSONResponse({"detail": "SSO 登录票据不存在。"}, status_code=401)
    digest = hashlib.sha256(raw_ticket.encode("utf-8")).hexdigest()
    now = _utcnow()
    claimed = db.query(SsoLoginTicket).filter(
        SsoLoginTicket.ticket_digest == digest,
        SsoLoginTicket.consumed_at.is_(None),
        SsoLoginTicket.expires_at > now,
    ).update(
        {SsoLoginTicket.consumed_at: now},
        synchronize_session=False,
    )
    if claimed != 1:
        db.rollback()
        return JSONResponse({"detail": "SSO 登录票据无效、已使用或已过期。"}, status_code=401)

    ticket = db.query(SsoLoginTicket).filter(
        SsoLoginTicket.ticket_digest == digest,
    ).first()
    if not ticket:
        db.rollback()
        return JSONResponse({"detail": "SSO 登录票据无效、已使用或已过期。"}, status_code=401)
    user = db.query(User).filter(User.id == ticket.user_id).first()
    if not user or not user.is_active:
        db.commit()
        return JSONResponse({"detail": "SkillHub 本地账号不可用。"}, status_code=401)

    db.commit()
    try:
        tokens = AuthService.create_tokens(db, user)
    except Exception:
        return JSONResponse({"detail": "SkillHub 会话创建失败。"}, status_code=500)
    response = JSONResponse(tokens.model_dump())
    response.delete_cookie("skillhub_sso_ticket", path="/api/v1/sso")
    response.headers["Cache-Control"] = "no-store"
    return response
