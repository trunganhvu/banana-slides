"""
Usage tracking service for tokens and generations.
"""
import logging
from flask import g, has_request_context
from models import db, User, Project

logger = logging.getLogger(__name__)


def record_usage(tokens_in: int = 0, tokens_out: int = 0, generation: bool = False, user_id: str = None, project_id: str = None):
    """
    Record token usage and generations for a user.
    Can resolve user from user_id, project_id, or request context g.current_user.
    """
    try:
        target_user_id = user_id

        if not target_user_id and project_id:
            try:
                project = Project.query.get(project_id)
                if project and project.user_id:
                    target_user_id = project.user_id
            except Exception as pe:
                logger.debug(f"Could not resolve project for usage: {pe}")

        if not target_user_id and has_request_context():
            user = getattr(g, 'current_user', None)
            if user:
                target_user_id = user.id

        if not target_user_id:
            # Fallback to admin or first user in system
            user = User.query.filter_by(role='admin').first() or User.query.first()
            if user:
                target_user_id = user.id

        if target_user_id:
            user = User.query.get(target_user_id)
            if user:
                user.tokens_in = (user.tokens_in or 0) + max(0, int(tokens_in or 0))
                user.tokens_out = (user.tokens_out or 0) + max(0, int(tokens_out or 0))
                if generation:
                    user.generation_count = (user.generation_count or 0) + 1
                db.session.commit()
    except Exception as e:
        logger.debug(f"Failed to record usage: {e}")
