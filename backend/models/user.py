"""
User model for authentication and usage metrics.
"""
import uuid
from datetime import datetime
from . import db


class User(db.Model):
    """
    User model - represents a registered user via Google SSO.
    """
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=True)
    avatar = db.Column(db.String(500), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True, index=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' | 'admin'
    login_count = db.Column(db.Integer, nullable=False, default=0)
    generation_count = db.Column(db.Integer, nullable=False, default=0)
    tokens_in = db.Column(db.BigInteger, nullable=False, default=0)
    tokens_out = db.Column(db.BigInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    projects = db.relationship('Project', back_populates='user', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'avatar': self.avatar,
            'role': self.role,
            'login_count': self.login_count,
            'generation_count': self.generation_count,
            'tokens_in': self.tokens_in,
            'tokens_out': self.tokens_out,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() + 'Z' if self.last_login_at else None,
        }
