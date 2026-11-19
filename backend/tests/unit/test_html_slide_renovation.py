"""Unit tests for HTML slide renovation workflow."""
import io
import os
from unittest.mock import MagicMock, patch

from PIL import Image
import pytest

from models import Page, Project, Task, db
from services.ai_service import AIService
from services.file_service import FileService
from services.html_slide_service import (
    _render_with_headless_browser,
    build_fallback_slide_content,
    detect_html_aspect_ratio_and_size,
    ensure_html_pages_rendered,
    extract_slide_from_standalone_html,
    is_chromium_rendered_png,
    render_html_slide_to_image,
    save_rendered_html_slide_png,
    split_html_to_slides,
)


SAMPLE_CARD_DECK_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <title>Quarterly AI Review</title>
  <style>
    .slide { width: 1280px; height: 720px; background: #0f172a; color: #f8fafc; }
    .slide.hidden-by-deck { display: none; }
  </style>
</head>
<body>
  <nav class="controls"><button data-slide-to="0">1</button><button data-slide-to="1">2</button></nav>
  <div class="deck">
    <section class="slide">
      <span class="eyebrow">Phần 1</span>
      <h1>Báo cáo AI Quý 4</h1>
      <ul>
        <li>Tăng trưởng người dùng đạt 42%</li>
        <li>Chi phí suy luận giảm 30%</li>
      </ul>
      <aside class="speaker-notes">Nhấn mạnh kết quả tăng trưởng người dùng.</aside>
    </section>
    <section class="slide hidden-by-deck" style="display: none;">
      <span class="eyebrow">Phần 2</span>
      <h2>Kiến trúc hệ thống mới</h2>
      <p>Chuyển đổi từ pipeline tuần tự sang xử lý song song.</p>
      <table>
        <tr><th>Chỉ số</th><th>Q3</th><th>Q4</th></tr>
        <tr><td>Độ trễ</td><td>420ms</td><td>180ms</td></tr>
      </table>
    </section>
  </div>
</body>
</html>
"""

SAMPLE_REVEAL_HTML = """<!DOCTYPE html>
<html>
<head><style>.reveal .slides section { aspect-ratio: 4 / 3; }</style></head>
<body>
  <div class="reveal">
    <div class="slides">
      <section><h1>Intro Slide</h1><p>Welcome</p></section>
      <section>
        <section><h2>Vertical A</h2></section>
        <section><h2>Vertical B</h2></section>
      </section>
    </div>
  </div>
</body>
</html>
"""

SAMPLE_ID_DECK_HTML = """<!DOCTYPE html>
<html>
<body>
  <div id="slide-1"><h1>Alpha</h1></div>
  <div id="slide-2"><h1>Beta</h1></div>
  <div id="slide-3"><h1>Gamma</h1></div>
</body>
</html>
"""

SAMPLE_SINGLE_SLIDE_HTML = """<!DOCTYPE html>
<html>
<head><style>body { width: 1080px; height: 1080px; }</style></head>
<body>
  <main class="hero-card">
    <h1>Single Poster Slide</h1>
    <p>Key highlight content for a 1:1 card</p>
  </main>
</body>
</html>
"""


class TestHtmlSlideSplittingAndDetection:
    def test_split_card_deck_preserves_styles_and_removes_siblings(self):
        slides = split_html_to_slides(SAMPLE_CARD_DECK_HTML)
        assert len(slides) == 2

        first, second = slides[0], slides[1]
        assert first['title'] == 'Báo cáo AI Quý 4'
        assert first['part'] == 'Phần 1'
        assert 'Tăng trưởng người dùng đạt 42%' in first['points']
        assert first['speaker_notes'] == 'Nhấn mạnh kết quả tăng trưởng người dùng.'
        assert 'Báo cáo AI Quý 4' in first['standalone_html']
        assert 'Kiến trúc hệ thống mới' not in first['standalone_html']
        assert 'data-banana-slide-root="true"' in first['standalone_html']
        assert 'banana-slide-style' in first['standalone_html']
        assert 'banana-slide-init' in first['standalone_html']
        # Head stylesheet retained, global nav pruned
        assert '.slide { width: 1280px;' in first['standalone_html']
        assert 'data-slide-to' not in first['standalone_html']

        # Second slide should have inline style="display: none;" stripped and no first slide content
        assert second['title'] == 'Kiến trúc hệ thống mới'
        assert 'Kiến trúc hệ thống mới' in second['standalone_html']
        assert 'Báo cáo AI Quý 4' not in second['standalone_html']
        assert 'style="display: none;"' not in second['standalone_html'].lower()
        assert '| Chỉ số | Q3 | Q4 |' in second['markdown_text']

        re_extracted = extract_slide_from_standalone_html(second['standalone_html'], index=1)
        assert re_extracted['title'] == 'Kiến trúc hệ thống mới'

    def test_split_reveal_nested_sections(self):
        slides = split_html_to_slides(SAMPLE_REVEAL_HTML)
        assert len(slides) == 3
        assert [s['title'] for s in slides] == ['Intro Slide', 'Vertical A', 'Vertical B']

    def test_split_id_deck(self):
        slides = split_html_to_slides(SAMPLE_ID_DECK_HTML)
        assert len(slides) == 3
        assert [s['title'] for s in slides] == ['Alpha', 'Beta', 'Gamma']

    def test_split_single_slide_fallback(self):
        slides = split_html_to_slides(SAMPLE_SINGLE_SLIDE_HTML)
        assert len(slides) == 1
        assert slides[0]['title'] == 'Single Poster Slide'
        assert 'data-banana-slide-root="true"' in slides[0]['standalone_html']

    def test_split_empty_html_raises(self):
        with pytest.raises(ValueError):
            split_html_to_slides('   \n  ')

    @pytest.mark.parametrize(
        'html_snippet,expected_ratio,expected_w,expected_h',
        [
            ('<style>.s { aspect-ratio: 16 / 9; }</style>', '16:9', 1280, 720),
            ('<style>.s { aspect-ratio: 4 / 3; }</style>', '4:3', 1024, 768),
            ('<style>.s { width: 1080px; height: 1080px; }</style>', '1:1', 1080, 1080),
            ('<style>.s { width: 720px; height: 1280px; }</style>', '9:16', 720, 1280),
        ],
    )
    def test_detect_aspect_ratio_and_size(self, html_snippet, expected_ratio, expected_w, expected_h):
        ratio, w, h = detect_html_aspect_ratio_and_size(html_snippet)
        assert ratio == expected_ratio
        assert (w, h) == (expected_w, expected_h)


class TestHtmlSlideExtractionAndRender:
    def test_build_fallback_slide_content(self):
        slides = split_html_to_slides(SAMPLE_CARD_DECK_HTML)
        fallback = build_fallback_slide_content(slides[0], index=0, language='vi')
        assert fallback['title'] == 'Báo cáo AI Quý 4'
        assert fallback['part'] == 'Phần 1'
        assert len(fallback['points']) >= 2
        assert 'Báo cáo AI Quý 4' in fallback['description']
        assert fallback['extra_fields']['Ghi chú thuyết trình'] == 'Nhấn mạnh kết quả tăng trưởng người dùng.'
        assert 'Hình ảnh & Tư liệu' in fallback['extra_fields']
        assert 'Bố cục & Trọng tâm' in fallback['extra_fields']

    def test_ai_service_extract_html_slide_content(self):
        slides = split_html_to_slides(SAMPLE_CARD_DECK_HTML)
        service = AIService(text_provider=MagicMock())
        service.generate_json = MagicMock(return_value={
            'title': 'Báo cáo tăng trưởng AI Q4',
            'part': 'Tổng quan',
            'points': ['Người dùng tăng 42%', 'Chi phí giảm 30%'],
            'description': '## Báo cáo tăng trưởng AI Q4\n- Người dùng tăng 42%\n- Chi phí giảm 30%',
            'extra_fields': {
                'Hình ảnh & Tư liệu': 'Biểu đồ KPI nền tối với 2 thẻ số liệu nổi bật.',
                'Bố cục & Trọng tâm': 'Bố cục 1 cột tối giản, nhấn mạnh hai chỉ số Q4.',
            },
        })

        result = service.extract_html_slide_content(
            slide_data=slides[0],
            language='vi',
            extra_fields=['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình'],
            keep_layout=True,
        )

        service.generate_json.assert_called_once()
        prompt_arg = service.generate_json.call_args[0][0]
        assert 'Báo cáo AI Quý 4' in prompt_arg
        assert result['title'] == 'Báo cáo tăng trưởng AI Q4'
        assert result['part'] == 'Tổng quan'
        assert result['points'] == ['Người dùng tăng 42%', 'Chi phí giảm 30%']
        assert 'extra_fields' in result
        # Missing Ghi chú thuyết trình in AI output should be backfilled from HTML notes fallback
        assert result['extra_fields']['Ghi chú thuyết trình'] == 'Nhấn mạnh kết quả tăng trưởng người dùng.'

    def test_render_html_slide_to_image_pillow_fallback(self):
        slides = split_html_to_slides(SAMPLE_CARD_DECK_HTML)
        img = render_html_slide_to_image(
            slides[0]['standalone_html'],
            slides[0],
            width=1280,
            height=720,
            use_browser=False,
        )
        assert img.size == (1280, 720)


class TestHtmlRenovationEndpointsAndTasks:
    def test_upload_html_creates_html_renovation_project_and_serves_slide(self, client, app, temp_upload_dir):
        data = {
            'file': (io.BytesIO(SAMPLE_CARD_DECK_HTML.encode('utf-8')), 'quarterly-deck.html'),
            'keep_layout': 'true',
        }

        with (
            patch('services.html_slide_service._render_with_headless_browser', return_value=None),
            patch('controllers.project_controller.task_manager.submit_task') as mock_submit,
        ):
            resp = client.post(
                '/api/projects/renovation',
                data=data,
                content_type='multipart/form-data',
            )

        assert resp.status_code == 202, resp.get_json()
        payload = resp.get_json()['data']
        project_id = payload['project_id']
        assert payload['page_count'] == 2
        assert payload['task_id']
        mock_submit.assert_called_once()

        with app.app_context():
            project = Project.query.get(project_id)
            assert project is not None
            assert project.creation_type == 'html_renovation'
            assert project.status == 'PROCESSING'
            upload_folder = app.config['UPLOAD_FOLDER']
            pages = Page.query.filter_by(project_id=project_id).order_by(Page.order_index).all()
            assert len(pages) == 2

            for idx, page in enumerate(pages):
                page_dict = page.to_dict()
                assert page_dict['html_slide_url'] == f'/files/{project_id}/pages/{page.id}.html'
                assert page.generated_image_path is not None
                html_path = os.path.join(upload_folder, project_id, 'pages', f'{page.id}.html')
                split_path = os.path.join(upload_folder, project_id, 'split_pages', f'page_{idx + 1}.html')
                assert os.path.isfile(html_path)
                assert os.path.isfile(split_path)

            first_slide_url = pages[0].to_dict()['html_slide_url']

        # Verify standalone HTML slide is served inline via /files/
        file_resp = client.get(first_slide_url)
        assert file_resp.status_code == 200
        served_html = file_resp.data.decode('utf-8')
        assert 'Báo cáo AI Quý 4' in served_html
        assert 'Kiến trúc hệ thống mới' not in served_html

    def test_process_html_renovation_task_populates_ai_and_fallback_descriptions(self, app, db_session):
        from services.task_manager import _process_html_renovation_pages

        slides = split_html_to_slides(SAMPLE_CARD_DECK_HTML)
        upload_folder = app.config['UPLOAD_FOLDER']
        project = Project(
            project_title='HTML Deck Test',
            creation_type='html_renovation',
            status='OUTLINE_GENERATED',
        )
        db.session.add(project)
        db.session.flush()

        pages_dir = os.path.join(upload_folder, project.id, 'pages')
        os.makedirs(pages_dir, exist_ok=True)

        for idx, s in enumerate(slides):
            p = Page(
                project_id=project.id,
                order_index=idx,
                part=s['part'],
                status='DRAFT',
            )
            p.set_outline_content({'title': s['title'], 'points': s['points']})
            db.session.add(p)
            db.session.flush()
            with open(os.path.join(pages_dir, f'{p.id}.html'), 'w', encoding='utf-8') as f:
                f.write(s['standalone_html'])

        task = Task(
            project_id=project.id,
            task_type='PPT_RENOVATION',
            status='PROCESSING',
        )
        task.set_progress({'total': 2, 'completed': 0})
        db.session.add(task)
        db.session.commit()

        mock_ai = MagicMock()
        # First slide succeeds via AI; second raises error -> verifies fallback path works seamlessly
        mock_ai.extract_html_slide_content.side_effect = [
            {
                'title': 'AI Synthesized Q4 Title',
                'part': 'Executive Summary',
                'points': ['42% user growth', '30% lower inference cost'],
                'description': 'AI generated overview of Q4 metrics.',
                'extra_fields': {
                    'Hình ảnh & Tư liệu': 'Dark dashboard metric cards.',
                    'Bố cục & Trọng tâm': 'Hero headline and KPI list.',
                    'Ghi chú thuyết trình': 'Highlight strong Q4 adoption.',
                },
            },
            RuntimeError('Simulated LLM timeout'),
        ]

        with patch('services.html_slide_service._find_headless_browser', return_value=None):
            _process_html_renovation_pages(
                task_id=task.id,
                project_id=project.id,
                project=project,
                ai_service=mock_ai,
                file_service=FileService(upload_folder),
                keep_layout=True,
                max_workers=1,
                app=app,
                language='vi',
            )

        db.session.expire_all()
        updated_project = Project.query.get(project.id)
        updated_pages = Page.query.filter_by(project_id=project.id).order_by(Page.order_index).all()

        assert updated_project.status == 'DESCRIPTIONS_GENERATED'
        assert updated_pages[0].get_outline_content()['title'] == 'AI Synthesized Q4 Title'
        assert updated_pages[0].get_description_content()['text'] == 'AI generated overview of Q4 metrics.'
        assert updated_pages[0].get_description_content()['extra_fields']['Hình ảnh & Tư liệu'] == 'Dark dashboard metric cards.'
        assert updated_pages[0].status == 'DESCRIPTION_GENERATED'

        # Fallback page should also complete with extracted HTML content
        assert updated_pages[1].status == 'DESCRIPTION_GENERATED'
        assert updated_pages[1].get_outline_content()['title'] == 'Kiến trúc hệ thống mới'
        assert 'Chuyển đổi từ pipeline tuần tự' in updated_pages[1].get_description_content()['text']

    def test_regenerate_renovation_page_endpoint_for_html_renovation(self, client, app):
        slides = split_html_to_slides(SAMPLE_CARD_DECK_HTML)
        with app.app_context():
            upload_folder = app.config['UPLOAD_FOLDER']
            project = Project(
                project_title='HTML Regen Test',
                creation_type='html_renovation',
                status='DESCRIPTIONS_GENERATED',
            )
            db.session.add(project)
            db.session.flush()

            page = Page(
                project_id=project.id,
                order_index=0,
                status='COMPLETED',
            )
            page.set_outline_content({'title': 'Old title', 'points': []})
            page.set_description_content({'text': 'Old description', 'extra_fields': {}})
            db.session.add(page)
            db.session.flush()

            pages_dir = os.path.join(upload_folder, project.id, 'pages')
            os.makedirs(pages_dir, exist_ok=True)
            with open(os.path.join(pages_dir, f'{page.id}.html'), 'w', encoding='utf-8') as f:
                f.write(slides[0]['standalone_html'])
            db.session.commit()
            project_id, page_id = project.id, page.id

        mock_ai = MagicMock()
        mock_ai.extract_html_slide_content.return_value = {
            'title': 'Regenerated HTML Title',
            'part': 'Phần 1',
            'points': ['Point A', 'Point B'],
            'description': 'Fresh reverse description from standalone HTML.',
            'extra_fields': {
                'Hình ảnh & Tư liệu': 'Fresh visuals',
                'Bố cục & Trọng tâm': 'Fresh layout',
                'Ghi chú thuyết trình': 'Fresh notes',
            },
        }

        with patch('controllers.page_controller.get_ai_service', return_value=mock_ai):
            resp = client.post(
                f'/api/projects/{project_id}/pages/{page_id}/regenerate-renovation',
                json={'language': 'vi', 'keep_layout': True},
            )

        assert resp.status_code == 200, resp.get_json()
        page_data = resp.get_json()['data']
        assert page_data['outline_content']['title'] == 'Regenerated HTML Title'
        assert page_data['description_content']['text'] == 'Fresh reverse description from standalone HTML.'
        assert page_data['html_slide_url'] == f'/files/{project_id}/pages/{page_id}.html'


class TestHtmlSlidePngProvenanceAndUpgrade:
    def test_png_renderer_metadata_distinguishes_chromium_and_fallback(self, tmp_path):
        chromium_png = tmp_path / 'chromium_v1.png'
        fallback_png = tmp_path / 'fallback_v1.png'
        untagged_png = tmp_path / 'untagged_v1.png'

        img_chr = Image.new('RGB', (16, 16), color=(10, 20, 30))
        img_chr.info['banana_renderer'] = 'chromium'
        save_rendered_html_slide_png(img_chr, str(chromium_png))

        img_fb = Image.new('RGB', (16, 16), color=(40, 50, 60))
        img_fb.info['banana_renderer'] = 'pillow_fallback'
        save_rendered_html_slide_png(img_fb, str(fallback_png))

        Image.new('RGB', (16, 16), color=(70, 80, 90)).save(str(untagged_png), 'PNG')

        assert is_chromium_rendered_png(str(chromium_png)) is True
        assert is_chromium_rendered_png(str(fallback_png)) is False
        assert is_chromium_rendered_png(str(untagged_png)) is False
        assert is_chromium_rendered_png(str(tmp_path / 'missing.png')) is False

    def test_render_with_headless_browser_uses_isolated_profile_and_hd_scale(self, tmp_path):
        html_file = tmp_path / 'slide.html'
        html_file.write_text('<!DOCTYPE html><html><body><h1>Hi</h1></body></html>', encoding='utf-8')
        recorded_cmds = []

        def fake_run(cmd, **kwargs):
            recorded_cmds.append(cmd)
            shot_arg = [arg for arg in cmd if arg.startswith('--screenshot=')][0]
            out_path = shot_arg.split('=', 1)[1]
            Image.new('RGB', (1920, 1080), color=(250, 248, 245)).save(out_path, 'PNG')
            proc = MagicMock()
            proc.returncode = 0
            return proc

        with (
            patch('services.html_slide_service._find_headless_browser', return_value='/usr/bin/chromium'),
            patch('services.html_slide_service.subprocess.run', side_effect=fake_run),
        ):
            img = _render_with_headless_browser(str(html_file), width=1280, height=720)

        assert img is not None
        assert img.size == (1920, 1080)
        assert img.info.get('banana_renderer') == 'chromium'
        assert len(recorded_cmds) == 1
        cmd = recorded_cmds[0]
        assert '--virtual-time-budget=5000' in cmd
        assert '--force-device-scale-factor=1.5' in cmd
        assert '--window-size=1280,720' in cmd
        assert any(arg.startswith('--user-data-dir=') for arg in cmd)

    def test_ensure_html_pages_rendered_upgrades_stale_v1_and_skips_v2(self, app, db_session):
        upload_folder = app.config['UPLOAD_FOLDER']
        file_service = FileService(upload_folder)

        project = Project(
            project_title='Upgrade Test',
            creation_type='html_renovation',
            image_aspect_ratio='16:9',
            status='DESCRIPTIONS_GENERATED',
        )
        db.session.add(project)
        db.session.flush()

        pages_dir = os.path.join(upload_folder, project.id, 'pages')
        os.makedirs(pages_dir, exist_ok=True)

        p1 = Page(project_id=project.id, order_index=0, status='DESCRIPTION_GENERATED')
        p2 = Page(project_id=project.id, order_index=1, status='DESCRIPTION_GENERATED')
        p3 = Page(project_id=project.id, order_index=2, status='COMPLETED')
        db.session.add_all([p1, p2, p3])
        db.session.flush()

        for idx, p in enumerate((p1, p2, p3)):
            with open(os.path.join(pages_dir, f'{p.id}.html'), 'w', encoding='utf-8') as f:
                f.write(f'<!DOCTYPE html><html><body><h1>Slide {idx + 1}</h1></body></html>')

        # p1: stale Pillow fallback _v1.png
        p1_rel = f'{project.id}/pages/{p1.id}_v1.png'
        fb_img = Image.new('RGB', (1280, 720), color=(248, 250, 252))
        fb_img.info['banana_renderer'] = 'pillow_fallback'
        save_rendered_html_slide_png(fb_img, os.path.join(upload_folder, p1_rel))
        p1.generated_image_path = p1_rel

        # p2: already Chromium-rendered _v1.png
        p2_rel = f'{project.id}/pages/{p2.id}_v1.png'
        ok_img = Image.new('RGB', (1920, 1080), color=(250, 248, 245))
        ok_img.info['banana_renderer'] = 'chromium'
        save_rendered_html_slide_png(ok_img, os.path.join(upload_folder, p2_rel))
        p2.generated_image_path = p2_rel

        # p3: AI-regenerated _v2.png (must not be overwritten)
        p3_rel = f'{project.id}/pages/{p3.id}_v2.png'
        Image.new('RGB', (1920, 1080), color=(12, 34, 56)).save(os.path.join(upload_folder, p3_rel), 'PNG')
        p3.generated_image_path = p3_rel
        db.session.commit()

        rendered_calls = []

        def fake_render(html_file_path, width, height, **kwargs):
            rendered_calls.append((html_file_path, width, height))
            out = Image.new('RGB', (1920, 1080), color=(255, 0, 128))
            out.info['banana_renderer'] = 'chromium'
            return out

        with (
            patch('services.html_slide_service._find_headless_browser', return_value='/usr/bin/chromium'),
            patch('services.html_slide_service._render_with_headless_browser', side_effect=fake_render),
        ):
            upgraded = ensure_html_pages_rendered(
                [p1, p2, p3],
                project,
                file_service,
                max_workers=2,
                db_session=db.session,
            )

        assert upgraded == 1
        assert len(rendered_calls) == 1
        assert p1.id in rendered_calls[0][0]
        assert is_chromium_rendered_png(file_service.get_absolute_path(p1.generated_image_path)) is True
        with Image.open(file_service.get_absolute_path(p1.generated_image_path)) as upgraded_img:
            assert upgraded_img.size == (1920, 1080)
        with Image.open(file_service.get_absolute_path(p3.generated_image_path)) as v2_img:
            assert v2_img.getpixel((0, 0)) == (12, 34, 56)
