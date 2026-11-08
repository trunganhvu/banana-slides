"""Unit tests for output_language in settings."""

from types import SimpleNamespace
from unittest.mock import patch
from flask import Flask

from controllers.settings_controller import update_settings


def _build_settings(**overrides):
    defaults = {
        'ai_provider_format': 'gemini',
        'api_key': None,
        'api_base_url': None,
        'text_model': None,
        'output_language': 'zh',
    }
    defaults.update(overrides)
    settings = SimpleNamespace(**defaults)
    settings.to_dict = lambda: {
        'ai_provider_format': settings.ai_provider_format,
        'output_language': settings.output_language,
    }
    return settings


def test_update_settings_accepts_output_language_vi():
    """`vi` should be accepted as a valid output language."""
    app = Flask(__name__)
    settings = _build_settings(output_language='zh')

    with app.app_context():
        with app.test_request_context('/api/settings/', method='PUT', json={'output_language': 'vi'}):
            with patch('controllers.settings_controller.Settings.get_settings', return_value=settings):
                with patch('controllers.settings_controller.db.session.commit'):
                    with patch('controllers.settings_controller._sync_settings_to_config'):
                        response, status_code = update_settings()

    assert status_code == 200
    assert settings.output_language == 'vi'


def test_update_settings_accepts_all_valid_languages():
    """All valid languages (vi, zh, en, ja, auto) should be accepted."""
    app = Flask(__name__)

    for lang in ['vi', 'zh', 'en', 'ja', 'auto']:
        settings = _build_settings()
        with app.app_context():
            with app.test_request_context('/api/settings/', method='PUT', json={'output_language': lang}):
                with patch('controllers.settings_controller.Settings.get_settings', return_value=settings):
                    with patch('controllers.settings_controller.db.session.commit'):
                        with patch('controllers.settings_controller._sync_settings_to_config'):
                            response, status_code = update_settings()
        assert status_code == 200
        assert settings.output_language == lang


def test_update_settings_resets_output_language_on_empty():
    """Empty or null output_language should reset to None (fallback to env/default)."""
    app = Flask(__name__)
    settings = _build_settings(output_language='vi')

    with app.app_context():
        with app.test_request_context('/api/settings/', method='PUT', json={'output_language': ''}):
            with patch('controllers.settings_controller.Settings.get_settings', return_value=settings):
                with patch('controllers.settings_controller.db.session.commit'):
                    with patch('controllers.settings_controller._sync_settings_to_config'):
                        response, status_code = update_settings()

    assert status_code == 200
    assert settings.output_language is None


def test_update_settings_rejects_invalid_output_language():
    """Invalid output language should return 400 Bad Request."""
    app = Flask(__name__)
    settings = _build_settings()

    with app.app_context():
        with app.test_request_context('/api/settings/', method='PUT', json={'output_language': 'invalid_lang'}):
            with patch('controllers.settings_controller.Settings.get_settings', return_value=settings):
                with patch('controllers.settings_controller.db.session.commit'):
                    with patch('controllers.settings_controller._sync_settings_to_config'):
                        response, status_code = update_settings()

    assert status_code == 400
    data = response.get_json()
    error_msg = data['error']['message'] if isinstance(data.get('error'), dict) else str(data.get('error'))
    assert "Output language must be 'vi', 'zh', 'en', 'ja', or 'auto'" in error_msg
