"""
API
"""

import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from conftest import assert_success_response, assert_error_response


class TestProjectCreate:
    """ Test docstring """
    
    def test_create_project_idea_mode(self, client):
        """ Test docstring """
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': 'AIPPT'
        })
        
        data = assert_success_response(response, 201)
        assert 'project_id' in data['data']
        assert data['data']['status'] == 'DRAFT'
    
    def test_create_project_outline_mode(self, client):
        """ Test docstring """
        response = client.post('/api/projects', json={
            'creation_type': 'outline',
            'outline_text': '\n- 1\n\n\n- 2'
        })
        
        data = assert_success_response(response, 201)
        assert 'project_id' in data['data']

    @pytest.mark.parametrize('payload, expected_message', [
        (
            {'creation_type': 'idea', 'idea_prompt': '  \n\t '},
            'idea_prompt must contain non-whitespace text',
        ),
        (
            {'creation_type': 'outline', 'outline_text': ''},
            'outline_text must contain non-whitespace text',
        ),
        (
            {'creation_type': 'descriptions', 'description_text': None},
            'description_text is required',
        ),
        (
            {'creation_type': 'descriptions', 'description_text': ['not text']},
            'description_text must be a string',
        ),
    ])
    def test_create_project_rejects_missing_blank_or_non_text_content(
        self, client, payload, expected_message
    ):
        response = client.post('/api/projects', json=payload)

        data = assert_error_response(response, 400)
        assert data['error']['message'] == expected_message

    def test_create_project_normalizes_selected_content_and_template_style(self, client):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': '  AI   ',
            'outline_text': '',
            'template_style': '    ',
        })

        created = assert_success_response(response, 201)['data']
        project = assert_success_response(
            client.get(f"/api/projects/{created['project_id']}")
        )['data']
        assert project['idea_prompt'] == 'AI '
        assert project['outline_text'] is None
        assert project['template_style'] == ''

    def test_create_project_rejects_non_text_template_style(self, client):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': 'AI ',
            'template_style': {'name': 'invalid'},
        })

        data = assert_error_response(response, 400)
        assert 'template_style' in data['error']['message']

    @pytest.mark.parametrize('template_style', ['', '   \n\t '])
    def test_create_project_normalizes_empty_template_style_to_none(
        self, client, template_style
    ):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': 'AI ',
            'template_style': template_style,
        })

        created = assert_success_response(response, 201)['data']
        project = assert_success_response(
            client.get(f"/api/projects/{created['project_id']}")
        )['data']
        assert project['template_style'] is None
    
    def test_create_project_missing_type(self, client):
        """ Test docstring """
        response = client.post('/api/projects', json={
            'idea_prompt': ''
        })
        
        # Test verification logic
        assert response.status_code in [400, 422]
    
    def test_create_project_invalid_type(self, client):
        """ Test docstring """
        response = client.post('/api/projects', json={
            'creation_type': 'invalid_type',
            'idea_prompt': ''
        })
        
        assert response.status_code in [400, 422]


class TestPageBatchCreate:
    """ Test docstring """

    def test_batch_create_pages_preserves_request_order_and_shifts_existing_pages(self, client):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        data = assert_success_response(response, 201)
        project_id = data['data']['project_id']

        first_page = assert_success_response(client.post(f'/api/projects/{project_id}/pages', json={
            'order_index': 0,
            'outline_content': {'title': '', 'points': ['']},
        }), 201)['data']
        second_page = assert_success_response(client.post(f'/api/projects/{project_id}/pages', json={
            'order_index': 1,
            'outline_content': {'title': '', 'points': ['']},
        }), 201)['data']

        response = client.post(f'/api/projects/{project_id}/pages/batch', json={
            'pages': [
                {
                    'order_index': 1,
                    'part': '',
                    'outline_content': {'title': '', 'points': ['A']},
                    'description_content': {'text': ''},
                },
                {
                    'order_index': 2,
                    'outline_content': {'title': '', 'points': ['B']},
                },
            ]
        })

        created = assert_success_response(response, 201)['data']
        assert [page['outline_content']['title'] for page in created] == ['', '']
        assert created[0]['status'] == 'DESCRIPTION_GENERATED'
        assert created[0]['part'] == ''

        project = assert_success_response(client.get(f'/api/projects/{project_id}'))['data']
        pages = sorted(project['pages'], key=lambda page: page['order_index'])

        assert [page['outline_content']['title'] for page in pages] == [
            '',
            '',
            '',
            '',
        ]
        assert [page['order_index'] for page in pages] == [0, 1, 2, 3]
        assert pages[0]['page_id'] == first_page['page_id']
        assert pages[3]['page_id'] == second_page['page_id']

    def test_batch_create_pages_rejects_empty_payload(self, client):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        data = assert_success_response(response, 201)
        project_id = data['data']['project_id']

        response = client.post(f'/api/projects/{project_id}/pages/batch', json={'pages': []})

        assert response.status_code == 400

    @pytest.mark.parametrize('page_payload', [
        {'order_index': '1', 'outline_content': {'title': 'bad'}},
        {'order_index': 1, 'outline_content': 'bad'},
        {'order_index': 1, 'description_content': 'bad'},
    ])
    def test_batch_create_pages_validates_payload_types(self, client, page_payload):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        data = assert_success_response(response, 201)
        project_id = data['data']['project_id']

        response = client.post(f'/api/projects/{project_id}/pages/batch', json={
            'pages': [page_payload]
        })

        assert response.status_code == 400

    def test_batch_create_pages_allows_null_optional_content(self, client):
        response = client.post('/api/projects', json={
            'creation_type': 'idea',
            'idea_prompt': ''
        })
        data = assert_success_response(response, 201)
        project_id = data['data']['project_id']

        response = client.post(f'/api/projects/{project_id}/pages/batch', json={
            'pages': [{
                'order_index': 0,
                'outline_content': None,
                'description_content': None,
            }]
        })

        created = assert_success_response(response, 201)['data']
        assert created[0]['status'] == 'DRAFT'
        assert created[0]['outline_content'] is None
        assert created[0]['description_content'] is None


class TestProjectGet:
    """ Test docstring """
    
    def test_get_project_success(self, client, sample_project):
        """ Test docstring """
        if not sample_project:
            pytest.skip("")
        
        project_id = sample_project['project_id']
        response = client.get(f'/api/projects/{project_id}')
        
        data = assert_success_response(response)
        assert data['data']['project_id'] == project_id
    
    def test_get_project_not_found(self, client):
        """ Test docstring """
        response = client.get('/api/projects/non-existent-id')
        
        assert response.status_code == 404
    
    def test_get_project_invalid_id_format(self, client):
        """ Test docstring """
        response = client.get('/api/projects/invalid!@#$%id')
        
        # Test verification logic
        assert response.status_code in [400, 404]


class TestResourceConcurrency:
    def test_image_limiter_allows_more_than_global_four_workers(self, app):
        """ Test docstring """
        from services.task_manager import (
            TaskManager,
            ResourceLimiter,
        )

        limiter = ResourceLimiter("image-test", 8)
        executor = ThreadPoolExecutor(max_workers=10)
        started = []
        active = 0
        peak_active = 0
        gate = threading.Event()
        state_lock = threading.Lock()

        def worker(i: int):
            nonlocal active, peak_active
            with limiter.slot(f"page-{i}"):
                with state_lock:
                    started.append(i)
                    active += 1
                    peak_active = max(peak_active, active)
                gate.wait(timeout=5)
                with state_lock:
                    active -= 1

        futures = [executor.submit(worker, i) for i in range(8)]

        deadline = time.time() + 2
        while time.time() < deadline:
            with state_lock:
                if len(started) == 8:
                    break
            time.sleep(0.05)

        gate.set()
        for future in futures:
            future.result(timeout=5)
        executor.shutdown(wait=True)

        assert len(started) == 8
        assert peak_active == 8

    def test_shared_task_pool_no_longer_caps_single_page_image_tasks_at_four(self, app):
        """ Test docstring """
        from models import db, Project, Page
        from controllers import page_controller as page_controller_module
        from services import task_manager as task_manager_module
        from services.task_manager import sync_resource_limits

        class SlowAIService:
            def extract_image_urls_from_markdown(self, _text):
                return []

            def generate_image_prompt(self, *args, **kwargs):
                return "prompt"

            def generate_image(self, *args, **kwargs):
                time.sleep(0.3)
                from PIL import Image
                return Image.new('RGB', (32, 32), color='blue')

        with app.app_context():
            app.config['MAX_IMAGE_WORKERS'] = 8
            app.config['MAX_DESCRIPTION_WORKERS'] = 2
            sync_resource_limits(2, 8)

            project = Project(
                id='proj-concurrency',
                creation_type='idea',
                idea_prompt='test',
                template_style='clean',
                image_aspect_ratio='16:9',
                status='DRAFT',
            )
            db.session.add(project)

            pages = []
            for i in range(5):
                page = Page(project_id=project.id, order_index=i, status='DESCRIPTION_GENERATED')
                page.set_outline_content({'title': f'Page {i+1}', 'points': []})
                page.set_description_content({'text': f'Description {i+1}'})
                db.session.add(page)
                pages.append(page)

            db.session.commit()

            client = app.test_client()
            task_ids = []

            def fake_save_image_with_version(_image, _project_id, _page_id, _file_service, page_obj=None, image_format='PNG'):
                if page_obj:
                    page_obj.generated_image_path = f"generated/{_page_id}.png"
                    page_obj.status = 'COMPLETED'
                return (f"generated/{_page_id}.png", 1)

            with (
                patch.object(page_controller_module, 'get_ai_service', return_value=SlowAIService()),
                patch.object(task_manager_module, 'save_image_with_version', side_effect=fake_save_image_with_version),
            ):
                for page in pages:
                    response = client.post(
                        f'/api/projects/{project.id}/pages/{page.id}/generate/image',
                        json={'force_regenerate': True},
                    )
                    data = assert_success_response(response, 202)
                    task_ids.append(data['data']['task_id'])

                deadline = time.time() + 1.5
                processed = 0
                while time.time() < deadline:
                    statuses = [client.get(f'/api/projects/{project.id}/tasks/{task_id}').get_json()['data']['status'] for task_id in task_ids]
                    processed = sum(status in {'PROCESSING', 'COMPLETED'} for status in statuses)
                    if processed >= 5:
                        break
                    time.sleep(0.05)

                assert processed >= 5

                completion_deadline = time.time() + 3
                while time.time() < completion_deadline:
                    statuses = [client.get(f'/api/projects/{project.id}/tasks/{task_id}').get_json()['data']['status'] for task_id in task_ids]
                    if all(status == 'COMPLETED' for status in statuses):
                        break
                    time.sleep(0.05)

                assert all(status == 'COMPLETED' for status in statuses)


class TestProjectOutlineStream:
    """ Test docstring """

    def test_flatten_outline_preserves_falsy_parent_part_values(self):
        """ Test docstring """
        from services.ai_service import AIService

        service = AIService.__new__(AIService)

        pages = service.flatten_outline([
            {'part': '', 'pages': [{'title': '', 'points': []}]},
            {'part': None, 'pages': [{'title': '', 'points': [], 'part': ''}]},
        ])

        assert pages[0]['part'] == ''
        assert pages[1]['part'] is None

    def test_flatten_outline_strips_title_and_part_whitespace(self):
        """ Test docstring """
        from services.ai_service import AIService

        service = AIService.__new__(AIService)

        pages = service.flatten_outline([
            {'title': '    ', 'points': [], 'part': '    '},
            {'part': '    ', 'pages': [{'title': '    ', 'points': []}]},
        ])

        assert pages[0]['title'] == ''
        assert pages[0]['part'] == ''
        assert pages[1]['title'] == ''
        assert pages[1]['part'] == ''

    def test_flatten_outline_drops_blank_points_from_ai_output(self):
        """ Test docstring """
        from services.ai_service import AIService

        service = AIService.__new__(AIService)

        pages = service.flatten_outline([
            {'title': '', 'points': ['    ', None, '', '   ']},
            {'title': '', 'points': '    '},
            {'title': '', 'points': '   '},
        ])

        assert pages[0]['points'] == ['']
        assert pages[1]['points'] == ['']
        assert pages[2]['points'] == []

    def test_from_description_normalizes_string_outline_pages_after_count_mismatch(self, client, app, monkeypatch):
        """ Test docstring """
        response = client.post('/api/projects', json={
            'creation_type': 'descriptions',
            'description_text': ''
        })
        data = assert_success_response(response, 201)
        project_id = data['data']['project_id']

        class FakeAIService:
            def parse_description_to_outline(self, project_context, language=None):
                return ['', '']

            def parse_description_to_page_descriptions(self, project_context, outline, language=None):
                return [f' {index}' for index in range(16)]

            def flatten_outline(self, outline):
                from services.ai_service import AIService
                service = AIService.__new__(AIService)
                return AIService.flatten_outline(service, outline)

        monkeypatch.setattr('controllers.project_controller.get_ai_service', lambda: FakeAIService())

        generate_response = client.post(
            f'/api/projects/{project_id}/generate/from-description',
            json={'language': 'zh'},
        )

        data = assert_success_response(generate_response)
        assert len(data['data']['pages']) == 2
        assert data['data']['pages'][0]['outline_content'] == {'title': '', 'points': []}
        assert data['data']['pages'][0]['description_content']['text'] == ' 0'

        with app.app_context():
            from models import Page, Project
            project = Project.query.get(project_id)
            pages = Page.query.filter_by(project_id=project_id).order_by(Page.order_index).all()

            assert project.status == 'DESCRIPTIONS_GENERATED'
            assert len(pages) == 2
            assert pages[1].get_outline_content() == {'title': '', 'points': []}
            assert pages[1].get_description_content()['text'] == ' 1'

    def test_description_stream_prompt_uses_latest_description_format(self):
        """ Test docstring """
        from services.ai_service import ProjectContext
        from services.prompts import get_description_to_outline_prompt_markdown

        context = ProjectContext({
            'creation_type': 'descriptions',
            'description_text': '',
        })

        prompt = get_description_to_outline_prompt_markdown(
            context,
            language='zh',
            extra_fields=['Hình ảnh & Tư liệu'],
        )

        assert '<!-- PAGE_DESCRIPTION -->' in prompt
        assert '---  ---' in prompt
        assert '---  ---' in prompt
        # Test verification logic
        assert '' not in prompt
        assert 'Hình ảnh & Tư liệu' in prompt
        assert '' not in prompt

    def test_outline_stream_parses_legacy_outline_only_markdown(self):
        """ Test docstring """
        from services.ai_service import AIService, ProjectContext

        class FakeTextProvider:
            def generate_text_stream(self, prompt, thinking_budget=0):
                yield '# Chuong 1\n## Trang 1\n- Y chinh 1\nMot cau bo sung\n## Trang 2\n- Y chinh 2\n<!-- END -->'

        service = AIService(text_provider=FakeTextProvider(), image_provider=None, caption_provider=None)
        context = ProjectContext({
            'creation_type': 'outline',
            'outline_text': 'Trang 1\n- Y chinh 1\nTrang 2\n- Y chinh 2',
        })

        pages = list(service.generate_outline_stream(context, language='zh'))

        assert pages[:-1] == [
            {'title': 'Trang 1', 'points': ['Y chinh 1', 'Mot cau bo sung'], 'part': 'Chuong 1'},
            {'title': 'Trang 2', 'points': ['Y chinh 2'], 'part': 'Chuong 1'},
        ]
        assert pages[-1] == {'__stream_complete__': True}

    def test_outline_stream_ignores_deck_title_before_cover(self):
        """SSE  deck  H1  part
         # Part """
        from services.ai_service import AIService, ProjectContext

        class FakeTextProvider:
            def generate_text_stream(self, prompt, thinking_budget=0):
                yield (
                    '# Tong quan thi truong\n'
                    '## AI \n'
                    '- Diem noi bat\n'
                    '# Phan 1: Phan tich kinh te\n'
                    '## Xu huong\n'
                    '- Noi dung\n'
                    '<!-- END -->'
                )

        service = AIService(text_provider=FakeTextProvider(), image_provider=None, caption_provider=None)
        context = ProjectContext({
            'creation_type': 'outline',
            'outline_text': 'x',
        })

        pages = list(service.generate_outline_stream(context, language='zh'))
        content = pages[:-1]

        assert len(content) == 2
        # Test verification logic
        assert content[0]['title'] == 'AI '
        assert 'part' not in content[0]
        # Test verification logic
        assert content[1].get('part') == 'Phan 1: Phan tich kinh te'
        assert pages[-1] == {'__stream_complete__': True}

    def test_description_stream_parser_binds_description_to_same_page(self):
        """Test stream parser binds description to same page"""
        from services.ai_service import AIService, ProjectContext

        class FakeTextProvider:
            def generate_text_stream(self, prompt, thinking_budget=0):
                yield (
                    '## Trang 1\n'
                    '<!-- OUTLINE_POINTS -->\n'
                    '- Establish the page purpose and connect the audience from context to the main argument.\n'
                    '<!-- PAGE_DESCRIPTION -->\n'
                    '--- Van ban trang ---\n'
                    '- Boi canh va muc tieu\n'
                    '\n--- Ket thuc van ban trang ---\n'
                    '\nHinh anh & Tu lieu: The chi so quan trong\n'
                    '<!-- PAGE_END -->\n'
                    '<!-- END -->'
                )

        service = AIService(text_provider=FakeTextProvider(), image_provider=None, caption_provider=None)
        context = ProjectContext({
            'creation_type': 'descriptions',
            'description_text': 'Trang 1: Boi canh va muc tieu',
        })

        pages = list(service.generate_outline_stream(context, language='vi'))

        assert pages[0]['title'] == 'Trang 1'
        assert pages[0]['points'] == ['Establish the page purpose and connect the audience from context to the main argument.']
        assert '--- Van ban trang ---' in pages[0]['description_text']
        assert 'Tieu de trang:' not in pages[0]['description_text']
        assert pages[0]['extra_fields']['Hình ảnh & Tư liệu'] == 'The chi so quan trong'
        assert pages[-1] == {'__stream_complete__': True}

    def test_description_stream_persists_outline_and_description(self, client, app, monkeypatch):
        """ Test docstring """
        response = client.post('/api/projects', json={
            'creation_type': 'descriptions',
            'description_text': ''
        })
        data = assert_success_response(response, 201)
        project_id = data['data']['project_id']

        class FakeAIService:
            def generate_outline_stream(self, project_context, language=None):
                yield {
                    'title': '',
                    'points': ['', ''],
                    'description_text': '---  ---\n- \n- \n\n---  ---',
                    'extra_fields': {'Hình ảnh & Tư liệu': ''},
                }
                yield {
                    'title': '',
                    'points': ['', ''],
                    'description_text': '---  ---\n- \n- \n\n---  ---',
                }
                yield {'__stream_complete__': True}

        monkeypatch.setattr('controllers.project_controller.get_ai_service', lambda: FakeAIService())

        stream_response = client.post(
            f'/api/projects/{project_id}/generate/outline/stream',
            json={'language': 'zh'},
            buffered=True,
        )
        assert stream_response.status_code == 200
        body = stream_response.get_data(as_text=True)

        assert 'event: page' in body
        assert 'description_text' in body
        assert 'event: done' in body

        with app.app_context():
            from models import Page, Project
            project = Project.query.get(project_id)
            pages = Page.query.filter_by(project_id=project_id).order_by(Page.order_index).all()

            assert project.status == 'DESCRIPTIONS_GENERATED'
            assert len(pages) == 2
            assert pages[0].get_outline_content() == {'title': '', 'points': ['', '']}
            assert pages[0].get_description_content()['text'].startswith('---  ---')
            assert pages[0].get_description_content()['extra_fields'] == {'Hình ảnh & Tư liệu': ''}
            assert pages[1].get_outline_content()['title'] == ''


class TestProjectUpdate:
    """ Test docstring """
    
    def test_update_project_status(self, client, sample_project):
        """ Test docstring """
        if not sample_project:
            pytest.skip("")
        
        project_id = sample_project['project_id']
        response = client.put(f'/api/projects/{project_id}', json={
            'status': 'GENERATING'
        })
        
        # Test verification logic
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_project_title(self, client, sample_project):
        """ Test docstring """
        if not sample_project:
            pytest.skip("")

        project_id = sample_project['project_id']
        get_before = client.get(f'/api/projects/{project_id}')
        before_data = assert_success_response(get_before)

        response = client.put(f'/api/projects/{project_id}', json={
            'project_title': ''
        })

        data = assert_success_response(response)
        assert data['data']['project_title'] == ''
        assert data['data']['idea_prompt'] == before_data['data']['idea_prompt']


class TestProjectDelete:
    """ Test docstring """
    
    def test_delete_project_success(self, client, sample_project):
        """ Test docstring """
        if not sample_project:
            pytest.skip("")
        
        project_id = sample_project['project_id']
        response = client.delete(f'/api/projects/{project_id}')
        
        data = assert_success_response(response)
        
        # Test verification logic
        get_response = client.get(f'/api/projects/{project_id}')
        assert get_response.status_code == 404
    
    def test_delete_project_not_found(self, client):
        """ Test docstring """
        response = client.delete('/api/projects/non-existent-id')
        
        assert response.status_code == 404