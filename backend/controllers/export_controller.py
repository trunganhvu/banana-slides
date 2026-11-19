"""
Export Controller - handles file export endpoints
"""
import hashlib
import logging
import json
import os
import io
import shutil
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
from models import db, Project, Page, Task
from utils import (
    error_response, not_found, bad_request, success_response,
    parse_page_ids_from_query, parse_page_ids_from_body, get_filtered_pages
)
from utils.client_settings import get_current_client_override, extract_client_settings_from_request
from utils.filename_utils import build_export_filename
from services import ExportService, FileService
from services.ai_service_manager import get_ai_service
from services.html_slide_service import ensure_html_pages_rendered
from services.prompts import normalize_narration_generation_config

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/api/projects')

EDITABLE_EXPORT_CACHE_VERSION = 1


def _sha256_file(path: Path) -> str:
    """Return hex SHA-256 digest of a file, or empty string if missing."""
    try:
        if not path.is_file():
            return ''
        digest = hashlib.sha256()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ''


def compute_editable_export_cache_key(
    project,
    pages,
    upload_folder: str,
    *,
    max_depth: int,
    export_extractor_method: str,
    export_inpaint_method: str,
    enable_icon_subject_extraction: bool,
    export_allow_partial: bool,
) -> str:
    """Compute a deterministic content fingerprint for an editable PPTX export."""
    upload_root = Path(upload_folder)
    page_fingerprints = []
    for page in pages:
        img_digest = ''
        if getattr(page, 'generated_image_path', None):
            raw_img_path = Path(page.generated_image_path)
            img_path = raw_img_path if raw_img_path.is_absolute() else (upload_root / raw_img_path)
            img_digest = _sha256_file(img_path)

        html_path = upload_root / project.id / 'pages' / f'{page.id}.html'
        html_digest = _sha256_file(html_path) if html_path.is_file() else ''

        page_fingerprints.append({
            'id': page.id,
            'img': img_digest,
            'html': html_digest,
        })

    payload = {
        'v': EDITABLE_EXPORT_CACHE_VERSION,
        'max_depth': int(max_depth),
        'extractor': str(export_extractor_method or 'gemini').lower(),
        'inpaint': str(export_inpaint_method or 'opencv').lower(),
        'icon_subject': bool(enable_icon_subject_extraction),
        'allow_partial': bool(export_allow_partial),
        'pages': page_fingerprints,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _find_reusable_editable_export_task(project_id: str, cache_key: str, exports_root: Path):
    """Find a completed cached export file or a live in-flight export matching cache_key."""
    recent_tasks = (
        Task.query
        .filter(
            Task.project_id == project_id,
            Task.task_type == 'EXPORT_EDITABLE_PPTX',
        )
        .order_by(Task.created_at.desc())
        .limit(50)
        .all()
    )

    for task in recent_tasks:
        if task.status != 'COMPLETED':
            continue
        progress = task.get_progress() or {}
        if progress.get('export_cache_key') != cache_key:
            continue
        cached_filename = progress.get('filename')
        if not cached_filename or secure_filename(cached_filename) != cached_filename:
            continue
        if exports_root is None:
            continue
        file_path = (exports_root / cached_filename).resolve()
        try:
            file_path.relative_to(exports_root)
        except ValueError:
            continue
        if file_path.is_file():
            return 'completed', task, progress

    for task in recent_tasks:
        if task.status not in ('PENDING', 'PROCESSING', 'RUNNING'):
            continue
        progress = task.get_progress() or {}
        if progress.get('export_cache_key') != cache_key:
            continue
        from services.task_watchdog import reconcile_task_for_response
        reconcile_task_for_response(task)
        if task.status in ('PENDING', 'PROCESSING', 'RUNNING'):
            return 'in_flight', task, progress

    return None, None, None


def _parse_pptx_transition_effects():
    enabled = request.args.get('transition_enabled', '').lower() in {'1', 'true', 'yes', 'on'}
    if not enabled:
        return [], None

    effects = list(dict.fromkeys(
        effect.strip()
        for effect in request.args.get('transition_effects', '').split(',')
        if effect.strip()
    ))
    valid_effects = [effect for effect in effects if effect in ExportService.PPTX_TRANSITION_EFFECTS]
    if not valid_effects:
        return [], "At least one valid transition effect is required"
    return valid_effects, None


def _resolve_exports_root(project_id):
    upload_folder = Path(current_app.config['UPLOAD_FOLDER']).resolve()
    exports_root = (upload_folder / project_id / 'exports').resolve()
    try:
        exports_root.relative_to(upload_folder)
    except ValueError:
        return None
    return exports_root


@export_bp.route('/<project_id>/exports', methods=['GET'])
def list_exports(project_id):
    """
    GET /api/projects/{project_id}/exports - 

     exports  (, , , ) . 
    """
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return not_found('Project')

        exports_root = _resolve_exports_root(project_id)
        if exports_root is None:
            return bad_request('Invalid project ID')

        if not exports_root.is_dir():
            return success_response(data={"files": []})

        files = []
        for filepath in sorted(exports_root.iterdir(), key=lambda path: path.name):
            name = filepath.name
            if not filepath.is_file():
                continue
            # Backend logic
            if name.startswith('.') or name.startswith('_'):
                continue

            stat = filepath.stat()
            ext = os.path.splitext(name)[1].lower()
            file_type = {
                '.mp4': 'video', '.pptx': 'pptx', '.pdf': 'pdf',
                '.zip': 'images', '.png': 'image', '.jpg': 'image',
            }.get(ext, 'other')

            files.append({
                "filename": name,
                "type": file_type,
                "size": stat.st_size,
                "modified_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(stat.st_mtime)),
                "download_url": f"/files/{project_id}/exports/{name}",
            })

        # Backend logic
        files.sort(key=lambda f: f['modified_at'], reverse=True)

        return success_response(data={"files": files})

    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/exports/<filename>', methods=['DELETE'])
def delete_export(project_id, filename):
    """
    DELETE /api/projects/{project_id}/exports/{filename} - 
    """
    try:
        project = db.session.get(Project, project_id)
        if not project:
            return not_found('Project')

        safe_filename = secure_filename(filename)
        if not safe_filename or safe_filename != filename:
            return bad_request('Invalid export filename')

        exports_root = _resolve_exports_root(project_id)
        if exports_root is None:
            return bad_request('Invalid project ID')
        file_path = (exports_root / safe_filename).resolve()

        try:
            file_path.relative_to(exports_root)
        except ValueError:
            return bad_request('Invalid export filename')

        if not file_path.is_file():
            return not_found('File')

        file_path.unlink()
        return success_response(data={"filename": safe_filename}, message="Export file deleted")

    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/export/pptx', methods=['GET'])
def export_pptx(project_id):
    """
    GET /api/projects/{project_id}/export/pptx?filename=...&page_ids=id1,id2,id3 - Export PPTX
    
    Query params:
        - filename: optional custom filename
        - page_ids: optional comma-separated page IDs to export (if not provided, exports all pages)
    
    Returns:
        JSON with download URL, e.g.
        {
            "success": true,
            "data": {
                "download_url": "/files/{project_id}/exports/xxx.pptx",
                "download_url_absolute": "http://host:port/files/{project_id}/exports/xxx.pptx"
            }
        }
    """
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return not_found('Project')
        
        # Get page_ids from query params and fetch filtered pages
        selected_page_ids = parse_page_ids_from_query(request)
        logger.debug(f"[export_pptx] selected_page_ids: {selected_page_ids}")
        
        pages = get_filtered_pages(project_id, selected_page_ids if selected_page_ids else None)
        logger.debug(f"[export_pptx] Exporting {len(pages)} pages")
        
        if not pages:
            return bad_request("No pages found for project")
        
        # Get image paths
        file_service = FileService(current_app.config['UPLOAD_FOLDER'])
        ensure_html_pages_rendered(pages, project, file_service, max_workers=4, db_session=db.session)
        
        image_paths = []
        for page in pages:
            if page.generated_image_path:
                abs_path = file_service.get_absolute_path(page.generated_image_path)
                image_paths.append(abs_path)
        
        if not image_paths:
            return bad_request("No generated images found for project")
        
        # Determine export directory and filename
        exports_dir = file_service._get_exports_dir(project_id)

        # Build concise friendly filename from project title / content
        filename = build_export_filename(
            project,
            '.pptx',
            requested_filename=request.args.get('filename'),
            pages=pages,
        )

        output_path = os.path.join(exports_dir, filename)

        transition_effects, transition_error = _parse_pptx_transition_effects()
        if transition_error:
            return bad_request(transition_error)

        # Generate PPTX file on disk
        ExportService.create_pptx_from_images(
            image_paths,
            output_file=output_path,
            aspect_ratio=project.image_aspect_ratio,
            transition_effects=transition_effects,
        )

        # Build download URLs
        download_path = f"/files/{project_id}/exports/{filename}"
        base_url = request.url_root.rstrip("/")
        download_url_absolute = f"{base_url}{download_path}"

        return success_response(
            data={
                "filename": filename,
                "download_url": download_path,
                "download_url_absolute": download_url_absolute,
            },
            message="Export PPTX task created"
        )
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/export/pdf', methods=['GET'])
def export_pdf(project_id):
    """
    GET /api/projects/{project_id}/export/pdf?filename=...&page_ids=id1,id2,id3 - Export PDF
    
    Query params:
        - filename: optional custom filename
        - page_ids: optional comma-separated page IDs to export (if not provided, exports all pages)
    
    Returns:
        JSON with download URL, e.g.
        {
            "success": true,
            "data": {
                "download_url": "/files/{project_id}/exports/xxx.pdf",
                "download_url_absolute": "http://host:port/files/{project_id}/exports/xxx.pdf"
            }
        }
    """
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return not_found('Project')
        
        # Get page_ids from query params and fetch filtered pages
        selected_page_ids = parse_page_ids_from_query(request)
        pages = get_filtered_pages(project_id, selected_page_ids if selected_page_ids else None)
        
        if not pages:
            return bad_request("No pages found for project")
        
        # Get image paths
        file_service = FileService(current_app.config['UPLOAD_FOLDER'])
        ensure_html_pages_rendered(pages, project, file_service, max_workers=4, db_session=db.session)
        
        image_paths = []
        for page in pages:
            if page.generated_image_path:
                abs_path = file_service.get_absolute_path(page.generated_image_path)
                image_paths.append(abs_path)
        
        if not image_paths:
            return bad_request("No generated images found for project")
        
        # Determine export directory and filename
        exports_dir = file_service._get_exports_dir(project_id)

        # Build concise friendly filename from project title / content
        filename = build_export_filename(
            project,
            '.pdf',
            requested_filename=request.args.get('filename'),
            pages=pages,
        )

        output_path = os.path.join(exports_dir, filename)

        # Generate PDF file on disk
        ExportService.create_pdf_from_images(image_paths, output_file=output_path, aspect_ratio=project.image_aspect_ratio)

        # Build download URLs
        download_path = f"/files/{project_id}/exports/{filename}"
        base_url = request.url_root.rstrip("/")
        download_url_absolute = f"{base_url}{download_path}"

        return success_response(
            data={
                "filename": filename,
                "download_url": download_path,
                "download_url_absolute": download_url_absolute,
            },
            message="Export PDF task created"
        )
    
    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/export/images', methods=['GET'])
def export_images(project_id):
    """
    GET /api/projects/{project_id}/export/images?page_ids=id1,id2,id3 - Export images

    Single image: copies to exports dir and returns download URL.
    Multiple images: creates a ZIP archive and returns download URL.
    """
    try:
        if '..' in project_id or '/' in project_id or '\\' in project_id:
            return bad_request('Invalid project ID')
        s_project_id = secure_filename(project_id)
        if s_project_id != project_id:
            return bad_request('Invalid project ID')

        project = Project.query.get(s_project_id)
        if not project:
            return not_found('Project')

        selected_page_ids = parse_page_ids_from_query(request)
        pages = get_filtered_pages(s_project_id, selected_page_ids if selected_page_ids else None)
        if not pages:
            return bad_request("No pages found for project")

        file_service = FileService(current_app.config['UPLOAD_FOLDER'])
        ensure_html_pages_rendered(pages, project, file_service, max_workers=4, db_session=db.session)

        image_items = []
        for page in pages:
            if page.generated_image_path:
                abs_path = file_service.get_absolute_path(page.generated_image_path)
                if os.path.exists(abs_path):
                    image_items.append((page, abs_path))

        if not image_items:
            return bad_request("No generated images found for project")

        exports_dir = file_service._get_exports_dir(s_project_id)
        requested_img_filename = request.args.get('filename')

        if len(image_items) == 1:
            page, path = image_items[0]
            ext = os.path.splitext(path)[1] or '.png'
            filename = build_export_filename(
                project,
                ext,
                requested_filename=requested_img_filename,
                suffix=f'-slide-{page.order_index + 1}',
                pages=pages,
            )
            output_path = os.path.join(exports_dir, filename)
            shutil.copy2(path, output_path)
        else:
            filename = build_export_filename(
                project,
                '.zip',
                requested_filename=requested_img_filename,
                suffix='-slides',
                pages=pages,
            )
            output_path = os.path.join(exports_dir, filename)
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for page, path in image_items:
                    ext = os.path.splitext(path)[1] or '.png'
                    zf.write(path, f'slide_{page.order_index + 1:03d}{ext}')

        download_path = f"/files/{s_project_id}/exports/{filename}"
        base_url = request.url_root.rstrip("/")

        return success_response(
            data={
                "filename": filename,
                "download_url": download_path,
                "download_url_absolute": f"{base_url}{download_path}",
            },
            message="Export images completed"
        )

    except Exception as e:
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/export/editable-pptx', methods=['POST'])
def export_editable_pptx(project_id):
    """
    POST /api/projects/{project_id}/export/editable-pptx - PPTX () 
    
     (, ) 
    
    : 
    1.  () 
    2. PDFMinerU
    3. bboxclean background (inpainting) 
    4. /
    5. PPTX
    
    Request body (JSON):
        {
            "filename": "optional_custom_name.pptx",
            "page_ids": ["id1", "id2"], // tùy chọn, Các trang cần xuấtIDdanh sách (Nếu không cung cấp sẽ xuất tất cả) 
            "client_task_id": "uuid", // tùy chọn, dùng để thử lại an toàn yêu cầu khởi tạo
            "max_depth": 1, // tùy chọn, Độ sâu đệ quy (mặc định1=không đệ quy, 2=đệ quy một tầng) 
            "max_workers": 4 // tùy chọn, Số luồng đồng thời (mặc định4) 
        }
    
    Returns:
        JSON with task_id, e.g.
        {
            "success": true,
            "data": {
                "task_id": "uuid-here",
                "method": "recursive_analysis",
                "max_depth": 2,
                "max_workers": 4
            },
            "message": "Export task created"
        }
    
     /api/projects/{project_id}/tasks/{task_id} 
    """
    try:
        project = Project.query.get(project_id)
        
        if not project:
            return not_found('Project')
        
        # Get parameters from request body
        data = request.get_json() or {}

        client_task_id = data.get('client_task_id')
        if client_task_id is not None:
            try:
                client_task_id = str(uuid.UUID(str(client_task_id)))
            except (ValueError, TypeError, AttributeError):
                return bad_request("client_task_id must be a valid UUID")

            existing_task = db.session.get(Task, client_task_id)
            if existing_task:
                if (
                    existing_task.project_id != project_id
                    or existing_task.task_type != 'EXPORT_EDITABLE_PPTX'
                ):
                    return error_response(
                        'EXPORT_TASK_ID_CONFLICT',
                        'client_task_id is already used by another task',
                        409,
                    )
                return success_response(
                    data={
                        "task_id": existing_task.id,
                        "method": "recursive_analysis",
                        "reused": True,
                    },
                    message="Existing export task returned",
                )
        
        # Get page_ids from request body and fetch filtered pages
        selected_page_ids = parse_page_ids_from_body(data)
        pages = get_filtered_pages(project_id, selected_page_ids if selected_page_ids else None)
        
        if not pages:
            return bad_request("No pages found for project")
        
        # Check if pages have generated images
        has_images = any(page.generated_image_path for page in pages)
        if not has_images:
            return bad_request("No generated images found for project")
        
        # Get parameters from already-parsed request body
        filename = build_export_filename(
            project,
            '.pptx',
            requested_filename=data.get('filename'),
            suffix='-editable',
            pages=pages,
        )
        
        max_depth = data.get('max_depth', 1)
        max_workers = data.get('max_workers', 4)
        force = bool(data.get('force', False))
        
        # Validate parameters
        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 5:
            return bad_request("max_depth must be an integer between 1 and 5")
        
        if not isinstance(max_workers, int) or max_workers < 1 or max_workers > 16:
            return bad_request("max_workers must be an integer between 1 and 16")

        export_extractor_method = project.export_extractor_method or 'gemini'
        export_inpaint_method = project.export_inpaint_method or 'opencv'
        enable_icon_subject_extraction = (
            True if project.enable_icon_subject_extraction is None
            else bool(project.enable_icon_subject_extraction)
        )
        export_allow_partial = bool(getattr(project, 'export_allow_partial', False))

        cache_key = compute_editable_export_cache_key(
            project,
            pages,
            current_app.config['UPLOAD_FOLDER'],
            max_depth=max_depth,
            export_extractor_method=export_extractor_method,
            export_inpaint_method=export_inpaint_method,
            enable_icon_subject_extraction=enable_icon_subject_extraction,
            export_allow_partial=export_allow_partial,
        )

        if not force:
            exports_root = _resolve_exports_root(project_id)
            hit_kind, cached_task, cached_progress = _find_reusable_editable_export_task(
                project_id,
                cache_key,
                exports_root,
            )
            if hit_kind == 'completed':
                cached_filename = cached_progress.get('filename') or filename
                cached_download_url = (
                    cached_progress.get('download_url')
                    or f"/files/{project_id}/exports/{cached_filename}"
                )
                logger.info(
                    "Reused cached editable PPTX for project %s (task=%s, file=%s, cache_key=%s)",
                    project_id,
                    cached_task.id,
                    cached_filename,
                    cache_key[:12],
                )
                return success_response(
                    data={
                        "task_id": cached_task.id,
                        "filename": cached_filename,
                        "download_url": cached_download_url,
                        "method": "recursive_analysis",
                        "max_depth": max_depth,
                        "max_workers": max_workers,
                        "cached": True,
                        "reused": True,
                    },
                    message="Reused previously exported editable PPTX (no AI calls)",
                )
            if hit_kind == 'in_flight':
                logger.info(
                    "Reused in-flight editable PPTX task for project %s (task=%s, cache_key=%s)",
                    project_id,
                    cached_task.id,
                    cache_key[:12],
                )
                return success_response(
                    data={
                        "task_id": cached_task.id,
                        "filename": cached_progress.get('filename') or filename,
                        "method": "recursive_analysis",
                        "max_depth": max_depth,
                        "max_workers": max_workers,
                        "cached": False,
                        "reused": True,
                    },
                    message="Existing in-flight export task returned",
                )

        # Check AI configuration (Google API Key is required for Gemini Vision)
        client_override = get_current_client_override() or extract_client_settings_from_request()
        api_key = (
            (client_override and client_override.get('api_key'))
            or current_app.config.get('GOOGLE_API_KEY')
        )
        if not api_key:
            from models import Settings
            settings = Settings.get_settings()
            if settings and getattr(settings, 'ai_provider_format', 'gemini') == 'gemini' and settings.api_key:
                api_key = settings.api_key

        if not api_key:
            return error_response(
                'CONFIGURATION_MISSING',
                'Vui lòng cấu hình Google API Key trong phần Cài đặt để sử dụng tính năng xuất PPTX có thể chỉnh sửa từ ảnh slide.',
                400,
            )

        # Create task record and stamp cache key before commit so concurrent requests deduplicate
        task_kwargs = {
            'project_id': project_id,
            'task_type': 'EXPORT_EDITABLE_PPTX',
            'status': 'PENDING',
        }
        if client_task_id:
            task_kwargs['id'] = client_task_id
        task = Task(**task_kwargs)
        task.set_progress({
            'total': 100,
            'completed': 0,
            'failed': 0,
            'current_step': 'Đang xếp hàng...',
            'percent': 0,
            'filename': filename,
            'export_cache_key': cache_key,
        })
        db.session.add(task)
        db.session.commit()
        
        logger.info(f"Created export task {task.id} for project {project_id} (recursive analysis: depth={max_depth}, workers={max_workers})")
        
        try:
            # Get services
            from services.file_service import FileService
            from services.task_manager import task_manager, export_editable_pptx_with_recursive_analysis_task

            file_service = FileService(current_app.config['UPLOAD_FOLDER'])

            # Get Flask app instance for background task
            app = current_app._get_current_object()

            logger.info(
                f"Export settings: extractor={export_extractor_method}, "
                f"inpaint={export_inpaint_method}, "
                f"icon_subject_extraction={enable_icon_subject_extraction}"
            )

            # Submit background task
            task_manager.submit_task(
                task.id,
                export_editable_pptx_with_recursive_analysis_task,
                project_id=project_id,
                filename=filename,
                file_service=file_service,
                page_ids=selected_page_ids if selected_page_ids else None,
                max_depth=max_depth,
                max_workers=max_workers,
                export_extractor_method=export_extractor_method,
                export_inpaint_method=export_inpaint_method,
                enable_icon_subject_extraction=enable_icon_subject_extraction,
                cache_key=cache_key,
                app=app
            )
        except Exception as submission_error:
            logger.exception("Failed to submit editable export task %s", task.id)
            failure_message = "Tác vụ xuất tệp có thể chỉnh sửa không thể đưa vào hàng đợi nền"
            task.status = 'FAILED'
            task.error_message = failure_message
            task.completed_at = datetime.utcnow()
            task.set_progress({
                'total': 100,
                'completed': 0,
                'failed': 1,
                'current_step': 'Gửi tác vụ thất bại',
                'percent': 0,
                'backend_status': 'FAILED',
                'error_code': 'EXPORT_TASK_SUBMISSION_FAILED',
                'error_type': 'internal',
                'error_stage': 'queue_submission',
                'error_details': {
                    'stage': 'queue_submission',
                    'retryable': True,
                    'technical_message': ExportService._safe_technical_message(submission_error),
                },
                'help_text': 'Hàng đợi tác vụ nền tạm thời không khả dụng, Vui lòng xuất lại sau. ',
            })
            db.session.commit()
            return error_response('EXPORT_TASK_SUBMISSION_FAILED', failure_message, 503)
        
        logger.info(f"Submitted recursive export task {task.id} to task manager")
        
        return success_response(
            data={
                "task_id": task.id,
                "filename": filename,
                "method": "recursive_analysis",
                "max_depth": max_depth,
                "max_workers": max_workers,
                "cached": False,
                "reused": False,
            },
            message="Export task created (using recursive analysis)"
        )
    
    except Exception as e:
        logger.exception("Error creating export task")
        return error_response('SERVER_ERROR', str(e), 500)


@export_bp.route('/<project_id>/export/video', methods=['POST'])
def export_video(project_id):
    """
    POST /api/projects/{project_id}/export/video -  () 

     + TTS  MP4 ,  Ken Burns . 

    Request body (JSON):
        {
            "filename": "optional_custom_name.mp4",
            "page_ids": ["id1", "id2"], // tùy chọn
            "voice": "zh-CN-XiaoxiaoNeural", // tùy chọn TTS giọng đọc
            "rate": "+0%", // Tốc độ đọc tùy chọn
            "generate_narration": true, // Có tự động tạo lời thuyết minh còn thiếu hay không (mặc định true) 
            "language": "zh" // Ngôn ngữ đầu ra tùy chọn
        }

    Returns:
        JSON with task_id for polling via /api/projects/{project_id}/tasks/{task_id}
    """
    try:
        project = Project.query.get(project_id)

        if not project:
            return not_found('Project')

        data = request.get_json() or {}
        requested_filename = data.get('filename')

        voice = data.get('voice', current_app.config.get('TTS_DEFAULT_VOICE_ZH', 'zh-CN-XiaoxiaoNeural'))
        rate = data.get('rate', current_app.config.get('TTS_DEFAULT_RATE', '+0%'))
        try:
            speed = float(data.get('speed', 1.0))
        except (TypeError, ValueError):
            speed = 1.0
        speed = max(0.7, min(speed, 1.2))
        generate_narration = data.get('generate_narration', True)
        enable_ken_burns = data.get('enable_ken_burns', False)
        include_no_image_pages = data.get('include_no_image_pages', False)
        language = data.get('language', current_app.config.get('OUTPUT_LANGUAGE', 'zh'))
        presentation_topic = data.get('presentation_topic') or project.idea_prompt or ''
        narration_config = normalize_narration_generation_config(
            data.get('narration_config'),
            fallback_topic=presentation_topic,
        )

        # Backend logic
        selected_page_ids = parse_page_ids_from_body(data)

        pages = get_filtered_pages(project_id, selected_page_ids if selected_page_ids else None)

        if not pages:
            return bad_request("No pages found for project")

        filename = build_export_filename(
            project,
            '.mp4',
            requested_filename=requested_filename,
            suffix='-video',
            pages=pages,
        )

        has_images = any(page.generated_image_path for page in pages)
        if not has_images and not include_no_image_pages:
            return bad_request("No generated images found for project. Enable 'include pages without images' to export all pages.")

        # Backend logic
        if 'voice' not in data:
            from services.tts_video_service import get_default_voice
            voice = get_default_voice(language, dict(current_app.config))

        # Backend logic
        task = Task(
            project_id=project_id,
            task_type='EXPORT_VIDEO',
            status='PENDING',
        )
        db.session.add(task)
        db.session.commit()

        logger.info(f"Created video export task {task.id} for project {project_id}")

        # Backend logic
        from services.file_service import FileService
        from services.task_manager import task_manager, export_video_task

        file_service = FileService(current_app.config['UPLOAD_FOLDER'])
        app = current_app._get_current_object()

        task_manager.submit_task(
            task.id,
            export_video_task,
            project_id=project_id,
            filename=filename,
            file_service=file_service,
            voice=voice,
            rate=rate,
            speed=speed,
            generate_narration=generate_narration,
            enable_ken_burns=enable_ken_burns,
            include_no_image_pages=include_no_image_pages,
            page_ids=selected_page_ids if selected_page_ids else None,
            language=language,
            narration_config=narration_config,
            app=app,
        )

        return success_response(
            data={
                "task_id": task.id,
                "filename": filename,
                "voice": voice,
                "generate_narration": generate_narration,
                "enable_ken_burns": enable_ken_burns,
                "include_no_image_pages": include_no_image_pages,
                "narration_config": narration_config,
            },
            message="Video export task created"
        )

    except Exception as e:
        logger.exception("Error creating video export task")
        return error_response('SERVER_ERROR', str(e), 500)