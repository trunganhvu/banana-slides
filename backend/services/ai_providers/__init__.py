"""
AI Providers factory module

Provides factory functions to get the configured text/image generation providers
based on database settings, client overrides, or environment configuration.

Configuration priority (highest -> lowest):
    0. Client request/thread-local override (per-client browser credentials)
    1. Database settings (Flask app.config, persisted via Settings page)
    2. Environment variables (.env file)
    3. Hard-coded defaults

Supported provider formats:
    gemini    -- Google AI Studio / Gemini API (API key auth)
    openai    -- OpenAI-compatible & self-hosted local LLM servers (Ollama, LM Studio, vLLM, llama.cpp...)
"""
import os
import logging
from typing import Any, Dict, Optional

from .text import TextProvider, GenAITextProvider, OpenAITextProvider, AnthropicTextProvider, LazyLLMTextProvider, CodexTextProvider
from .image import ImageProvider, GenAIImageProvider, OpenAIImageProvider, AnthropicImageProvider, LazyLLMImageProvider, CodexImageProvider
from .lazyllm_env import TEXT2IMAGE_CAPABLE_LAZYLLM_VENDORS
from .openai_compat import (
    LOCAL_DUMMY_API_KEY,
    discover_openai_compatible_models,
    is_local_or_private_base_url,
    normalize_openai_base_url,
    normalize_provider_format,
    parse_provider_format,
)

logger = logging.getLogger(__name__)

__all__ = [
    'TextProvider', 'GenAITextProvider', 'OpenAITextProvider', 'AnthropicTextProvider', 'LazyLLMTextProvider', 'CodexTextProvider',
    'ImageProvider', 'GenAIImageProvider', 'OpenAIImageProvider', 'AnthropicImageProvider', 'LazyLLMImageProvider', 'CodexImageProvider',
    'get_text_provider', 'get_image_provider', 'get_provider_format',
    'get_caption_provider', 'get_image_caption_provider_config', 'LAZYLLM_VENDORS',
    'get_default_models_for_provider', 'discover_openai_compatible_models',
]

# Legacy export kept for backwards compatibility
LAZYLLM_VENDORS = {'qwen', 'doubao', 'deepseek', 'glm', 'siliconflow', 'sensenova', 'minimax', 'kimi', 'ppio', 'aiping'}

_GOOGLE_MODEL_PREFIXES = ('gemini', 'imagen', 'gemma', 'learnlm', 'models/')


def get_provider_format() -> str:
    """Return the active canonical AI provider format ('gemini' or 'openai')."""
    try:
        from utils.client_settings import get_current_client_override
        client_override = get_current_client_override()
        if client_override and client_override.get('ai_provider_format'):
            return normalize_provider_format(str(client_override['ai_provider_format']), default='gemini')
    except Exception:
        pass

    try:
        from flask import current_app
        if current_app and hasattr(current_app, 'config'):
            cfg_fmt = current_app.config.get('AI_PROVIDER_FORMAT')
            if cfg_fmt:
                return normalize_provider_format(str(cfg_fmt), default='gemini')
    except RuntimeError:
        pass

    try:
        from models import Settings
        settings = Settings.get_settings()
        if settings and settings.ai_provider_format:
            return normalize_provider_format(settings.ai_provider_format, default='gemini')
    except Exception:
        pass

    return normalize_provider_format(os.getenv('AI_PROVIDER_FORMAT', 'gemini'), default='gemini')


def _resolve_setting(key: str, fallback: Optional[str] = None) -> Optional[str]:
    """Look up a configuration value using the standard priority chain.

    Empty-string values are treated as unset at every level, except when a
    client override specifies an OpenAI-compatible base URL without an API key
    (so server credentials are never leaked to a client-supplied endpoint).

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
            client_fmt = normalize_provider_format(
                str(client_override.get('ai_provider_format') or 'gemini'),
                default='gemini',
            )
            if key == 'AI_PROVIDER_FORMAT' and client_override.get('ai_provider_format'):
                return client_fmt
            if key == 'GOOGLE_API_KEY' and client_fmt == 'gemini':
                client_key = client_override.get('api_key')
                if client_key:
                    return str(client_key)
            elif key == 'GOOGLE_API_BASE' and client_fmt == 'gemini':
                client_base = client_override.get('api_base_url')
                if client_base:
                    return str(client_base)
            elif key == 'OPENAI_API_KEY' and client_fmt == 'openai':
                client_key = client_override.get('api_key')
                if client_key:
                    return str(client_key)
                if client_override.get('api_base_url'):
                    return ""
            elif key == 'OPENAI_API_BASE' and client_fmt == 'openai':
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

    # 1.5) Try database Settings model directly
    try:
        from models import Settings
        from config import is_placeholder_api_key
        settings = Settings.get_settings()
        if settings:
            db_fmt = normalize_provider_format(getattr(settings, 'ai_provider_format', None), default='gemini')
            val = None
            if key == 'AI_PROVIDER_FORMAT':
                if getattr(settings, 'ai_provider_format', None):
                    return db_fmt
            elif key == 'GOOGLE_API_KEY':
                val = getattr(settings, 'api_key', None) if db_fmt == 'gemini' else None
            elif key == 'GOOGLE_API_BASE':
                val = getattr(settings, 'api_base_url', None) if db_fmt == 'gemini' else None
            elif key == 'OPENAI_API_KEY':
                val = getattr(settings, 'api_key', None) if db_fmt == 'openai' else None
            elif key == 'OPENAI_API_BASE':
                val = getattr(settings, 'api_base_url', None) if db_fmt == 'openai' else None
            else:
                val = getattr(settings, key.lower(), None)

            if val and not (('KEY' in key or 'TOKEN' in key) and is_placeholder_api_key(str(val))):
                return str(val)
    except Exception:
        pass

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


def _build_openai_provider_config(prefix: Optional[str] = None) -> Dict[str, Any]:
    """Assemble OpenAI-compatible / self-hosted local LLM config."""
    api_key = (_resolve_setting(f'{prefix}_API_KEY') if prefix else None) or _resolve_setting('OPENAI_API_KEY') or ''
    raw_base = (_resolve_setting(f'{prefix}_API_BASE') if prefix else None) or _resolve_setting('OPENAI_API_BASE') or ''
    api_base = normalize_openai_base_url(raw_base, rewrite_docker_localhost=True) if raw_base else ''
    if not api_base and not api_key:
        raise ValueError(
            "Vui lòng cấu hình API Base URL (ví dụ http://localhost:11434/v1) "
            "hoặc API Key cho Self-Hosted / Local LLM"
        )
    logger.info(
        "Provider config -- format: openai, api_base: %s, api_key: %s",
        api_base or '(default)',
        '***' if api_key else '(keyless)',
    )
    return {
        'format': 'openai',
        'api_key': api_key or LOCAL_DUMMY_API_KEY,
        'api_base': api_base or None,
        'is_local': is_local_or_private_base_url(api_base),
    }


def _build_provider_config() -> Dict[str, Any]:
    """Assemble active AI provider configuration dict."""
    fmt = get_provider_format()
    if fmt == 'openai':
        return _build_openai_provider_config()

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
    """Return provider config for a model type (with optional per-model key/base override)."""
    prefix = model_type.upper()
    fmt = get_provider_format()
    if fmt == 'openai':
        return _build_openai_provider_config(prefix=prefix)

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
    """Return default (text, image, caption) models for the specified provider."""
    if parse_provider_format(fmt) == 'openai':
        return {
            'text': '',
            'caption': '',
            'image': '',
        }
    return {
        'text': 'gemini-3.5-flash-lite',
        'caption': 'gemini-3.5-flash-lite',
        'image': 'gemini-2.5-flash-image',
    }


_MODEL_ALIASES = {
    # Text models (map old/expensive/deprecated models to gemini-3.5-flash-lite)
    'gemini-2.0-flash': 'gemini-3.5-flash-lite',
    'gemini-2.5-flash': 'gemini-3.5-flash-lite',
    'gemini-2.5-flash-lite': 'gemini-3.5-flash-lite',
    'gemini-1.5-flash': 'gemini-3.5-flash-lite',
    'gemini-1.5-pro': 'gemini-3.5-flash-lite',
    'gemini-3-flash-preview': 'gemini-3.5-flash-lite',
    # Image models (map obsolete models)
    'gemini-2.0-flash-preview-image-generation': 'gemini-2.5-flash-image',
    'gemini-2.0-flash-image': 'gemini-2.5-flash-image',
    'gemini-2.0-flash-exp-image': 'gemini-2.5-flash-image',
    'gemini-3-pro-image-preview': 'gemini-3.1-flash-image',
    'imagen-3.0-generate-002': 'gemini-3.1-flash-image',
}


def _normalize_model_for_provider(model: Optional[str], role: str, config: Dict[str, Any]) -> str:
    """Normalize or validate model name according to active provider."""
    trimmed = (model or '').strip()
    if config.get('format') == 'openai':
        if trimmed:
            return trimmed
        if role == 'caption':
            fallback_text = (_resolve_setting('TEXT_MODEL') or '').strip()
            if fallback_text:
                return fallback_text
            raise ValueError("Chưa cấu hình mô hình nhận diện ảnh (Caption/Text Model) cho Self-Hosted LLM")
        if role == 'text':
            raise ValueError("Chưa cấu hình tên mô hình văn bản (Text Model) cho Self-Hosted LLM")
        raise ValueError("Chưa cấu hình mô hình tạo ảnh (Image Model) cho Self-Hosted LLM")

    default_model = 'gemini-2.5-flash-image' if role == 'image' else 'gemini-3.5-flash-lite'
    if not trimmed:
        return default_model
    if trimmed in _MODEL_ALIASES:
        target = _MODEL_ALIASES[trimmed]
        logger.info("Normalizing aliased %s model '%s' -> '%s'", role, trimmed, target)
        return target
    if not trimmed.lower().startswith(_GOOGLE_MODEL_PREFIXES):
        logger.info("Normalizing non-Google %s model '%s' -> '%s'", role, trimmed, default_model)
        return default_model
    return trimmed


def get_image_caption_provider_config() -> Dict[str, Any]:
    """Get provider config specifically for image caption model."""
    return _get_model_type_provider_config('image_caption')


def get_caption_provider(model: Optional[str] = None) -> TextProvider:
    """Factory: return a TextProvider for image caption tasks."""
    config = _get_model_type_provider_config('image_caption')
    candidate = model if model is not None else (_resolve_setting('IMAGE_CAPTION_MODEL') or '')
    resolved_model = _normalize_model_for_provider(candidate, 'caption', config)
    if config['format'] == 'openai':
        logger.info("Caption provider: OpenAI-compatible, model=%s, base=%s", resolved_model, config['api_base'])
        return OpenAITextProvider(
            api_key=config['api_key'],
            api_base=config['api_base'],
            model=resolved_model,
            is_local=config.get('is_local'),
        )
    logger.info("Caption provider: Gemini, model=%s", resolved_model)
    return GenAITextProvider(api_key=config['api_key'], api_base=config['api_base'], model=resolved_model)


def get_text_provider(model: Optional[str] = None) -> TextProvider:
    """Factory: return the active TextProvider."""
    config = _get_model_type_provider_config('text')
    candidate = model if model is not None else (_resolve_setting('TEXT_MODEL') or '')
    resolved_model = _normalize_model_for_provider(candidate, 'text', config)
    if config['format'] == 'openai':
        logger.info("Text provider: OpenAI-compatible, model=%s, base=%s", resolved_model, config['api_base'])
        return OpenAITextProvider(
            api_key=config['api_key'],
            api_base=config['api_base'],
            model=resolved_model,
            is_local=config.get('is_local'),
        )
    logger.info("Text provider: Gemini, model=%s", resolved_model)
    return GenAITextProvider(api_key=config['api_key'], api_base=config['api_base'], model=resolved_model)


def get_image_provider(model: Optional[str] = None) -> ImageProvider:
    """Factory: return the active ImageProvider."""
    config = _get_model_type_provider_config('image')
    candidate = model if model is not None else (_resolve_setting('IMAGE_MODEL') or '')
    resolved_model = _normalize_model_for_provider(candidate, 'image', config)
    if config['format'] == 'openai':
        image_quality = _resolve_setting('IMAGE_QUALITY', 'auto') or 'auto'
        protocol = (_resolve_setting('OPENAI_IMAGE_API_PROTOCOL', 'auto') or 'auto').lower()
        if protocol == 'auto' and 'gemini' not in resolved_model.lower():
            protocol = 'images'
        logger.info(
            "Image provider: OpenAI-compatible, model=%s, base=%s, protocol=%s",
            resolved_model,
            config['api_base'],
            protocol,
        )
        return OpenAIImageProvider(
            api_key=config['api_key'],
            api_base=config['api_base'],
            model=resolved_model,
            image_api_protocol=protocol,
            image_quality=image_quality,
        )
    logger.info("Image provider: Gemini, model=%s", resolved_model)
    return GenAIImageProvider(api_key=config['api_key'], api_base=config['api_base'], model=resolved_model)
