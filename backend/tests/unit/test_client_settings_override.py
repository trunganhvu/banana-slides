"""Unit tests for client-scoped settings override."""

import pytest
from flask import Flask
from utils.client_settings import (
    extract_client_settings_from_request,
    get_current_client_override,
    client_settings_scope,
)
from services.ai_providers import get_provider_format, _resolve_setting
from services.ai_providers.lazyllm_env import get_lazyllm_api_key


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.config['AI_PROVIDER_FORMAT'] = 'gemini'
    flask_app.config['GOOGLE_API_KEY'] = 'server-gemini-key'
    flask_app.config['OPENAI_API_KEY'] = 'server-openai-key'
    return flask_app


def test_extract_client_settings_from_headers(app):
    with app.test_request_context(
        '/',
        headers={
            'X-Client-Storage-Mode': 'client',
            'X-Client-Provider': 'openai',
            'X-Client-Api-Key': 'client-sk-test123',
            'X-Client-Api-Base': 'https://custom-openai.com/v1',
            'X-Client-Lazyllm-Keys': '{"deepseek": "client-ds-key"}',
            'X-Client-Text-Model': 'gpt-4o',
            'X-Client-Image-Model': 'dall-e-3',
            'X-Client-Mineru-Token': 'client-mineru',
            'X-Client-Baidu-Key': 'client-baidu',
            'X-Client-Elevenlabs-Key': 'client-elevenlabs',
        },
    ):
        override = extract_client_settings_from_request()
        assert override is not None
        assert override['ai_provider_format'] == 'openai'
        assert override['api_key'] == 'client-sk-test123'
        assert override['api_base_url'] == 'https://custom-openai.com/v1'
        assert override['lazyllm_api_keys'] == {'deepseek': 'client-ds-key'}
        assert override['text_model'] == 'gpt-4o'
        assert override['image_model'] == 'dall-e-3'
        assert override['mineru_token'] == 'client-mineru'
        assert override['baidu_api_key'] == 'client-baidu'
        assert override['elevenlabs_api_key'] == 'client-elevenlabs'


def test_client_override_precedence(app):
    with app.app_context():
        # Without client override, default server settings are used
        assert get_provider_format() == 'gemini'
        assert _resolve_setting('GOOGLE_API_KEY') == 'server-gemini-key'

        # Inside client_settings_scope, client settings override server values
        client_data = {
            'ai_provider_format': 'deepseek',
            'api_key': 'client-active-key',
            'lazyllm_api_keys': {'deepseek': 'client-deepseek-key-123'},
            'text_model': 'deepseek-chat',
        }

        with client_settings_scope(client_data):
            assert get_provider_format() == 'deepseek'
            assert get_lazyllm_api_key('deepseek') == 'client-deepseek-key-123'
            assert _resolve_setting('TEXT_MODEL') == 'deepseek-chat'

        # Outside scope, reverts to server settings cleanly
        assert get_provider_format() == 'gemini'
        assert _resolve_setting('GOOGLE_API_KEY') == 'server-gemini-key'


def test_request_headers_override_resolution(app):
    with app.test_request_context(
        '/',
        headers={
            'X-Client-Storage-Mode': 'client',
            'X-Client-Provider': 'volcengine',
            'X-Client-Api-Key': 'client-volc-key-999',
            'X-Client-Api-Base': 'https://volcengine-proxy.com/api',
        },
    ):
        assert get_provider_format() == 'volcengine'
        assert _resolve_setting('VOLCENGINE_API_KEY') == 'client-volc-key-999'
        assert _resolve_setting('VOLCENGINE_API_BASE') == 'https://volcengine-proxy.com/api'
