import pytest
from unittest.mock import MagicMock, patch
from services.prompts import get_style_from_content_prompt
from services.ai_service import AIService
from app import create_app


def test_get_style_from_content_prompt_structure_zh():
    content = " AI "
    prompt = get_style_from_content_prompt(content=content, language='zh')

    assert content in prompt
    assert "" in prompt
    assert "" in prompt
    assert "" in prompt
    assert "" in prompt
    assert "" in prompt
    assert "" in prompt


def test_get_style_from_content_prompt_structure_en():
    content = "AI in Healthcare and Medical Imaging Diagnostics."
    prompt = get_style_from_content_prompt(content=content, language='en')

    assert content in prompt
    assert "Visual Description" in prompt
    assert "Color & Material" in prompt
    assert "Content & Typography" in prompt
    assert "Illustration & Rendering" in prompt


def test_ai_service_generate_style_from_content():
    ai_service = AIService.__new__(AIService)
    mock_provider = MagicMock()
    mock_provider.generate_text.return_value = "...\n#FFFFFF..."
    ai_service.text_provider = mock_provider

    res = ai_service.generate_style_from_content("AI ", language='zh')
    assert "" in res
    mock_provider.generate_text.assert_called_once()
    # Check that it called generate_text without invalid temperature keyword arg
    assert 'temperature' not in mock_provider.generate_text.call_args.kwargs


def test_ai_service_generate_style_from_content_empty():
    ai_service = AIService.__new__(AIService)
    with pytest.raises(ValueError, match="Content cannot be empty"):
        ai_service.generate_style_from_content("   ")


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_generate_style_from_content_api_success(client):
    with patch('controllers.project_controller.get_ai_service') as mock_get_ai:
        mock_ai = MagicMock()
        mock_ai.generate_style_from_content.return_value = "...\n#0B1F3B"
        mock_get_ai.return_value = mock_ai

        response = client.post('/api/generate-style-from-content', json={
            'content': '2026',
            'language': 'zh'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert "" in data['data']['style_description']
        mock_ai.generate_style_from_content.assert_called_once_with(
            content='2026',
            language='zh'
        )


def test_generate_style_from_content_api_validation(client):
    response = client.post('/api/generate-style-from-content', json={
        'content': '   '
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False