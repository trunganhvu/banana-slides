"""Client-scoped settings override utilities.

Allows individual client browsers/devices to supply encrypted or per-session API keys
via HTTP headers without persisting personal credentials into the server's global SQLite database.
"""

import json
import logging
import threading
from contextlib import contextmanager
from typing import Any, Dict, Optional
from flask import has_request_context, request

logger = logging.getLogger(__name__)

# Thread-local storage for background tasks or explicit code scopes
_thread_local = threading.local()


def extract_client_settings_from_request(req=None) -> Optional[Dict[str, Any]]:
    """Extract client-provided override settings from HTTP request headers.

    Headers checked:
        X-Client-Storage-Mode: 'client'
        X-Client-Provider: Provider format (e.g. 'gemini', 'openai', 'deepseek')
        X-Client-Api-Key: API key for the active provider
        X-Client-Api-Base: Custom API base URL
        X-Client-Lazyllm-Keys: JSON string of vendor keys (e.g. {"deepseek": "sk-..."})
        X-Client-Text-Model: Override text model
        X-Client-Image-Model: Override image model
        X-Client-Mineru-Token: Token for MinerU PDF parser
        X-Client-Baidu-Key: API key for Baidu OCR
        X-Client-Elevenlabs-Key: API key for ElevenLabs TTS
    """
    r = req or (request if has_request_context() else None)
    if not r or not hasattr(r, 'headers'):
        return None

    storage_mode = r.headers.get('X-Client-Storage-Mode')
    client_key = r.headers.get('X-Client-Api-Key')
    client_provider = r.headers.get('X-Client-Provider')

    if not client_key and not client_provider and storage_mode != 'client':
        return None

    override: Dict[str, Any] = {}

    if client_provider:
        override['ai_provider_format'] = client_provider.strip().lower()

    if client_key:
        override['api_key'] = client_key.strip()

    client_base = r.headers.get('X-Client-Api-Base')
    if client_base:
        override['api_base_url'] = client_base.strip()

    lazy_keys_raw = r.headers.get('X-Client-Lazyllm-Keys')
    if lazy_keys_raw:
        try:
            parsed = json.loads(lazy_keys_raw)
            if isinstance(parsed, dict):
                override['lazyllm_api_keys'] = parsed
        except Exception as e:
            logger.warning("Failed to parse X-Client-Lazyllm-Keys header: %s", e)

    text_model = r.headers.get('X-Client-Text-Model')
    if text_model:
        override['text_model'] = text_model.strip()

    image_model = r.headers.get('X-Client-Image-Model')
    if image_model:
        override['image_model'] = image_model.strip()

    mineru_token = r.headers.get('X-Client-Mineru-Token')
    if mineru_token:
        override['mineru_token'] = mineru_token.strip()

    baidu_key = r.headers.get('X-Client-Baidu-Key')
    if baidu_key:
        override['baidu_api_key'] = baidu_key.strip()

    elevenlabs_key = r.headers.get('X-Client-Elevenlabs-Key')
    if elevenlabs_key:
        override['elevenlabs_api_key'] = elevenlabs_key.strip()

    return override if override else None


def get_current_client_override() -> Optional[Dict[str, Any]]:
    """Get active client settings override for current thread or request context.

    Checks thread-local scope first (for background tasks), then active Flask request.
    """
    # 1. Thread-local override
    tl_override = getattr(_thread_local, 'client_override', None)
    if tl_override is not None:
        return tl_override

    # 2. Flask request context
    if has_request_context():
        return extract_client_settings_from_request()

    return None


@contextmanager
def client_settings_scope(override: Optional[Dict[str, Any]]):
    """Context manager binding a client settings override to the current execution thread.

    Thread-safe and restores previous state upon exit.
    """
    if not override:
        yield
        return

    previous = getattr(_thread_local, 'client_override', None)
    _thread_local.client_override = override
    try:
        yield
    finally:
        if previous is not None:
            _thread_local.client_override = previous
        elif hasattr(_thread_local, 'client_override'):
            del _thread_local.client_override
