"""
Authentication utilities, JWT tokens, and role-based access decorators.
"""
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional
import jwt
from flask import request, jsonify, g
from models import User

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'banana-slides-jwt-default-key')


def generate_token(user_id: str, email: str, role: str) -> str:
    """Generate a JWT token for a user valid for 30 days."""
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        logger.debug(f"Invalid JWT token: {e}")
        return None


def get_current_user() -> Optional[User]:
    """Retrieve the authenticated user from request headers or context."""
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
    elif request.headers.get('X-Auth-Token'):
        token = request.headers.get('X-Auth-Token', '').strip()
    elif request.cookies.get('auth_token'):
        token = request.cookies.get('auth_token', '').strip()

    if not token:
        g.current_user = None
        g._auth_token = None
        return None

    if getattr(g, '_auth_token', None) == token and getattr(g, 'current_user', None):
        return g.current_user

    payload = decode_token(token)
    if not payload or 'user_id' not in payload:
        g.current_user = None
        g._auth_token = None
        return None

    user = User.query.get(payload['user_id'])
    g.current_user = user
    g._auth_token = token
    return user


def login_required(f):
    """Decorator requiring valid user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'code': 'UNAUTHORIZED',
                'error': 'Vui lòng đăng nhập để tiếp tục'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator requiring admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({
                'code': 'UNAUTHORIZED',
                'error': 'Vui lòng đăng nhập để tiếp tục'
            }), 401
        if user.role != 'admin':
            return jsonify({
                'code': 'FORBIDDEN',
                'error': 'Yêu cầu quyền quản trị viên'
            }), 403
        return f(*args, **kwargs)
    return decorated_function
