"""
AI Providers factory module

Provides factory functions to get the Google Gemini text/image generation providers
based on database settings or environment configuration.

Configuration priority (highest -> lowest):
    0. Client request/thread-local override (per-client browser credentials)
    1. Database settings (Flask app.config, persisted via Settings page)
    2. Environment variables (.env file)
    3. Hard-coded defaults

Supported provider format:
    gemini    -- Google AI Studio / Gemini API (API key auth)
"""
import os
import logging
from typing import Any, Dict, Optional

from .text import TextProvider, GenAITextProvider, OpenAITextProvider, AnthropicTextProvider, LazyLLMTextProvider, CodexTextProvider
from .image import ImageProvider, GenAIImageProvider, OpenAIImageProvider, AnthropicImageProvider, LazyLLMImageProvider, CodexImageProvider
from .lazyllm_env import TEXT2IMAGE_CAPABLE_LAZYLLM_VENDORS

logger = logging.getLogger(__name__)

__all__ = [
    'TextProvider', 'GenAITextProvider', 'OpenAITextProvider', 'AnthropicTextProvider', 'LazyLLMTextProvider', 'CodexTextProvider',
    'ImageProvider', 'GenAIImageProvider', 'OpenAIImageProvider', 'AnthropicImageProvider', 'LazyLLMImageProvider', 'CodexImageProvider',
    'get_text_provider', 'get_image_provider', 'get_provider_format',
    'get_caption_provider', 'get_image_caption_provider_config', 'LAZYLLM_VENDORS',
    'get_default_models_for_provider',
]

# Legacy export kept for backwards compatibility
LAZYLLM_VENDORS = {'qwen', 'doubao', 'deepseek', 'glm', 'siliconflow', 'sensenova', 'minimax', 'kimi', 'ppio', 'aiping'}

_GOOGLE_MODEL_PREFIXES = ('gemini', 'imagen', 'gemma', 'learnlm', 'models/')


def get_provider_format() -> str:
    """Return the active AI provider format (Google Gemini only)."""
    return 'gemini'


def _resolve_setting(key: str, fallback: Optional[str] = None) -> Optional[str]:
    """Look up a configuration value using the standard priority chain.

    Empty-string values are treated as unset at every level.

    Resolution order:
        0. Client request/thread-local override (per-client browser credentials)
        1. Flask ``app.config`` (populated from the database Settings page)
        2. OS environment variable
        3. *fallback* argument (may be ``None``)
    """
    # 0) Try client override first
    try:
        from utils.client_settings import get_current_client_override
        client_override = get_current_client_override()
        if client_override:
            client_fmt = str(client_override.get('ai_provider_format') or 'gemini').lower()
            if key == 'GOOGLE_API_KEY' and client_fmt == 'gemini':
                client_key = client_override.get('api_key')
                if client_key:
                    return str(client_key)
            elif key == 'GOOGLE_API_BASE' and client_fmt == 'gemini':
                client_base = client_override.get('api_base_url')
                if client_base:
                    return str(client_base)
            elif key == 'MINERU_TOKEN':
                token = client_override.get('mineru_token')
                if token:
                    return str(token)
            elif key == 'BAIDU_API_KEY':
                bkey = client_override.get('baidu_api_key')
                if bkey:
                    return str(bkey)
            elif key == 'ELEVENLABS_API_KEY':
                ekey = client_override.get('elevenlabs_api_key')
                if ekey:
                    return str(ekey)
            elif key == 'TEXT_MODEL':
                tm = client_override.get('text_model')
                if tm:
                    return str(tm)
            elif key == 'IMAGE_MODEL':
                im = client_override.get('image_model')
                if im:
                    return str(im)
            elif key == 'IMAGE_CAPTION_MODEL':
                cm = client_override.get('image_caption_model') or client_override.get('text_model')
                if cm:
                    return str(cm)
    except Exception:
        pass

    # 1) Try Flask app.config
    try:
        from flask import current_app
        from config import is_placeholder_api_key
        if current_app and hasattr(current_app, 'config') and key in current_app.config:
            val = current_app.config[key]
            if val and not (('KEY' in key or 'TOKEN' in key) and is_placeholder_api_key(str(val))):
                logger.debug("Setting %s resolved from app.config", key)
                return str(val)
    except RuntimeError:
        pass  # outside Flask request context

    # 2) Try environment
    env_val = os.getenv(key)
    if env_val:
        from config import is_placeholder_api_key
        if not (('KEY' in key or 'TOKEN' in key) and is_placeholder_api_key(env_val)):
            logger.debug("Setting %s resolved from environment", key)
            return env_val

    # 3) Fallback
    if fallback is not None:
        logger.debug("Setting %s using fallback: %s", key, fallback)
    return fallback


def _build_provider_config() -> Dict[str, Any]:
    """Assemble Google Gemini provider configuration dict.

    Raises ``ValueError`` when GOOGLE_API_KEY is missing.
    """
    api_key = _resolve_setting('GOOGLE_API_KEY')
    api_base = _resolve_setting('GOOGLE_API_BASE')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY (from database settings or environment) is required")
    logger.info(
        "Provider config -- format: gemini, api_base: %s, api_key: %s",
        api_base,
        '***' if api_key else 'None',
    )
    return {
        'format': 'gemini',
        'api_key': api_key,
        'api_base': api_base,
    }


def _get_model_type_provider_config(model_type: str) -> Dict[str, Any]:
    """Return Google Gemini provider config for a model type (with optional per-model key/base override)."""
    prefix = model_type.upper()
    api_key = _resolve_setting(f'{prefix}_API_KEY') or _resolve_setting('GOOGLE_API_KEY')
    api_base = _resolve_setting(f'{prefix}_API_BASE') or _resolve_setting('GOOGLE_API_BASE')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY (from database settings or environment) is required")
    return {
        'format': 'gemini',
        'api_key': api_key,
        'api_base': api_base,
    }


def get_default_models_for_provider(fmt: str = 'gemini', api_base: Optional[str] = None, source: Optional[str] = None) -> Dict[str, str]:
    """Return default (text, image, caption) Google Gemini models."""
    return {
        'text': 'gemini-3-flash-preview',
        'caption': 'gemini-3-flash-preview',
        'image': 'gemini-3-pro-image-preview',
    }


def _normalize_model_for_provider(model: str, role: str, config: Dict[str, Any]) -> str:
    """Normalize empty or stale non-Google model names to Google Gemini defaults."""
    trimmed = (model or '').strip()
    default_model = 'gemini-3-pro-image-preview' if role == 'image' else 'gemini-3-flash-preview'
    if not trimmed:
        return default_model
    if not trimmed.lower().startswith(_GOOGLE_MODEL_PREFIXES):
        logger.info("Normalizing non-Google %s model '%s' -> '%s'", role, trimmed, default_model)
        return default_model
    return trimmed


def get_image_caption_provider_config() -> Dict[str, Any]:
    """Get provider config specifically for image caption model."""
    return _get_model_type_provider_config('image_caption')


def get_caption_provider(model: str = "gemini-3-flash-preview") -> TextProvider:
    """Factory: return a Google Gemini TextProvider for image caption tasks."""
    config = _get_model_type_provider_config('image_caption')
    model = _normalize_model_for_provider(model, 'caption', config)
    logger.info("Caption provider: Gemini, model=%s", model)
    return GenAITextProvider(api_key=config['api_key'], api_base=config['api_base'], model=model)


def get_text_provider(model: str = "gemini-3-flash-preview") -> TextProvider:
    """Factory: return a Google Gemini TextProvider."""
    config = _get_model_type_provider_config('text')
    model = _normalize_model_for_provider(model, 'text', config)
    logger.info("Text provider: Gemini, model=%s", model)
    return GenAITextProvider(api_key=config['api_key'], api_base=config['api_base'], model=model)


def get_image_provider(model: str = "gemini-3-pro-image-preview") -> ImageProvider:
    """Factory: return a Google Gemini ImageProvider."""
    config = _get_model_type_provider_config('image')
    model = _normalize_model_for_provider(model, 'image', config)
    logger.info("Image provider: Gemini, model=%s", model)
    return GenAIImageProvider(api_key=config['api_key'], api_base=config['api_base'], model=model)
