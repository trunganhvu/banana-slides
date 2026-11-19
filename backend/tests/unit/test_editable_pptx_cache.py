"""Unit tests for content-fingerprinted editable PPTX export cache and deduplication."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from controllers.export_controller import compute_editable_export_cache_key
from models import Page, Project, Task, db
from services.file_service import FileService
from services.task_manager import export_editable_pptx_with_recursive_analysis_task


def _create_project_pages(app, upload_folder: str, num_pages: int = 2, with_html: bool = False):
    with app.app_context():
        project = Project(
            project_title='Cache Test Deck 2026',
            creation_type='idea',
            image_aspect_ratio='16:9',
            export_extractor_method='gemini',
            export_inpaint_method='opencv',
            enable_icon_subject_extraction=True,
            export_allow_partial=False,
            status='COMPLETED',
        )
        db.session.add(project)
        db.session.flush()

        pages_dir = os.path.join(upload_folder, project.id, 'pages')
        os.makedirs(pages_dir, exist_ok=True)
        page_ids = []
        for idx in range(num_pages):
            page = Page(
                project_id=project.id,
                order_index=idx,
                status='COMPLETED',
            )
            page.set_outline_content({'title': f'Slide {idx + 1}', 'points': ['Item']})
            db.session.add(page)
            db.session.flush()

            rel_img = f'{project.id}/pages/{page.id}_v1.png'
            abs_img = os.path.join(upload_folder, rel_img)
            Image.new('RGB', (320, 180), color=(20 + idx * 30, 60, 120)).save(abs_img, 'PNG')
            page.generated_image_path = rel_img

            if with_html:
                html_path = os.path.join(pages_dir, f'{page.id}.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(f'<section class="slide"><h1>Slide {idx + 1}</h1></section>')

            page_ids.append(page.id)

        db.session.commit()
        return project.id, page_ids


class TestEditablePptxExportCache:
    def test_repeat_export_hits_completed_cache_without_ai_or_api_key(self, client, app):
        upload_folder = app.config['UPLOAD_FOLDER']
        project_id, _page_ids = _create_project_pages(app, upload_folder, num_pages=2)

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_submit,
        ):
            first_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={})

        assert first_resp.status_code == 200, first_resp.get_json()
        first_data = first_resp.get_json()['data']
        assert first_data['cached'] is False
        assert first_data['reused'] is False
        mock_submit.assert_called_once()
        task_id = first_data['task_id']
        filename = first_data['filename']

        # Simulate task completion and file written on disk
        exports_dir = Path(upload_folder) / project_id / 'exports'
        exports_dir.mkdir(parents=True, exist_ok=True)
        (exports_dir / filename).write_bytes(b'PK-fake-pptx-content')

        with app.app_context():
            task = db.session.get(Task, task_id)
            progress = task.get_progress()
            task.status = 'COMPLETED'
            progress['download_url'] = f'/files/{project_id}/exports/{filename}'
            progress['filename'] = filename
            task.set_progress(progress)
            db.session.commit()

        # Second export without changes hits cache even when GOOGLE_API_KEY is unset and calls submit_task 0 times
        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': ''}),
            patch('services.task_manager.task_manager.submit_task') as mock_submit_2,
        ):
            second_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={})

        assert second_resp.status_code == 200, second_resp.get_json()
        second_data = second_resp.get_json()['data']
        assert second_data['cached'] is True
        assert second_data['reused'] is True
        assert second_data['task_id'] == task_id
        assert second_data['filename'] == filename
        assert second_data['download_url'] == f'/files/{project_id}/exports/{filename}'
        mock_submit_2.assert_not_called()

    def test_in_flight_deduplication_and_stale_task_fallback(self, client, app):
        upload_folder = app.config['UPLOAD_FOLDER']
        project_id, _ = _create_project_pages(app, upload_folder, num_pages=1)

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_submit,
        ):
            first_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={})
        first_task_id = first_resp.get_json()['data']['task_id']
        assert mock_submit.call_count == 1

        # Simulate another live request arriving while task is RUNNING
        with app.app_context():
            t = db.session.get(Task, first_task_id)
            t.status = 'RUNNING'
            db.session.commit()

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_watchdog.reconcile_task_for_response', return_value=False),
            patch('services.task_manager.task_manager.submit_task') as mock_submit_dup,
        ):
            dup_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={})

        assert dup_resp.status_code == 200
        dup_data = dup_resp.get_json()['data']
        assert dup_data['cached'] is False
        assert dup_data['reused'] is True
        assert dup_data['task_id'] == first_task_id
        mock_submit_dup.assert_not_called()

        # If watchdog reconciles task to FAILED (orphaned), next request submits a fresh task
        def _mark_failed(task_obj):
            task_obj.status = 'FAILED'
            db.session.commit()
            return True

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_watchdog.reconcile_task_for_response', side_effect=_mark_failed),
            patch('services.task_manager.task_manager.submit_task') as mock_submit_new,
        ):
            fresh_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={})

        assert fresh_resp.status_code == 200
        fresh_data = fresh_resp.get_json()['data']
        assert fresh_data['reused'] is False
        assert fresh_data['task_id'] != first_task_id
        mock_submit_new.assert_called_once()

    def test_invalidation_on_slide_edit_settings_selection_delete_and_force(self, client, app):
        upload_folder = app.config['UPLOAD_FOLDER']
        project_id, page_ids = _create_project_pages(app, upload_folder, num_pages=2)

        def _seed_completed():
            with (
                patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
                patch('services.task_manager.task_manager.submit_task'),
            ):
                r = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={'max_depth': 1})
            d = r.get_json()['data']
            exports_dir = Path(upload_folder) / project_id / 'exports'
            exports_dir.mkdir(parents=True, exist_ok=True)
            (exports_dir / d['filename']).write_bytes(b'PK-cached')
            with app.app_context():
                t = db.session.get(Task, d['task_id'])
                p = t.get_progress()
                t.status = 'COMPLETED'
                p['download_url'] = f"/files/{project_id}/exports/{d['filename']}"
                p['filename'] = d['filename']
                t.set_progress(p)
                db.session.commit()
            return d['filename']

        cached_filename = _seed_completed()

        # 1. Subset page_ids misses cache
        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_subset,
        ):
            r_sub = client.post(
                f'/api/projects/{project_id}/export/editable-pptx',
                json={'page_ids': [page_ids[0]]},
            )
        assert r_sub.get_json()['data']['cached'] is False
        mock_subset.assert_called_once()

        # 2. Changing export settings misses cache
        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_depth,
        ):
            r_depth = client.post(
                f'/api/projects/{project_id}/export/editable-pptx',
                json={'max_depth': 2},
            )
        assert r_depth.get_json()['data']['cached'] is False
        mock_depth.assert_called_once()

        # 3. Deleting cached .pptx file misses cache
        del_resp = client.delete(f'/api/projects/{project_id}/exports/{cached_filename}')
        assert del_resp.status_code == 200
        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_after_del,
        ):
            r_after_del = client.post(
                f'/api/projects/{project_id}/export/editable-pptx',
                json={'max_depth': 1},
            )
        assert r_after_del.get_json()['data']['cached'] is False
        mock_after_del.assert_called_once()

        # Re-seed completed export, then modify slide PNG image on disk -> must miss cache
        _seed_completed()
        with app.app_context():
            p0 = db.session.get(Page, page_ids[0])
            abs_img = os.path.join(upload_folder, p0.generated_image_path)
            Image.new('RGB', (320, 180), color=(255, 0, 0)).save(abs_img, 'PNG')

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_after_edit,
        ):
            r_edit = client.post(
                f'/api/projects/{project_id}/export/editable-pptx',
                json={'max_depth': 1},
            )
        assert r_edit.get_json()['data']['cached'] is False
        mock_after_edit.assert_called_once()

        # 4. Re-seed completed export, then explicit force=True bypasses completed cache
        _seed_completed()
        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_force,
        ):
            r_force = client.post(
                f'/api/projects/{project_id}/export/editable-pptx',
                json={'max_depth': 1, 'force': True},
            )
        assert r_force.status_code == 200
        assert r_force.get_json()['data']['cached'] is False
        assert r_force.get_json()['data']['reused'] is False
        mock_force.assert_called_once()

    def test_worker_persists_cache_key_and_second_export_reuses_it(self, client, app):
        upload_folder = app.config['UPLOAD_FOLDER']
        project_id, _ = _create_project_pages(app, upload_folder, num_pages=1, with_html=True)

        with app.app_context():
            project = db.session.get(Project, project_id)
            pages = list(project.pages)
            initial_key = compute_editable_export_cache_key(
                project,
                pages,
                upload_folder,
                max_depth=1,
                export_extractor_method='gemini',
                export_inpaint_method='opencv',
                enable_icon_subject_extraction=True,
                export_allow_partial=False,
            )

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_submit,
        ):
            first_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={'max_depth': 1})
        assert first_resp.status_code == 200
        first_data = first_resp.get_json()['data']
        task_id = first_data['task_id']
        filename = first_data['filename']
        assert mock_submit.call_args.kwargs['cache_key'] == initial_key

        def _fake_create_editable(**kwargs):
            Path(kwargs['output_file']).parent.mkdir(parents=True, exist_ok=True)
            Path(kwargs['output_file']).write_bytes(b'PK-worker-built-pptx')
            return kwargs['output_file'], MagicMock(has_warnings=lambda: False, to_dict=lambda: {})

        file_service = FileService(upload_folder)
        with (
            patch('services.image_editability.TextAttributeExtractorFactory.create_caption_model_extractor', return_value=MagicMock()),
            patch('services.export_service.ExportService.create_editable_pptx_with_recursive_analysis', side_effect=_fake_create_editable),
        ):
            export_editable_pptx_with_recursive_analysis_task(
                task_id=task_id,
                project_id=project_id,
                filename=filename,
                file_service=file_service,
                max_depth=1,
                max_workers=2,
                export_extractor_method='gemini',
                export_inpaint_method='opencv',
                enable_icon_subject_extraction=True,
                cache_key=initial_key,
                app=app,
            )

        with app.app_context():
            project = db.session.get(Project, project_id)
            expected_final_key = compute_editable_export_cache_key(
                project,
                list(project.pages),
                upload_folder,
                max_depth=1,
                export_extractor_method='gemini',
                export_inpaint_method='opencv',
                enable_icon_subject_extraction=True,
                export_allow_partial=False,
            )
            done_task = db.session.get(Task, task_id)
            assert done_task.status == 'COMPLETED'
            assert done_task.get_progress().get('export_cache_key') == expected_final_key
            assert done_task.get_progress().get('filename') == filename

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': ''}),
            patch('services.task_manager.task_manager.submit_task') as mock_submit_repeat,
        ):
            repeat_resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={'max_depth': 1})

        assert repeat_resp.status_code == 200
        repeat_data = repeat_resp.get_json()['data']
        assert repeat_data['cached'] is True
        assert repeat_data['reused'] is True
        assert repeat_data['task_id'] == task_id
        assert repeat_data['filename'] == filename
        mock_submit_repeat.assert_not_called()
