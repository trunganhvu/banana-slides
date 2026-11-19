"""Unit tests for concise, project-derived export filenames."""
import io
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image
from werkzeug.utils import secure_filename

from models import Page, Project, db
from utils.filename_utils import (
    build_export_filename,
    get_project_display_name,
    slugify_filename,
)


class TestSlugifyAndFilenameBuilder:
    def test_slugify_vietnamese_diacritics_and_word_boundary_truncation(self):
        title = 'Trang 1: "Báo cáo Phân tích Chiến lược ESG: Đại học & Định hướng 2030"'
        slug = slugify_filename(title, max_length=48)
        assert slug == 'bao-cao-phan-tich-chien-luoc-esg-dai-hoc-dinh'
        assert len(slug) <= 48
        assert not slug.endswith('-')
        assert secure_filename(f'{slug}.pptx') == f'{slug}.pptx'

    def test_slugify_strips_slide_prefix_and_handles_empty(self):
        assert slugify_filename('Slide 3: Tổng quan Đổi mới') == 'tong-quan-doi-moi'
        assert slugify_filename('Page 12 - Quarterly Revenue') == 'quarterly-revenue'
        assert slugify_filename('   !!! ---   ', default='banana-slides-1234abcd') == 'banana-slides-1234abcd'

    def test_display_name_priority_and_generic_page_skip(self):
        # 1. Explicit project_title wins
        proj = SimpleNamespace(
            id='12345678-aaaa-bbbb-cccc-1234567890ab',
            project_title='The Coca-Cola ESG Monograph',
            idea_prompt='Some idea',
            outline_text=None,
            description_text=None,
            pages=[SimpleNamespace(order_index=0, outline_content={'title': 'First Slide'})],
        )
        assert get_project_display_name(proj) == 'The Coca-Cola ESG Monograph'

        # 2. Non-generic first page title used when project_title missing
        proj_no_title = SimpleNamespace(
            id='12345678-aaaa-bbbb-cccc-1234567890ab',
            project_title=None,
            idea_prompt='Fallback idea prompt',
            outline_text=None,
            description_text=None,
            pages=[
                SimpleNamespace(order_index=1, outline_content={'title': 'Second'}),
                SimpleNamespace(order_index=0, outline_content={'title': 'AI Architecture Overview'}),
            ],
        )
        assert get_project_display_name(proj_no_title) == 'AI Architecture Overview'

        # 3. Generic first-page title ("Page 1") skipped in favor of concise idea_prompt clause
        proj_generic_page = SimpleNamespace(
            id='12345678-aaaa-bbbb-cccc-1234567890ab',
            project_title='',
            idea_prompt='Chiến lược tăng trưởng sản phẩm AI cho doanh nghiệp vừa và nhỏ. Bao gồm kế hoạch 6 tháng.',
            outline_text=None,
            description_text=None,
            pages=[SimpleNamespace(order_index=0, outline_content={'title': 'Page 1'})],
        )
        assert get_project_display_name(proj_generic_page) == 'Chiến lược tăng trưởng sản phẩm AI cho doanh nghiệp vừa và nhỏ'

    def test_build_export_filename_with_suffixes_and_custom_override(self):
        proj = SimpleNamespace(
            id='c8ac31c3-6ec3-455d-8cef-c3769af1b392',
            project_title='Báo cáo Chiến lược ESG: Coca-Cola',
            idea_prompt=None,
            outline_text=None,
            description_text=None,
            pages=[],
        )

        pptx_name = build_export_filename(proj, '.pptx')
        editable_name = build_export_filename(proj, '.pptx', suffix='-editable')
        zip_name = build_export_filename(proj, '.zip', suffix='-slides')
        video_name = build_export_filename(proj, '.mp4', suffix='-video')
        custom_name = build_export_filename(proj, '.pptx', requested_filename='Bản nháp Quý 4.pptx')

        assert pptx_name == 'bao-cao-chien-luoc-esg-coca-cola.pptx'
        assert editable_name == 'bao-cao-chien-luoc-esg-coca-cola-editable.pptx'
        assert zip_name == 'bao-cao-chien-luoc-esg-coca-cola-slides.zip'
        assert video_name == 'bao-cao-chien-luoc-esg-coca-cola-video.mp4'
        assert custom_name == 'ban-nhap-quy-4.pptx'

        for fname in (pptx_name, editable_name, zip_name, video_name, custom_name):
            assert secure_filename(fname) == fname


class TestExportControllerFilenames:
    def _create_project_with_pages(self, app, upload_folder, num_pages=2):
        with app.app_context():
            project = Project(
                project_title='Kế hoạch Ra mắt Sản phẩm Mới 2026',
                creation_type='idea',
                image_aspect_ratio='16:9',
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
                page.set_outline_content({'title': f'Slide Title {idx + 1}', 'points': ['A']})
                db.session.add(page)
                db.session.flush()

                rel_img = f'{project.id}/pages/{page.id}_v1.png'
                Image.new('RGB', (320, 180), color=(240, 240, 240)).save(
                    os.path.join(upload_folder, rel_img), 'PNG'
                )
                page.generated_image_path = rel_img
                page_ids.append(page.id)

            db.session.commit()
            return project.id, page_ids

    def test_sync_exports_and_delete_use_friendly_filename(self, client, app):
        upload_folder = app.config['UPLOAD_FOLDER']
        project_id, page_ids = self._create_project_with_pages(app, upload_folder, num_pages=2)
        expected_base = 'ke-hoach-ra-mat-san-pham-moi-2026'

        # PPTX export + download + delete round-trip
        pptx_resp = client.get(f'/api/projects/{project_id}/export/pptx')
        assert pptx_resp.status_code == 200, pptx_resp.get_json()
        pptx_data = pptx_resp.get_json()['data']
        assert pptx_data['filename'] == f'{expected_base}.pptx'
        assert pptx_data['download_url'] == f'/files/{project_id}/exports/{expected_base}.pptx'

        with client.get(pptx_data['download_url']) as dl_resp:
            assert dl_resp.status_code == 200
            assert 'attachment' in dl_resp.headers.get('Content-Disposition', '').lower()

        del_resp = client.delete(f'/api/projects/{project_id}/exports/{expected_base}.pptx')
        assert del_resp.status_code == 200, del_resp.get_json()

        # PDF export
        pdf_resp = client.get(f'/api/projects/{project_id}/export/pdf')
        assert pdf_resp.status_code == 200
        assert pdf_resp.get_json()['data']['filename'] == f'{expected_base}.pdf'

        # Images ZIP (multi-page) and single slide PNG
        zip_resp = client.get(f'/api/projects/{project_id}/export/images')
        assert zip_resp.status_code == 200
        assert zip_resp.get_json()['data']['filename'] == f'{expected_base}-slides.zip'

        single_resp = client.get(f'/api/projects/{project_id}/export/images?page_ids={page_ids[0]}')
        assert single_resp.status_code == 200
        assert single_resp.get_json()['data']['filename'] == f'{expected_base}-slide-1.png'

    def test_editable_pptx_export_uses_concise_editable_filename(self, client, app):
        upload_folder = app.config['UPLOAD_FOLDER']
        project_id, _page_ids = self._create_project_with_pages(app, upload_folder, num_pages=1)

        with (
            patch.dict(app.config, {'GOOGLE_API_KEY': 'test-key'}),
            patch('services.task_manager.task_manager.submit_task') as mock_submit,
        ):
            resp = client.post(f'/api/projects/{project_id}/export/editable-pptx', json={})

        assert resp.status_code == 200, resp.get_json()
        data = resp.get_json()['data']
        assert data['filename'] == 'ke-hoach-ra-mat-san-pham-moi-2026-editable.pptx'
        mock_submit.assert_called_once()
        assert mock_submit.call_args.kwargs['filename'] == 'ke-hoach-ra-mat-san-pham-moi-2026-editable.pptx'

    def test_html_renovation_upload_sets_project_title_for_exports(self, client, app):
        html_bytes = (
            '<!DOCTYPE html><html><head><title>Báo cáo Chiến lược Coca-Cola</title></head>'
            '<body><section class="slide"><h1>Slide 1</h1></section></body></html>'
        ).encode('utf-8')
        with (
            patch('services.html_slide_service._render_with_headless_browser', return_value=None),
            patch('controllers.project_controller.task_manager.submit_task'),
        ):
            up_resp = client.post(
                '/api/projects/renovation',
                data={'file': (io.BytesIO(html_bytes), 'deck.html'), 'keep_layout': 'true'},
                content_type='multipart/form-data',
            )

        assert up_resp.status_code == 202
        project_id = up_resp.get_json()['data']['project_id']
        with app.app_context():
            project = db.session.get(Project, project_id)
            assert project.project_title == 'Báo cáo Chiến lược Coca-Cola'

        pptx_resp = client.get(f'/api/projects/{project_id}/export/pptx')
        assert pptx_resp.status_code == 200
        assert pptx_resp.get_json()['data']['filename'] == 'bao-cao-chien-luoc-coca-cola.pptx'
