"""
Authentication Controller - Google SSO, token issuance, and profile endpoints.
"""
import os
import logging
from datetime import datetime
import requests
from flask import Blueprint, request, jsonify, g, current_app
from models import db, User, Project
from utils.auth_middleware import generate_token, get_current_user, login_required

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _is_admin_email(email: str) -> bool:
    """Check if an email matches the configured admin emails."""
    raw = os.getenv('ADMIN_EMAILS', '')
    admin_emails = [e.strip().lower() for e in raw.split(',') if e.strip()]
    if not admin_emails:
        return False
    return email.strip().lower() in admin_emails


def _is_dev_login_enabled() -> bool:
    """Allow dev login only in testing mode or when explicitly enabled."""
    if current_app.config.get('TESTING'):
        return True
    return os.getenv('ENABLE_DEV_LOGIN', '').strip().lower() in ('1', 'true', 'yes')


@auth_bp.route('/config', methods=['GET'])
def get_auth_config():
    """Return public authentication configuration."""
    client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
    return jsonify({
        'code': 0,
        'data': {
            'google_client_id': client_id,
            'enabled': bool(client_id)
        }
    })


@auth_bp.route('/google', methods=['POST'])
def google_sso_login():
    """
    Authenticate a user using a Google Identity Services credential (ID Token).
    Verifies the token with Google, creates or updates the user, and returns a JWT.
    """
    body = request.get_json(silent=True) or {}
    credential = body.get('credential')
    if not credential:
        return jsonify({
            'code': 'PARAM_REQUIRED',
            'error': 'Thiếu Google credential'
        }), 400

    expected_client_id = os.getenv('GOOGLE_CLIENT_ID', '').strip()
    if not expected_client_id:
        return jsonify({
            'code': 'AUTH_NOT_CONFIGURED',
            'error': 'Chưa cấu hình GOOGLE_CLIENT_ID trên máy chủ'
        }), 503

    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={'id_token': credential},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"Google token verification failed with status {resp.status_code}: {resp.text}")
            return jsonify({
                'code': 'INVALID_TOKEN',
                'error': 'Xác thực tài khoản Google không thành công'
            }), 401

        payload = resp.json()
        if payload.get('aud') != expected_client_id:
            logger.warning("Google token audience mismatch: %s", payload.get('aud'))
            return jsonify({
                'code': 'INVALID_TOKEN_AUDIENCE',
                'error': 'Google token không hợp lệ cho ứng dụng này'
            }), 401

        issuer = payload.get('iss')
        if issuer and issuer not in ('accounts.google.com', 'https://accounts.google.com'):
            logger.warning("Google token issuer mismatch: %s", issuer)
            return jsonify({
                'code': 'INVALID_TOKEN_ISSUER',
                'error': 'Nguồn xác thực Google token không hợp lệ'
            }), 401

        if str(payload.get('email_verified', '')).lower() != 'true':
            return jsonify({
                'code': 'EMAIL_NOT_VERIFIED',
                'error': 'Email Google chưa được xác minh'
            }), 401

        email = payload.get('email')
        if not email:
            return jsonify({
                'code': 'INVALID_PROFILE',
                'error': 'Tài khoản Google không có email'
            }), 400

        name = payload.get('name') or email.split('@')[0]
        avatar = payload.get('picture')
        google_id = payload.get('sub')
        is_admin = _is_admin_email(email)

        user = User.query.filter_by(email=email).first()
        if not user:
            # Check if this is the very first user in the system
            if User.query.count() == 0:
                is_admin = True

            user = User(
                email=email,
                name=name,
                avatar=avatar,
                google_id=google_id,
                role='admin' if is_admin else 'user',
                login_count=1,
                last_login_at=datetime.utcnow()
            )
            db.session.add(user)
        else:
            user.name = name or user.name
            user.avatar = avatar or user.avatar
            user.google_id = google_id or user.google_id
            if is_admin:
                user.role = 'admin'
            user.login_count = (user.login_count or 0) + 1
            user.last_login_at = datetime.utcnow()

        db.session.flush()

        # If user is admin, assign unassigned legacy projects
        if is_admin:
            unassigned_count = Project.query.filter(Project.user_id.is_(None)).count()
            if unassigned_count > 0:
                Project.query.filter(Project.user_id.is_(None)).update(
                    {Project.user_id: user.id},
                    synchronize_session=False
                )
                logger.info(f"Assigned {unassigned_count} orphaned projects to admin")

        db.session.commit()

        token = generate_token(user.id, user.email, user.role)
        return jsonify({
            'code': 0,
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Google login failed: {e}", exc_info=True)
        return jsonify({
            'code': 'AUTH_FAILED',
            'error': f'Lỗi đăng nhập: {str(e)}'
        }), 500


@auth_bp.route('/dev-login', methods=['POST'])
def dev_login():
    """Fast login endpoint for local testing or dev fallback."""
    if not _is_dev_login_enabled():
        return jsonify({
            'code': 'DEV_LOGIN_DISABLED',
            'error': 'Dev login bị tắt trong môi trường production'
        }), 403

    raw_admin = os.getenv('ADMIN_EMAILS', '')
    admin_emails = [e.strip() for e in raw_admin.split(',') if e.strip()]
    default_email = admin_emails[0] if admin_emails else 'admin@example.com'

    body = request.get_json(silent=True) or {}
    email = (body.get('email') or default_email).strip()
    name = body.get('name') or email.split('@')[0]
    is_admin = _is_admin_email(email)

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                name=name,
                role='admin' if is_admin else 'user',
                login_count=1,
                last_login_at=datetime.utcnow()
            )
            db.session.add(user)
        else:
            if is_admin:
                user.role = 'admin'
            user.login_count = (user.login_count or 0) + 1
            user.last_login_at = datetime.utcnow()

        db.session.flush()

        if is_admin:
            Project.query.filter(Project.user_id.is_(None)).update(
                {Project.user_id: user.id},
                synchronize_session=False
            )

        db.session.commit()

        token = generate_token(user.id, user.email, user.role)
        return jsonify({
            'code': 0,
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Dev login failed: {e}", exc_info=True)
        return jsonify({'code': 'ERROR', 'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user_profile():
    """Return the profile of the currently authenticated user."""
    user = get_current_user()
    return jsonify({
        'code': 0,
        'data': {
            'user': user.to_dict()
        }
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Client-side token disposal confirmation."""
    return jsonify({
        'code': 0,
        'data': {
            'success': True
        }
    })
