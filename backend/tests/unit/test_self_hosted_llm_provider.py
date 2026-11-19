"""Unit tests for minimalist self-hosted / OpenAI-compatible LLM provider support."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from openai import BadRequestError

from controllers.settings_controller import _sync_settings_to_config, temporary_settings_override
from models import Settings, db
from services.ai_providers import (
    _normalize_model_for_provider,
    _resolve_setting,
    get_caption_provider,
    get_provider_format,
    get_text_provider,
)
from services.ai_providers.openai_compat import (
    LOCAL_DUMMY_API_KEY,
    discover_openai_compatible_models,
    is_local_or_private_base_url,
    normalize_openai_base_url,
    normalize_provider_format,
    parse_provider_format,
)
from services.ai_providers.text.openai_provider import OpenAITextProvider
from services.ai_service import AIService
from utils.client_settings import client_settings_scope


class TestProviderAndUrlHelpers:
    def test_parse_and_normalize_provider_aliases(self):
        assert parse_provider_format("gemini") == "gemini"
        assert parse_provider_format("openai") == "openai"
        assert parse_provider_format("local") == "openai"
        assert parse_provider_format("self_hosted") == "openai"
        assert parse_provider_format("self-hosted") == "openai"
        assert parse_provider_format("openai_compatible") == "openai"
        assert parse_provider_format("unknown_legacy") is None
        assert normalize_provider_format("unknown_legacy", default="gemini") == "gemini"

    def test_normalize_openai_base_url_variants(self, monkeypatch):
        monkeypatch.delenv("IN_DOCKER", raising=False)
        monkeypatch.setattr("services.ai_providers.openai_compat.is_running_in_docker", lambda: False)

        assert normalize_openai_base_url("http://localhost:11434") == "http://localhost:11434/v1"
        assert normalize_openai_base_url("http://localhost:1234/v1/") == "http://localhost:1234/v1"
        assert normalize_openai_base_url("http://192.168.1.50:8000/v1/chat/completions") == "http://192.168.1.50:8000/v1"
        assert normalize_openai_base_url("http://192.168.1.50:3000/ollama/v1/") == "http://192.168.1.50:3000/ollama/v1"
        assert normalize_openai_base_url("localhost:11434") == "http://localhost:11434/v1"

    def test_docker_loopback_rewrite(self, monkeypatch):
        monkeypatch.setattr("services.ai_providers.openai_compat.is_running_in_docker", lambda: True)
        monkeypatch.setenv("DOCKER_HOST_GATEWAY", "host.docker.internal")

        assert normalize_openai_base_url("http://localhost:11434") == "http://host.docker.internal:11434/v1"
        assert normalize_openai_base_url("http://127.0.0.1:8080/v1") == "http://host.docker.internal:8080/v1"
        assert (
            normalize_openai_base_url("http://localhost:11434", rewrite_docker_localhost=False)
            == "http://localhost:11434/v1"
        )
        assert is_local_or_private_base_url("http://192.168.1.25:1234/v1") is True
        assert is_local_or_private_base_url("https://api.openai.com/v1") is False


class TestKeylessSelfHostedProviders:
    def test_keyless_text_and_caption_providers_preserve_custom_model(self, monkeypatch):
        monkeypatch.setattr("services.ai_providers.openai_compat.is_running_in_docker", lambda: False)
        flask_app = Flask(__name__)
        flask_app.config.update(
            AI_PROVIDER_FORMAT="openai",
            OPENAI_API_KEY="",
            OPENAI_API_BASE="http://localhost:11434",
            TEXT_MODEL="qwen2.5:14b",
            IMAGE_MODEL="",
            IMAGE_CAPTION_MODEL="",
        )

        with flask_app.app_context():
            assert get_provider_format() == "openai"
            text_provider = get_text_provider(model="qwen2.5:14b")
            caption_provider = get_caption_provider(model="")

            assert isinstance(text_provider, OpenAITextProvider)
            assert text_provider.model == "qwen2.5:14b"
            assert str(text_provider.client.base_url).rstrip("/") == "http://localhost:11434/v1"
            assert text_provider.client.api_key == LOCAL_DUMMY_API_KEY
            assert text_provider.is_local is True

            assert isinstance(caption_provider, OpenAITextProvider)
            assert caption_provider.model == "qwen2.5:14b"

            # AIService works cleanly in text-only mode when image_model is unset
            ai_service = AIService()
            assert ai_service.image_provider is None
            with pytest.raises(ValueError, match="Image Model"):
                ai_service.generate_image("draw a chart")

    def test_normalize_model_does_not_rewrite_openai_model_to_gemini(self):
        cfg = {"format": "openai"}
        assert _normalize_model_for_provider("llama3.3:70b", "text", cfg) == "llama3.3:70b"
        with pytest.raises(ValueError, match="Text Model"):
            _normalize_model_for_provider("", "text", cfg)

    def test_client_override_security_does_not_leak_server_openai_key(self):
        flask_app = Flask(__name__)
        flask_app.config.update(
            AI_PROVIDER_FORMAT="gemini",
            OPENAI_API_KEY="sk-server-secret",
            OPENAI_API_BASE="https://api.openai.com/v1",
        )
        with flask_app.app_context():
            with client_settings_scope({
                "ai_provider_format": "openai",
                "api_base_url": "http://localhost:1234/v1",
                "text_model": "mistral-7b",
            }):
                assert get_provider_format() == "openai"
                assert _resolve_setting("OPENAI_API_BASE") == "http://localhost:1234/v1"
                assert _resolve_setting("OPENAI_API_KEY") == ""


class TestOpenAITextProviderLocalCompatibility:
    def test_local_endpoint_omits_default_max_tokens_and_strips_think_tags(self):
        mock_resp = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="<think>reasoning</think>\nFinal answer"))]
        )
        with patch("services.ai_providers.text.openai_provider.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_resp
            mock_openai.return_value = mock_client

            provider = OpenAITextProvider(
                api_key=LOCAL_DUMMY_API_KEY,
                api_base="http://localhost:11434/v1",
                model="deepseek-r1:8b",
                is_local=True,
            )
            result = provider.generate_text("Hello")

            assert result == "Final answer"
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert "max_tokens" not in call_kwargs
            assert "max_completion_tokens" not in call_kwargs

    def test_retries_without_max_tokens_on_context_limit_error(self):
        mock_req = MagicMock()
        mock_http_resp = MagicMock(status_code=400, headers={})
        bad_err = BadRequestError(
            "max_tokens exceeds model context length",
            response=mock_http_resp,
            body={"error": {"message": "max_tokens exceeds context"}},
        )
        ok_resp = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None))])

        with patch("services.ai_providers.text.openai_provider.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = [bad_err, ok_resp]
            mock_openai.return_value = mock_client

            provider = OpenAITextProvider(
                api_key="sk-test",
                api_base="https://remote-vllm.example.com/v1",
                model="qwen2.5-72b",
                is_local=False,
            )
            # Ensure max_tokens is initially included, then retried cleanly on 400
            result = provider.generate_text("Hello")
            assert result == ""
            assert mock_client.chat.completions.create.call_count == 2
            first_kwargs = mock_client.chat.completions.create.call_args_list[0].kwargs
            second_kwargs = mock_client.chat.completions.create.call_args_list[1].kwargs
            assert "max_tokens" in first_kwargs
            assert "max_tokens" not in second_kwargs
            assert mock_req is not None


class TestModelDiscoveryAndSettingsLifecycle:
    def test_discover_models_openai_and_ollama_fallback(self, monkeypatch):
        monkeypatch.setattr("services.ai_providers.openai_compat.is_running_in_docker", lambda: False)

        # 1. OpenAI /models success without Authorization header when keyless
        openai_resp = MagicMock(
            ok=True,
            status_code=200,
            json=lambda: {"data": [{"id": "qwen2.5:14b"}, {"id": "llama3.3"}, {"id": "qwen2.5:14b"}]},
        )
        with patch("services.ai_providers.openai_compat.requests.get", return_value=openai_resp) as mock_get:
            res = discover_openai_compatible_models("http://localhost:1234", api_key="")
            assert res["models"] == ["qwen2.5:14b", "llama3.3"]
            assert res["effective_base_url"] == "http://localhost:1234/v1"
            assert res["source"] == "openai_models"
            assert mock_get.call_args.kwargs["headers"] == {}

        # 2. Ollama /api/tags fallback when /v1/models returns 404
        not_found_resp = MagicMock(ok=False, status_code=404, text="Not Found")
        ollama_resp = MagicMock(
            ok=True,
            status_code=200,
            json=lambda: {"models": [{"name": "gemma3:12b"}, {"model": "phi4:latest"}]},
        )
        with patch("services.ai_providers.openai_compat.requests.get", side_effect=[not_found_resp, ollama_resp]):
            res = discover_openai_compatible_models("http://localhost:11434")
            assert res["models"] == ["gemma3:12b", "phi4:latest"]
            assert res["source"] == "ollama_tags"

    def test_settings_switch_gemini_to_openai_and_discover_endpoint(self, app, client):
        with app.app_context():
            # Seed Gemini settings first
            settings = Settings.get_settings()
            settings.ai_provider_format = "gemini"
            settings.api_key = "AIzaOldGeminiKey"
            settings.api_base_url = "https://generativelanguage.googleapis.com"
            db.session.commit()

        # Switch to keyless Self-Hosted Local LLM
        put_resp = client.put(
            "/api/settings",
            json={
                "ai_provider_format": "openai",
                "api_base_url": "http://localhost:11434/v1",
                "api_key": "",
                "text_model": "qwen2.5:14b",
                "image_model": "",
                "image_caption_model": "llava:13b",
            },
        )
        assert put_resp.status_code == 200
        payload = put_resp.get_json()["data"]
        assert payload["ai_provider_format"] == "openai"
        assert payload["api_base_url"] == "http://localhost:11434/v1"
        assert payload["api_key_length"] == 0
        assert payload["text_model"] == "qwen2.5:14b"
        assert payload["image_model"] == ""
        assert payload["image_caption_model"] == "llava:13b"

        get_resp = client.get("/api/settings")
        assert get_resp.status_code == 200
        fetched = get_resp.get_json()["data"]
        assert fetched["ai_provider_format"] == "openai"
        assert fetched["api_base_url"] == "http://localhost:11434/v1"
        assert fetched["text_model"] == "qwen2.5:14b"

        with app.app_context():
            _sync_settings_to_config(Settings.get_settings())
            assert app.config["AI_PROVIDER_FORMAT"] == "openai"
            assert app.config["OPENAI_API_BASE"] == "http://localhost:11434/v1"
            assert app.config["TEXT_MODEL"] == "qwen2.5:14b"

            # Verify temporary_settings_override honors openai and keyless api_key=''
            with temporary_settings_override({
                "ai_provider_format": "openai",
                "api_base_url": "http://localhost:1234/v1",
                "api_key": "",
                "text_model": "phi4",
            }):
                assert app.config["AI_PROVIDER_FORMAT"] == "openai"
                assert app.config["OPENAI_API_BASE"] == "http://localhost:1234/v1"
                assert app.config["OPENAI_API_KEY"] == ""
                assert app.config["TEXT_MODEL"] == "phi4"

        # Discover models endpoint validation & success
        with patch(
            "controllers.settings_controller.discover_openai_compatible_models",
            return_value={
                "models": ["qwen2.5:14b"],
                "effective_base_url": "http://localhost:11434/v1",
                "docker_rewritten": False,
                "source": "openai_models",
            },
        ) as mock_discover:
            # Explicit URL works cleanly
            ok_resp = client.post(
                "/api/settings/discover-models",
                json={"api_base_url": "http://localhost:11434/v1"},
            )
            assert ok_resp.status_code == 200
            assert ok_resp.get_json()["data"]["models"] == ["qwen2.5:14b"]

            # Empty URL falls back to saved openai base URL
            fallback_resp = client.post("/api/settings/discover-models", json={})
            assert fallback_resp.status_code == 200
            assert mock_discover.call_count == 2

        # When saved settings are gemini and payload api_base_url is empty, returns 400
        with app.app_context():
            s = Settings.get_settings()
            s.ai_provider_format = "gemini"
            s.api_base_url = None
            db.session.commit()
        bad_resp = client.post("/api/settings/discover-models", json={"api_base_url": ""})
        assert bad_resp.status_code == 400
