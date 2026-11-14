"""
AIService singleton manager for optimizing provider initialization

This module provides a singleton pattern implementation for AIService to avoid
repeated initialization of AI providers (TextProvider and ImageProvider) on every request.

Benefits:
- Reuses AI provider instances across requests
- Reduces initialization overhead
- Better resource management
- Thread-safe for Flask multi-threaded environment

Usage:
    from services.ai_service_manager import get_ai_service
    
    # In your controller
    ai_service = get_ai_service()
    outline = ai_service.generate_outline(project_context)
"""

import hashlib
import logging
from threading import Lock
from typing import Optional, Tuple
from flask import current_app, has_app_context
from .ai_service import AIService
from .ai_providers import (
    get_text_provider,
    get_image_provider,
    get_caption_provider,
    get_provider_format,
    _resolve_setting,
    TextProvider,
    ImageProvider,
)

logger = logging.getLogger(__name__)

# Global singleton instance
_ai_service_instance: Optional[AIService] = None
_last_config_signature: Optional[Tuple] = None
_lock = Lock()

# Provider cache to avoid re-initialization when models don't change
_text_provider_cache: dict = {}
_image_provider_cache: dict = {}
_caption_provider_cache: dict = {}
_cache_lock = Lock()


def _hash_secret(val: Optional[str]) -> str:
    if not val:
        return ""
    return hashlib.sha256(str(val).encode("utf-8")).hexdigest()[:12]


def _get_active_config_signature() -> Tuple:
    """Compute a lightweight signature of current Gemini credentials, endpoint, and models."""
    from config import get_config
    config = get_config()
    fmt = "gemini"
    text_model = _resolve_setting("TEXT_MODEL") or (
        current_app.config.get("TEXT_MODEL", config.TEXT_MODEL)
        if has_app_context() and current_app and hasattr(current_app, "config")
        else config.TEXT_MODEL
    )
    image_model = _resolve_setting("IMAGE_MODEL") or (
        current_app.config.get("IMAGE_MODEL", config.IMAGE_MODEL)
        if has_app_context() and current_app and hasattr(current_app, "config")
        else config.IMAGE_MODEL
    )
    caption_model = _resolve_setting("IMAGE_CAPTION_MODEL") or (
        current_app.config.get("IMAGE_CAPTION_MODEL", config.IMAGE_CAPTION_MODEL)
        if has_app_context() and current_app and hasattr(current_app, "config")
        else config.IMAGE_CAPTION_MODEL
    )
    api_key = _resolve_setting("GOOGLE_API_KEY") or ""
    api_base = _resolve_setting("GOOGLE_API_BASE") or ""
    return (
        fmt,
        text_model,
        image_model,
        caption_model,
        _hash_secret(api_key),
        api_base,
        "",
        "",
        "",
    )


def _get_cached_text_provider(model: str) -> TextProvider:
    """
    Get or create a cached text provider instance
    
    Args:
        model: Model name to use
        
    Returns:
        Cached or new TextProvider instance
    """
    with _cache_lock:
        if model not in _text_provider_cache:
            logger.info(f"Creating new TextProvider for model: {model}")
            _text_provider_cache[model] = get_text_provider(model=model)
        else:
            logger.debug(f"Reusing cached TextProvider for model: {model}")
        return _text_provider_cache[model]


def _get_cached_image_provider(model: str) -> Optional[ImageProvider]:
    """
    Get or create a cached image provider instance
    
    Args:
        model: Model name to use
        
    Returns:
        Cached or new ImageProvider instance
    """
    with _cache_lock:
        if model not in _image_provider_cache:
            logger.info(f"Creating new ImageProvider for model: {model}")
            try:
                _image_provider_cache[model] = get_image_provider(model=model)
            except ValueError as e:
                logger.warning(f"Deferred ImageProvider initialization ({model}): {e}")
                return None
        else:
            logger.debug(f"Reusing cached ImageProvider for model: {model}")
        return _image_provider_cache[model]


def _get_cached_caption_provider(model: str) -> Optional[TextProvider]:
    """Get or create a cached caption provider instance"""
    with _cache_lock:
        if model not in _caption_provider_cache:
            logger.info(f"Creating new CaptionProvider for model: {model}")
            try:
                _caption_provider_cache[model] = get_caption_provider(model=model)
            except ValueError as e:
                logger.warning(f"Deferred CaptionProvider initialization ({model}): {e}")
                return None
        return _caption_provider_cache[model]


def get_ai_service(force_new: bool = False) -> AIService:
    """
    Get the singleton AIService instance with optimized provider caching
    """
    global _ai_service_instance, _last_config_signature
    
    current_sig = _get_active_config_signature()

    if force_new or (_last_config_signature is not None and _last_config_signature != current_sig):
        with _lock:
            logger.info("Configuration change detected or force_new requested; refreshing AIService instance")
            _ai_service_instance = None
            with _cache_lock:
                _text_provider_cache.clear()
                _image_provider_cache.clear()
                _caption_provider_cache.clear()
    
    if _ai_service_instance is None:
        with _lock:
            # Double-check locking pattern
            if _ai_service_instance is None:
                logger.info("Initializing AIService singleton with provider caching")
                
                _, text_model, image_model, caption_model, *_ = current_sig

                # Get cached providers
                text_provider = _get_cached_text_provider(text_model)
                image_provider = _get_cached_image_provider(image_model)
                caption_provider = _get_cached_caption_provider(caption_model) or text_provider

                # Create AIService with cached providers
                _ai_service_instance = AIService(
                    text_provider=text_provider,
                    image_provider=image_provider,
                    caption_provider=caption_provider
                )
                _last_config_signature = current_sig

                logger.info(f"AIService singleton created with models: text={text_model}, image={image_model}, caption={caption_model}")
    
    return _ai_service_instance


def clear_ai_service_cache():
    """
    Clear the AIService singleton and provider cache
    """
    global _ai_service_instance, _last_config_signature
    
    with _lock:
        _ai_service_instance = None
        _last_config_signature = None
        logger.info("AIService singleton cache cleared")
        with _cache_lock:
            _text_provider_cache.clear()
            _image_provider_cache.clear()
            _caption_provider_cache.clear()
            logger.info("Provider cache cleared")


def get_provider_cache_info() -> dict:
    """
    Get information about cached providers (for debugging/monitoring)
    
    Returns:
        Dictionary with cache statistics
    """
    with _cache_lock:
        return {
            "text_providers": list(_text_provider_cache.keys()),
            "image_providers": list(_image_provider_cache.keys()),
            "caption_providers": list(_caption_provider_cache.keys()),
            "total_cached": len(_text_provider_cache) + len(_image_provider_cache) + len(_caption_provider_cache)
        }
