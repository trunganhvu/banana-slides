"""
Authentication Controller - Google SSO, token issuance, and profile endpoints.
"""
import os
import logging
from datetime import datetime
import requests
from flask import Blueprint, request, jsonify, g
from models import db, User, Project
from utils.auth_middleware import generate_token, get_current_user, login_required

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _is_admin_email(email: str) -> bool:
    """Check if an email matches the configured admin emails."""
    raw = os.getenv('ADMIN_EMAILS', 'vutrunganh1@gmail.com')
    admin_emails = [e.strip().lower() for e in raw.split(',') if e.strip()]
    return email.strip().lower() in admin_emails


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

    try:
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        resp = requests.get(verify_url, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Google token verification failed with status {resp.status_code}: {resp.text}")
            return jsonify({
                'code': 'INVALID_TOKEN',
                'error': 'Xác thực tài khoản Google không thành công'
            }), 401

        payload = resp.json()
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

        # If user is admin (or specifically vutrunganh1@gmail.com), assign unassigned legacy projects
        if is_admin:
            unassigned_count = Project.query.filter(Project.user_id.is_(None)).count()
            if unassigned_count > 0:
                Project.query.filter(Project.user_id.is_(None)).update(
                    {Project.user_id: user.id},
                    synchronize_session=False
                )
                logger.info(f"Assigned {unassigned_count} orphaned projects to admin {email}")

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
    body = request.get_json(silent=True) or {}
    email = (body.get('email') or 'vutrunganh1@gmail.com').strip()
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
