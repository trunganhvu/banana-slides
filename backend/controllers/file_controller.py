"""
File Controller - handles static file serving
"""
from flask import Blueprint, send_from_directory, current_app
from utils import error_response, not_found
from utils.path_utils import find_file_with_prefix
import os
from pathlib import Path
from typing import Optional
from werkzeug.utils import secure_filename

file_bp = Blueprint('files', __name__, url_prefix='/files')


def _is_safe_path_segment(segment: str) -> bool:
    """Validate a single URL path segment against traversal or separator injection."""
    if not segment or segment in ('.', '..'):
        return False
    return '/' not in segment and '\\' not in segment and '\x00' not in segment


def _resolve_contained_path(base_dir: Path, *parts: str) -> Optional[Path]:
    """Resolve a path under base_dir and verify strict directory containment."""
    try:
        resolved_base = base_dir.resolve()
        resolved_target = base_dir.joinpath(*parts).resolve()
        resolved_target.relative_to(resolved_base)
    except (ValueError, OSError):
        return None
    if resolved_target == resolved_base:
        return None
    return resolved_target


@file_bp.route('/<project_id>/<file_type>/<filename>', methods=['GET'])
def serve_file(project_id, file_type, filename):
    """
    GET /files/{project_id}/{type}/{filename} - Serve static files
    
    Args:
        project_id: Project UUID
        file_type: 'template' or 'pages'
        filename: File name
    """
    try:
        if file_type not in ['template', 'pages', 'materials', 'exports']:
            return not_found('File')

        if not _is_safe_path_segment(project_id) or not _is_safe_path_segment(filename):
            return error_response('INVALID_PATH', 'Invalid file path', 403)

        upload_root = Path(current_app.config['UPLOAD_FOLDER'])
        file_dir = _resolve_contained_path(upload_root, project_id, file_type)
        if file_dir is None:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_dir.exists() or not file_dir.is_dir():
            return not_found('File')

        file_path = _resolve_contained_path(file_dir, filename)
        if file_path is None:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_path.exists() or not file_path.is_file():
            return not_found('File')

        # Exports should be downloaded rather than opened in browser for better UX and
        # to keep E2E download assertions stable.
        as_attachment = file_type == 'exports'
        return send_from_directory(str(file_dir), file_path.name, as_attachment=as_attachment)
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@file_bp.route('/<project_id>/template-assets/<asset_id>/<filename>', methods=['GET'])
def serve_template_asset(project_id, asset_id, filename):
    """
    GET /files/{project_id}/template-assets/{asset_id}/{filename}

    Serve per-project template asset files (original.* and thumb.jpg).
    """
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename:
            return not_found('File')

        root = Path(current_app.config['UPLOAD_FOLDER']).resolve()
        file_dir = (root / project_id / 'template-assets' / asset_id).resolve()

        try:
            file_dir.relative_to(root)
        except ValueError:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_dir.exists() or not file_dir.is_dir():
            return not_found('File')

        file_path = (file_dir / safe_filename).resolve()
        try:
            file_path.relative_to(file_dir)
        except ValueError:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_path.exists() or not file_path.is_file():
            return not_found('File')

        return send_from_directory(str(file_dir), safe_filename)

    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@file_bp.route('/user-templates/<template_id>/<filename>', methods=['GET'])
def serve_user_template(template_id, filename):
    """
    GET /files/user-templates/{template_id}/{filename} - Serve user template files
    
    Args:
        template_id: Template UUID
        filename: File name
    """
    try:
        if not _is_safe_path_segment(template_id) or not _is_safe_path_segment(filename):
            return error_response('INVALID_PATH', 'Invalid file path', 403)

        user_templates_root = Path(current_app.config['UPLOAD_FOLDER']) / 'user-templates'
        file_dir = _resolve_contained_path(user_templates_root, template_id)
        if file_dir is None:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_dir.exists() or not file_dir.is_dir():
            return not_found('File')

        file_path = _resolve_contained_path(file_dir, filename)
        if file_path is None:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_path.exists() or not file_path.is_file():
            return not_found('File')

        # Serve file
        return send_from_directory(str(file_dir), file_path.name)
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@file_bp.route('/materials/<filename>', methods=['GET'])
def serve_global_material(filename):
    """
    GET /files/materials/{filename} - Serve global material files (not bound to a project)
    
    Args:
        filename: File name
    """
    try:
        safe_filename = secure_filename(filename)
        if not safe_filename:
            return not_found('File')

        materials_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'materials'
        if not materials_dir.exists() or not materials_dir.is_dir():
            return not_found('File')

        file_path = _resolve_contained_path(materials_dir, safe_filename)
        if file_path is None:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if not file_path.exists() or not file_path.is_file():
            return not_found('File')

        # Serve file
        return send_from_directory(str(materials_dir.resolve()), file_path.name)
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@file_bp.route('/mineru/<extract_id>/<path:filepath>', methods=['GET'])
def serve_mineru_file(extract_id, filepath):
    """
    GET /files/mineru/{extract_id}/{filepath} - Serve MinerU extracted files.

    Args:
        extract_id: Extract UUID
        filepath: Relative file path within the extract
    """
    try:
        if not _is_safe_path_segment(extract_id):
            return error_response('INVALID_PATH', 'Invalid file path', 403)

        mineru_root = Path(current_app.config['UPLOAD_FOLDER']) / 'mineru_files'
        resolved_root_dir = _resolve_contained_path(mineru_root, extract_id)
        if resolved_root_dir is None:
            return error_response('INVALID_PATH', 'Invalid file path', 403)

        full_path = resolved_root_dir / filepath
        try:
            # Verify strict containment inside extract_id directory (prevents sibling-prefix escape)
            resolved_full_path = full_path.resolve()
            resolved_full_path.relative_to(resolved_root_dir)
        except Exception:
            return error_response('INVALID_PATH', 'Invalid file path', 403)
        if resolved_full_path == resolved_root_dir:
            return error_response('INVALID_PATH', 'Invalid file path', 403)

        # Try to find file with prefix matching
        matched_path = find_file_with_prefix(resolved_full_path)

        if matched_path is not None:
            try:
                resolved_matched_path = matched_path.resolve(strict=True)
                resolved_matched_path.relative_to(resolved_root_dir)
            except FileNotFoundError:
                return not_found('File')
            except Exception:
                return error_response('INVALID_PATH', 'Invalid file path', 403)

            return send_from_directory(str(resolved_matched_path.parent), resolved_matched_path.name)

        return not_found('File')
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)
