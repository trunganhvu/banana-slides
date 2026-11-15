"""
Admin Controller - Minimalist system monitoring and user analytics.
"""
import logging
from flask import Blueprint, jsonify
from models import db, User, Project
from utils.auth_middleware import admin_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_system_stats():
    """
    Return high-level summary statistics:
    - Total users
    - Total visits (logins)
    - Total generations
    - Total tokens in / out
    - Total projects across all users
    """
    try:
        total_users = User.query.count()
        total_projects = Project.query.count()

        totals = db.session.query(
            db.func.sum(User.login_count).label('visits'),
            db.func.sum(User.generation_count).label('generations'),
            db.func.sum(User.tokens_in).label('tokens_in'),
            db.func.sum(User.tokens_out).label('tokens_out')
        ).first()

        total_visits = int(totals.visits or 0)
        total_generations = int(totals.generations or 0)
        total_tokens_in = int(totals.tokens_in or 0)
        total_tokens_out = int(totals.tokens_out or 0)

        return jsonify({
            'code': 0,
            'data': {
                'total_users': total_users,
                'total_visits': total_visits,
                'total_generations': total_generations,
                'total_tokens_in': total_tokens_in,
                'total_tokens_out': total_tokens_out,
                'total_projects': total_projects
            }
        })
    except Exception as e:
        logger.error(f"Failed to fetch admin stats: {e}", exc_info=True)
        return jsonify({'code': 'ERROR', 'error': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_admin_users():
    """
    Return user list with per-user usage and project counts.
    """
    try:
        users = User.query.order_by(User.created_at.desc()).all()

        user_list = []
        for u in users:
            proj_count = Project.query.filter_by(user_id=u.id).count()
            u_dict = u.to_dict()
            u_dict['project_count'] = proj_count
            user_list.append(u_dict)

        return jsonify({
            'code': 0,
            'data': {
                'users': user_list
            }
        })
    except Exception as e:
        logger.error(f"Failed to fetch admin users: {e}", exc_info=True)
        return jsonify({'code': 'ERROR', 'error': str(e)}), 500
