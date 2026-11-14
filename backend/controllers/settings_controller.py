"""Settings Controller - handles application settings endpoints"""

import json
import logging
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager
from flask import Blueprint, request, current_app
from PIL import Image
from models import db, Settings, Task
from utils import success_response, error_response, bad_request
from config import Config, PROJECT_ROOT
from services.ai_service import AIService
from services.file_parser_service import FileParserService
from services.ai_providers.ocr.baidu_accurate_ocr_provider import create_baidu_accurate_ocr_provider
from services.ai_providers.image.baidu_inpainting_provider import create_baidu_inpainting_provider
from services.task_manager import task_manager
from services.update_check_service import check_for_update

logger = logging.getLogger(__name__)
ALLOWED_PROVIDER_FORMATS = {"gemini"}
# Backend logic
ALLOWED_IMAGE_QUALITIES = ("auto", "low", "medium", "high", "xhigh", "max")

settings_bp = Blueprint(
    "settings", __name__, url_prefix="/api/settings"
)


PROVIDER_API_CONFIG_KEYS = {
    "gemini": ("GOOGLE_API_KEY", "GOOGLE_API_BASE"),
}


def _provider_api_config_keys(provider_format):
    """Return provider-specific config keys for the global API key/base override (Google Gemini only)."""
    return PROVIDER_API_CONFIG_KEYS.get((provider_format or "gemini").lower(), PROVIDER_API_CONFIG_KEYS["gemini"])


def _provider_api_env_defaults():
    """Return Google Gemini API config values from .env-backed Config defaults."""
    return {
        "GOOGLE_API_KEY": Config.GOOGLE_API_KEY,
        "GOOGLE_API_BASE": Config.GOOGLE_API_BASE,
    }


@contextmanager
def temporary_settings_override(settings_override: dict):
    """
    

    :
        with temporary_settings_override({"api_key": "test-key"}):
            # Backend logic
            result = some_test_function()

    Args:
        settings_override: 

    Yields:
        None
    """
    original_values = {}

    try:
        key_config, base_config = _provider_api_config_keys("gemini")

        if settings_override.get("api_key"):
            original_values[key_config] = current_app.config.get(key_config)
            current_app.config[key_config] = settings_override["api_key"]

        if settings_override.get("api_base_url"):
            original_values[base_config] = current_app.config.get(base_config)
            current_app.config[base_config] = settings_override["api_base_url"]

        original_values["AI_PROVIDER_FORMAT"] = current_app.config.get("AI_PROVIDER_FORMAT")
        current_app.config["AI_PROVIDER_FORMAT"] = "gemini"

        if settings_override.get("text_model"):
            original_values["TEXT_MODEL"] = current_app.config.get("TEXT_MODEL")
            current_app.config["TEXT_MODEL"] = settings_override["text_model"]

        if settings_override.get("image_model"):
            original_values["IMAGE_MODEL"] = current_app.config.get("IMAGE_MODEL")
            current_app.config["IMAGE_MODEL"] = settings_override["image_model"]

        if settings_override.get("image_caption_model"):
            original_values["IMAGE_CAPTION_MODEL"] = current_app.config.get("IMAGE_CAPTION_MODEL")
            current_app.config["IMAGE_CAPTION_MODEL"] = settings_override["image_caption_model"]

        # Clear any legacy per-model provider source overrides for Google Gemini-only tests
        for config_key in (
            "TEXT_MODEL_SOURCE",
            "IMAGE_MODEL_SOURCE",
            "IMAGE_CAPTION_MODEL_SOURCE",
        ):
            if config_key in current_app.config:
                original_values[config_key] = current_app.config.get(config_key)
                current_app.config.pop(config_key, None)

        if settings_override.get("mineru_api_base"):
            original_values["MINERU_API_BASE"] = current_app.config.get("MINERU_API_BASE")
            current_app.config["MINERU_API_BASE"] = settings_override["mineru_api_base"]

        if settings_override.get("mineru_token"):
            original_values["MINERU_TOKEN"] = current_app.config.get("MINERU_TOKEN")
            current_app.config["MINERU_TOKEN"] = settings_override["mineru_token"]

        if settings_override.get("baidu_api_key"):
            original_values["BAIDU_API_KEY"] = current_app.config.get("BAIDU_API_KEY")
            current_app.config["BAIDU_API_KEY"] = settings_override["baidu_api_key"]

        if settings_override.get("image_resolution"):
            original_values["DEFAULT_RESOLUTION"] = current_app.config.get("DEFAULT_RESOLUTION")
            current_app.config["DEFAULT_RESOLUTION"] = settings_override["image_resolution"]

        if settings_override.get("image_quality"):
            original_values["IMAGE_QUALITY"] = current_app.config.get("IMAGE_QUALITY")
            current_app.config["IMAGE_QUALITY"] = settings_override["image_quality"]

        if "enable_text_reasoning" in settings_override:
            original_values["ENABLE_TEXT_REASONING"] = current_app.config.get("ENABLE_TEXT_REASONING")
            current_app.config["ENABLE_TEXT_REASONING"] = settings_override["enable_text_reasoning"]

        if "text_max_output_tokens" in settings_override:
            value = settings_override["text_max_output_tokens"]
            if type(value) is not int or not 1 <= value <= 2147483647:
                raise ValueError("text_max_output_tokens must be a positive 32-bit integer")
            original_values["TEXT_MAX_OUTPUT_TOKENS"] = current_app.config.get("TEXT_MAX_OUTPUT_TOKENS")
            current_app.config["TEXT_MAX_OUTPUT_TOKENS"] = value

        if "text_thinking_budget" in settings_override:
            original_values["TEXT_THINKING_BUDGET"] = current_app.config.get("TEXT_THINKING_BUDGET")
            current_app.config["TEXT_THINKING_BUDGET"] = settings_override["text_thinking_budget"]

        if "enable_image_reasoning" in settings_override:
            original_values["ENABLE_IMAGE_REASONING"] = current_app.config.get("ENABLE_IMAGE_REASONING")
            current_app.config["ENABLE_IMAGE_REASONING"] = settings_override["enable_image_reasoning"]

        if "image_thinking_budget" in settings_override:
            original_values["IMAGE_THINKING_BUDGET"] = current_app.config.get("IMAGE_THINKING_BUDGET")
            current_app.config["IMAGE_THINKING_BUDGET"] = settings_override["image_thinking_budget"]

        yield

    finally:
        # Backend logic
        for key, value in original_values.items():
            if value is not None:
                current_app.config[key] = value
            else:
                current_app.config.pop(key, None)


@settings_bp.route("/", methods=["GET"], strict_slashes=False)
def get_settings():
    """
    GET /api/settings - Get application settings
    """
    try:
        settings = Settings.get_settings()
        return success_response(settings.to_dict())
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return error_response(
            "GET_SETTINGS_ERROR",
            f"Failed to get settings: {str(e)}",
            500,
        )


@settings_bp.route("/check-update", methods=["GET"], strict_slashes=False)
def check_update():
    """
    GET /api/settings/check-update - Check Docker Hub for a newer image.
    """
    try:
        return success_response(check_for_update())
    except Exception as e:
        logger.error(f"Error checking for updates: {str(e)}")
        return error_response(
            "CHECK_UPDATE_ERROR",
            f"Failed to check updates: {str(e)}",
            502,
        )


@settings_bp.route("/", methods=["PUT"], strict_slashes=False)
def update_settings():
    """
    PUT /api/settings - Update application settings

    Request Body:
        {
            "api_base_url": "https://api.example.com",
            "api_key": "your-api-key",
            "image_resolution": "2K",
            "image_aspect_ratio": "16:9"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request("Request body is required")

        settings = Settings.get_settings()

        was_non_gemini = (settings.ai_provider_format or "gemini").lower() != "gemini"
        if "ai_provider_format" in data:
            provider_format = str(data["ai_provider_format"] or "").lower()
            if provider_format not in ALLOWED_PROVIDER_FORMATS:
                allowed_values = "', '".join(sorted(ALLOWED_PROVIDER_FORMATS))
                return bad_request(f"AI provider format must be one of '{allowed_values}'")
        settings.ai_provider_format = "gemini"
        if was_non_gemini:
            settings.api_base_url = None
            settings.api_key = None

        # Update API configuration
        if "api_base_url" in data:
            raw_base_url = data["api_base_url"]
            # Empty string from frontend means "clear override, fall back to env/default"
            if raw_base_url is None:
                settings.api_base_url = None
            else:
                value = str(raw_base_url).strip()
                settings.api_base_url = value if value != "" else None

        if "api_key" in data:
            settings.api_key = data["api_key"]

        # Update image generation configuration
        if "image_resolution" in data:
            resolution = data["image_resolution"]
            if resolution not in ["1K", "2K", "4K"]:
                return bad_request("Resolution must be 1K, 2K, or 4K")
            settings.image_resolution = resolution

        if "image_quality" in data:
            quality = data["image_quality"]
            if quality not in ALLOWED_IMAGE_QUALITIES:
                allowed_values = "', '".join(ALLOWED_IMAGE_QUALITIES)
                return bad_request(f"image_quality must be one of '{allowed_values}'")
            # Store 'auto' literally: an explicit choice in the UI must override
            # an IMAGE_QUALITY value coming from .env, unlike NULL (= follow env).
            settings.image_quality = quality

        if "image_aspect_ratio" in data:
            aspect_ratio = data["image_aspect_ratio"]
            settings.image_aspect_ratio = aspect_ratio

        # Update worker configuration
        if "max_description_workers" in data:
            workers = int(data["max_description_workers"])
            if workers < 1 or workers > 20:
                return bad_request(
                    "Max description workers must be between 1 and 20"
                )
            settings.max_description_workers = workers

        if "max_image_workers" in data:
            workers = int(data["max_image_workers"])
            if workers < 1 or workers > 20:
                return bad_request(
                    "Max image workers must be between 1 and 20"
                )
            settings.max_image_workers = workers

        # Update model & MinerU configuration (optional, empty values fall back to Config)
        if "text_model" in data:
            settings.text_model = (data["text_model"] or "").strip() or None

        if "image_model" in data:
            settings.image_model = (data["image_model"] or "").strip() or None

        if "mineru_api_base" in data:
            settings.mineru_api_base = (data["mineru_api_base"] or "").strip() or None

        if "mineru_token" in data:
            settings.mineru_token = data["mineru_token"]

        if "image_caption_model" in data:
            settings.image_caption_model = (data["image_caption_model"] or "").strip() or None

        if "output_language" in data:
            language = data["output_language"]
            if not language:
                settings.output_language = None
            elif language in ["vi", "zh", "en", "ja", "auto"]:
                settings.output_language = language
            else:
                return bad_request("Output language must be 'vi', 'zh', 'en', 'ja', or 'auto'")

        if "text_max_output_tokens" in data:
            value = data["text_max_output_tokens"]
            if type(value) is not int or not 1 <= value <= 2147483647:
                return bad_request("text_max_output_tokens must be a positive 32-bit integer")
            settings.text_max_output_tokens = value

        # Update description generation mode
        if "description_generation_mode" in data:
            mode = data["description_generation_mode"]
            if mode not in ("streaming", "parallel"):
                return bad_request("description_generation_mode must be 'streaming' or 'parallel'")
            settings.description_generation_mode = mode

        # Update description extra fields
        if "description_extra_fields" in data:
            fields = data["description_extra_fields"]
            if not isinstance(fields, list) or not fields:
                return bad_request("description_extra_fields must be a non-empty array of strings")
            if len(fields) > 10:
                return bad_request("description_extra_fields allows at most 10 items")
            if not all(isinstance(f, str) and f.strip() for f in fields):
                return bad_request("Each extra field must be a non-empty string")
            settings.description_extra_fields = json.dumps([f.strip() for f in fields], ensure_ascii=False)

        if "image_prompt_extra_fields" in data:
            fields = data["image_prompt_extra_fields"]
            if not isinstance(fields, list):
                return bad_request("image_prompt_extra_fields must be an array of strings")
            # Backend logic
            settings.image_prompt_extra_fields = json.dumps([f.strip() for f in fields if isinstance(f, str) and f.strip()], ensure_ascii=False)

        # Update reasoning mode configuration (separate for text and image)
        if "enable_text_reasoning" in data:
            settings.enable_text_reasoning = bool(data["enable_text_reasoning"])
        
        if "text_thinking_budget" in data:
            budget = int(data["text_thinking_budget"])
            if budget < 1 or budget > 8192:
                return bad_request("Text thinking budget must be between 1 and 8192")
            settings.text_thinking_budget = budget
        
        if "enable_image_reasoning" in data:
            settings.enable_image_reasoning = bool(data["enable_image_reasoning"])
        
        if "image_thinking_budget" in data:
            budget = int(data["image_thinking_budget"])
            if budget < 1 or budget > 8192:
                return bad_request("Image thinking budget must be between 1 and 8192")
            settings.image_thinking_budget = budget

        if "enable_image_quality_control" in data:
            settings.enable_image_quality_control = bool(data["enable_image_quality_control"])

        # Update Baidu OCR configuration
        if "baidu_api_key" in data:
            settings.baidu_api_key = data["baidu_api_key"] or None

        # Update ElevenLabs TTS configuration
        if "elevenlabs_enabled" in data:
            settings.elevenlabs_enabled = bool(data["elevenlabs_enabled"])
        if "elevenlabs_api_key" in data:
            settings.elevenlabs_api_key = data["elevenlabs_api_key"] or None
        if "elevenlabs_voice_id" in data:
            settings.elevenlabs_voice_id = (data["elevenlabs_voice_id"] or "").strip() or None

        # Enforce Google Gemini only — clear any legacy non-Google per-model/vendor configuration
        settings.text_model_source = None
        settings.image_model_source = None
        settings.image_caption_model_source = None
        settings.openai_image_api_protocol = None
        settings.lazyllm_api_keys = None
        for model_type in ('text', 'image', 'image_caption'):
            setattr(settings, f'{model_type}_api_key', None)
            setattr(settings, f'{model_type}_api_base_url', None)

        settings.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Sync to app.config
        _sync_settings_to_config(settings)

        logger.info("Settings updated successfully")
        return success_response(
            settings.to_dict(), "Settings updated successfully"
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating settings: {str(e)}")
        return error_response(
            "UPDATE_SETTINGS_ERROR",
            f"Failed to update settings: {str(e)}",
            500,
        )


@settings_bp.route("/reset", methods=["POST"], strict_slashes=False)
def reset_settings():
    """
    POST /api/settings/reset - Reset settings to default values
    """
    try:
        settings = Settings.get_settings()

        # Reset all fields to NULL so .env defaults take over via to_dict()
        settings.ai_provider_format = None
        settings.api_base_url = None
        settings.api_key = None
        settings.text_model = None
        settings.image_model = None
        settings.mineru_api_base = None
        settings.mineru_token = None
        settings.image_caption_model = None
        settings.output_language = None
        settings.enable_text_reasoning = False
        settings.text_max_output_tokens = None
        settings.text_thinking_budget = 1024
        settings.enable_image_reasoning = False
        settings.image_thinking_budget = 1024
        settings.enable_image_quality_control = False
        settings.description_generation_mode = None
        settings.description_extra_fields = None
        settings.image_prompt_extra_fields = None
        settings.baidu_api_key = None
        settings.elevenlabs_enabled = False
        settings.elevenlabs_api_key = None
        settings.elevenlabs_voice_id = None
        settings.text_model_source = None
        settings.image_model_source = None
        settings.image_caption_model_source = None
        settings.openai_image_api_protocol = None
        settings.image_quality = None
        settings.lazyllm_api_keys = None
        for model_type in ('text', 'image', 'image_caption'):
            setattr(settings, f'{model_type}_api_key', None)
            setattr(settings, f'{model_type}_api_base_url', None)
        settings.image_resolution = None
        settings.image_aspect_ratio = None
        settings.max_description_workers = None
        settings.max_image_workers = None
        settings.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        # Sync to app.config
        _sync_settings_to_config(settings)

        logger.info("Settings reset to defaults")
        return success_response(
            settings.to_dict(), "Settings reset to defaults"
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting settings: {str(e)}")
        return error_response(
            "RESET_SETTINGS_ERROR",
            f"Failed to reset settings: {str(e)}",
            500,
        )


@settings_bp.route("/elevenlabs-voices", methods=["GET"], strict_slashes=False)
def get_elevenlabs_voices():
    """ Backend docstring """
    from models import Settings
    db.session.expire_all()
    settings = Settings.get_settings()
    api_key = settings.elevenlabs_api_key
    if not api_key:
        return error_response("ELEVENLABS_KEY_MISSING", "ElevenLabs API Key chưa cấu hình", 400)
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs.core import ApiError as ElevenLabsApiError
        client = ElevenLabs(api_key=api_key)
        try:
            voices_response = client.voices.get_all()
        except ElevenLabsApiError as e:
            body = getattr(e, 'body', None) or {}
            detail = body.get('detail', {}) if isinstance(body, dict) else {}
            status = detail.get('status', '') if isinstance(detail, dict) else ''
            msg = (detail.get('message') if isinstance(detail, dict) else None) or str(e)
            if status == 'missing_permissions':
                return error_response(
                    "ELEVENLABS_KEY_MISSING_PERMISSION",
                    "ElevenLabs API Key thiếu voices_read quyền. Vui lòng vào ElevenLabs Dashboard chỉnh sửa Key và đánh dấu chọn Voices: Read, hoặc tạo 'Has access to all' Key rồi lưu lại. ",
                    400,
                )
            if status == 'invalid_api_key' or e.status_code == 401:
                return error_response("ELEVENLABS_KEY_INVALID", f"ElevenLabs API Key không hợp lệ: {msg}", 400)
            return error_response("ELEVENLABS_VOICES_ERROR", f"ElevenLabs Lỗi (HTTP {e.status_code}): {msg}", 500)
        voices = []
        for v in voices_response.voices:
            labels = getattr(v, "labels", None) or {}
            verified = getattr(v, "verified_languages", None) or []
            languages = []
            seen = set()
            primary = labels.get("language") if isinstance(labels, dict) else None
            if primary and primary not in seen:
                languages.append(primary)
                seen.add(primary)
            for entry in verified:
                lang = entry.get("language") if isinstance(entry, dict) else getattr(entry, "language", None)
                if lang and lang not in seen:
                    languages.append(lang)
                    seen.add(lang)
            voices.append({
                "id": v.voice_id,
                "name": v.name,
                "category": getattr(v, "category", "premade"),
                "languages": languages,
                "accent": labels.get("accent") if isinstance(labels, dict) else None,
            })
        voices.sort(key=lambda v: v["name"])
        return success_response({"voices": voices})
    except Exception as e:
        logger.exception("[elevenlabs-voices] Lấy danh sách giọng đọc thất bại")
        return error_response("ELEVENLABS_VOICES_ERROR", f"Lấy ElevenLabs danh sách giọng đọc thất bại: {e}", 500)


@settings_bp.route("/active-config", methods=["GET"], strict_slashes=False)
def get_active_config():
    """
    GET /api/settings/active-config - Return current app.config values for AI settings.
    Useful for verifying that _sync_settings_to_config correctly restored .env defaults.
    """
    return success_response({
        "ai_provider_format": current_app.config.get("AI_PROVIDER_FORMAT"),
        "text_model": current_app.config.get("TEXT_MODEL"),
        "image_model": current_app.config.get("IMAGE_MODEL"),
        "output_language": current_app.config.get("OUTPUT_LANGUAGE"),
        "image_caption_model": current_app.config.get("IMAGE_CAPTION_MODEL"),
        "enable_image_quality_control": current_app.config.get("ENABLE_IMAGE_QUALITY_CONTROL", False),
    })


@settings_bp.route("/verify", methods=["POST"], strict_slashes=False)
def verify_api_key():
    """
    POST /api/settings/verify - 
     (thinking_budget=0) 

    Returns:
        {
            "data": {
                "available": true/false,
                "message": "Thông tin gợi ý"
            }
        }
    """
    try:
        # Backend logic
        settings = Settings.get_settings()
        if not settings:
            return success_response({
                "available": False,
                "message": "Không tìm thấy cài đặt người dùng"
            })

        # Backend logic
        settings_override = {}
        if settings.api_key:
            settings_override["api_key"] = settings.api_key
        if settings.api_base_url:
            settings_override["api_base_url"] = settings.api_base_url
        if settings.ai_provider_format:
            settings_override["ai_provider_format"] = settings.ai_provider_format
        if settings.text_model:
            settings_override["text_model"] = settings.text_model

        # Backend logic
        with temporary_settings_override(settings_override):
            from services.ai_providers import get_text_provider

            verification_model = (
                settings.text_model
                or current_app.config.get("TEXT_MODEL")
                or Config.TEXT_MODEL
                or "gemini-3-flash-preview"
            )

            # Backend logic
            try:
                provider = get_text_provider(model=verification_model)
                # Backend logic
                provider.generate_text("Hello", thinking_budget=0)

                logger.info("API key verification successful")
                return success_response({
                    "available": True,
                    "message": "API key khả dụng"
                })

            except ValueError as ve:
                # Backend logic
                logger.warning(f"API key not configured: {str(ve)}")
                message = "Google Gemini API key chưa cấu hình, Vui lòng cấu hình trong phần Cài đặt API key và API Base URL"
                return success_response({
                    "available": False,
                    "message": message
                })
            except Exception as e:
                # Backend logic
                error_msg = str(e)
                logger.warning(f"API key verification failed: {error_msg}")

                # Backend logic
                if "401" in error_msg or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                    message = "API key không hợp lệ hoặc đã hết hạn, Vui lòng kiểm tra trong phần Cài đặt API key Cấu hình"
                elif "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    message = "API vượt quá giới hạn gọi hoặc số dư không đủ, Vui lòng kiểm tra cấu hình trong phần Cài đặt"
                elif "403" in error_msg or "forbidden" in error_msg.lower():
                    message = "API Truy cập bị từ chối, Vui lòng kiểm tra trong phần Cài đặt API key quyền"
                elif "timeout" in error_msg.lower():
                    message = "API quá thời gian gọi, Vui lòng kiểm tra kết nối mạng trong Cài đặt và API Base URL"
                else:
                    message = f"API gọi thất bại, Vui lòng kiểm tra cấu hình trong phần Cài đặt: {error_msg}"

                return success_response({
                    "available": False,
                    "message": message
                })

    except Exception as e:
        logger.error(f"Error verifying API key: {str(e)}")
        return error_response(
            "VERIFY_API_KEY_ERROR",
            f"Xác minh API key gặp lỗi: {str(e)}",
            500,
        )


def _sync_settings_to_config(settings: Settings):
    """Sync Google Gemini settings to Flask app config and clear AI service cache if needed"""
    # Track if AI-related settings changed
    ai_config_changed = False

    # Enforce Google Gemini provider format
    new_format = "gemini"
    old_format = current_app.config.get("AI_PROVIDER_FORMAT")
    if old_format != new_format:
        ai_config_changed = True
        logger.info(f"AI provider format changed: {old_format} -> {new_format}")
    current_app.config["AI_PROVIDER_FORMAT"] = new_format

    env_api_defaults = _provider_api_env_defaults()
    key_config, base_config = _provider_api_config_keys(new_format)
    is_gemini_settings = (settings.ai_provider_format or "gemini").lower() == "gemini"

    target_api_config = dict(env_api_defaults)
    if is_gemini_settings:
        if settings.api_key is not None:
            target_api_config[key_config] = settings.api_key
        if settings.api_base_url is not None:
            target_api_config[base_config] = settings.api_base_url

    for config_key, target_value in target_api_config.items():
        if current_app.config.get(config_key) != target_value:
            ai_config_changed = True
            if config_key.endswith("_API_KEY"):
                logger.info(f"{config_key} updated")
            else:
                logger.info(f"{config_key} changed: {current_app.config.get(config_key)} -> {target_value}")
        current_app.config[config_key] = target_value
    
    # Check model changes
    new_text_model = settings.text_model or Config.TEXT_MODEL
    old_model = current_app.config.get("TEXT_MODEL")
    if old_model != new_text_model:
        ai_config_changed = True
        logger.info(f"Text model changed: {old_model} -> {new_text_model}")
    current_app.config["TEXT_MODEL"] = new_text_model

    new_image_model = settings.image_model or Config.IMAGE_MODEL
    old_model = current_app.config.get("IMAGE_MODEL")
    if old_model != new_image_model:
        ai_config_changed = True
        logger.info(f"Image model changed: {old_model} -> {new_image_model}")
    current_app.config["IMAGE_MODEL"] = new_image_model

    # Sync image generation settings (fall back to Config when NULL)
    current_app.config["DEFAULT_RESOLUTION"] = settings.image_resolution or Config.DEFAULT_RESOLUTION
    current_app.config["DEFAULT_ASPECT_RATIO"] = settings.image_aspect_ratio or Config.DEFAULT_ASPECT_RATIO
    new_quality = getattr(settings, "image_quality", None) or Config.IMAGE_QUALITY
    if current_app.config.get("IMAGE_QUALITY") != new_quality:
        # Image providers are cached per model name, so a quality change must
        # invalidate the cache or generation keeps using the previous tier.
        ai_config_changed = True
        logger.info(f"Image quality changed: {current_app.config.get('IMAGE_QUALITY')} -> {new_quality}")
    current_app.config["IMAGE_QUALITY"] = new_quality

    # Sync worker settings (fall back to Config when NULL)
    current_app.config["MAX_DESCRIPTION_WORKERS"] = settings.max_description_workers or Config.MAX_DESCRIPTION_WORKERS
    current_app.config["MAX_IMAGE_WORKERS"] = settings.max_image_workers or Config.MAX_IMAGE_WORKERS
    from services.task_manager import sync_resource_limits
    sync_resource_limits(
        current_app.config["MAX_DESCRIPTION_WORKERS"],
        current_app.config["MAX_IMAGE_WORKERS"],
    )
    logger.info(f"Updated worker settings: desc={current_app.config['MAX_DESCRIPTION_WORKERS']}, img={current_app.config['MAX_IMAGE_WORKERS']}")

    # Sync MinerU settings (fall back to Config defaults when NULL)
    current_app.config["MINERU_API_BASE"] = settings.mineru_api_base or Config.MINERU_API_BASE
    current_app.config["MINERU_TOKEN"] = settings.mineru_token if settings.mineru_token is not None else Config.MINERU_TOKEN
    current_app.config["IMAGE_CAPTION_MODEL"] = settings.image_caption_model or Config.IMAGE_CAPTION_MODEL
    current_app.config["OUTPUT_LANGUAGE"] = settings.output_language or Config.OUTPUT_LANGUAGE
    
    # Sync reasoning mode settings (separate for text and image)
    # Check if reasoning configuration changed (requires AIService cache clear)
    old_text_reasoning = current_app.config.get("ENABLE_TEXT_REASONING")
    old_text_budget = current_app.config.get("TEXT_THINKING_BUDGET")
    old_image_reasoning = current_app.config.get("ENABLE_IMAGE_REASONING")
    old_image_budget = current_app.config.get("IMAGE_THINKING_BUDGET")
    
    if (old_text_reasoning != settings.enable_text_reasoning or 
        old_text_budget != settings.text_thinking_budget or
        old_image_reasoning != settings.enable_image_reasoning or
        old_image_budget != settings.image_thinking_budget):
        ai_config_changed = True
        logger.info(f"Reasoning config changed: text={old_text_reasoning}({old_text_budget})->{settings.enable_text_reasoning}({settings.text_thinking_budget}), image={old_image_reasoning}({old_image_budget})->{settings.enable_image_reasoning}({settings.image_thinking_budget})")
    
    current_app.config["ENABLE_TEXT_REASONING"] = settings.enable_text_reasoning
    current_app.config["TEXT_MAX_OUTPUT_TOKENS"] = getattr(settings, "text_max_output_tokens", None) or Config.TEXT_MAX_OUTPUT_TOKENS
    current_app.config["TEXT_THINKING_BUDGET"] = settings.text_thinking_budget
    current_app.config["ENABLE_IMAGE_REASONING"] = settings.enable_image_reasoning
    current_app.config["IMAGE_THINKING_BUDGET"] = settings.image_thinking_budget
    current_app.config["ENABLE_IMAGE_QUALITY_CONTROL"] = getattr(settings, "enable_image_quality_control", False)
    
    # Sync Baidu OCR settings (fall back to Config default when NULL)
    current_app.config["BAIDU_API_KEY"] = settings.baidu_api_key or Config.BAIDU_API_KEY

    # Clear legacy non-Google / per-model source and credential keys (Google Gemini only)
    for config_key in (
        "TEXT_MODEL_SOURCE",
        "IMAGE_MODEL_SOURCE",
        "IMAGE_CAPTION_MODEL_SOURCE",
        "TEXT_API_KEY",
        "TEXT_API_BASE",
        "IMAGE_API_KEY",
        "IMAGE_API_BASE",
        "IMAGE_CAPTION_API_KEY",
        "IMAGE_CAPTION_API_BASE",
        "OPENAI_IMAGE_API_PROTOCOL",
    ):
        if config_key in current_app.config:
            ai_config_changed = True
            current_app.config.pop(config_key, None)
    
    # Clear AI service cache if AI-related configuration changed
    if ai_config_changed:
        try:
            from services.ai_service_manager import clear_ai_service_cache
            clear_ai_service_cache()
            logger.warning("AI configuration changed - AIService cache cleared. New providers will be created on next request.")
        except Exception as e:
            logger.error(f"Failed to clear AI service cache: {e}")


def _get_test_image_path() -> Path:
    candidates = [Path(PROJECT_ROOT) / "assets" / "test_img.png"]

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        pyinstaller_root = getattr(sys, "_MEIPASS", None)
        if pyinstaller_root:
            candidates.append(Path(pyinstaller_root) / "assets" / "test_img.png")
        candidates.extend([
            exe_dir / "assets" / "test_img.png",
            exe_dir / "_internal" / "assets" / "test_img.png",
        ])

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError("Không tìm thấy test_img.png, Vui lòng kiểm tra tài nguyên đóng gói hoặc thư mục gốc của dự án assets có tồn tại tệp này")


def _get_baidu_credentials():
    """ Backend docstring """
    api_key = current_app.config.get("BAIDU_API_KEY") or Config.BAIDU_API_KEY
    if not api_key:
        raise ValueError("chưa cấu hình BAIDU_API_KEY")
    return api_key


def _create_file_parser():
    """ Backend docstring """
    google_key = current_app.config.get("IMAGE_CAPTION_API_KEY") or current_app.config.get("GOOGLE_API_KEY", "")
    google_base = current_app.config.get("IMAGE_CAPTION_API_BASE") or current_app.config.get("GOOGLE_API_BASE", "")

    return FileParserService(
        mineru_token=current_app.config.get("MINERU_TOKEN", ""),
        mineru_api_base=current_app.config.get("MINERU_API_BASE", ""),
        google_api_key=google_key,
        google_api_base=google_base,
        openai_api_key="",
        openai_api_base="",
        image_caption_model=current_app.config.get("IMAGE_CAPTION_MODEL", Config.IMAGE_CAPTION_MODEL),
        lazyllm_image_caption_source=None,
        provider_format="gemini",
    )


# Backend logic
def _test_baidu_ocr():
    """ Backend docstring """
    api_key = _get_baidu_credentials()
    provider = create_baidu_accurate_ocr_provider(api_key)
    if not provider:
        raise ValueError("Baidu OCR Provider khởi tạo thất bại")

    test_image_path = _get_test_image_path()
    result = provider.recognize(str(test_image_path), language_type="CHN_ENG")
    recognized_text = provider.get_full_text(result, separator=" ")

    return {
        "recognized_text": recognized_text,
        "words_result_num": result.get("words_result_num", 0),
    }, "Baidu OCR kiểm tra thành công"


def _test_text_model():
    """ Backend docstring """
    from services.ai_providers import get_text_provider, _resolve_setting
    text_model = _resolve_setting("TEXT_MODEL") or current_app.config.get("TEXT_MODEL", Config.TEXT_MODEL)
    provider = get_text_provider(model=text_model)
    enable_reasoning = current_app.config.get("ENABLE_TEXT_REASONING", False)
    budget = current_app.config.get("TEXT_THINKING_BUDGET", 64) if enable_reasoning else 0
    reply = provider.generate_text("Vui lòng chỉ trả lời OK. ", thinking_budget=budget)
    return {"reply": reply.strip()}, "Kiểm tra mô hình văn bản thành công"


def _test_caption_model():
    """ Backend docstring """
    upload_folder = Path(current_app.config.get("UPLOAD_FOLDER", Config.UPLOAD_FOLDER))
    mineru_root = upload_folder / "mineru_files"
    mineru_root.mkdir(parents=True, exist_ok=True)
    extract_id = datetime.now(timezone.utc).strftime("test-%Y%m%d%H%M%S")
    image_dir = mineru_root / extract_id
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / "caption_test.png"

    try:
        test_image_path = _get_test_image_path()
        shutil.copyfile(test_image_path, image_path)

        parser = _create_file_parser()
        image_url = f"/files/mineru/{extract_id}/{image_path.name}"
        caption = parser._generate_single_caption(image_url).strip()

        if not caption:
            raise ValueError("Mô hình nhận diện ảnh trả về kết quả rỗng")

        return {"caption": caption}, "Kiểm tra mô hình nhận diện ảnh thành công"
    finally:
        if image_path.exists():
            image_path.unlink()
        if image_dir.exists():
            try:
                image_dir.rmdir()
            except OSError:
                pass


def _test_baidu_inpaint():
    """ Backend docstring """
    api_key = _get_baidu_credentials()
    provider = create_baidu_inpainting_provider(api_key)
    if not provider:
        raise ValueError("Phục hồi ảnh Baidu Provider khởi tạo thất bại")

    test_image_path = _get_test_image_path()
    with Image.open(test_image_path) as image:
        width, height = image.size
        rect_width = max(1, int(width * 0.3))
        rect_height = max(1, int(height * 0.3))
        left = max(0, int(width * 0.35))
        top = max(0, int(height * 0.35))
        rectangles = [{
            "left": left,
            "top": top,
            "width": min(rect_width, width - left),
            "height": min(rect_height, height - top),
        }]
        result = provider.inpaint(image, rectangles)

    if result is None:
        raise ValueError("Phục hồi ảnh Baidu trả về kết quả rỗng")

    return {"image_size": result.size}, "Kiểm tra phục hồi ảnh Baidu thành công"


def _test_image_model():
    """ Backend docstring """
    ai_service = AIService()
    test_image_path = _get_test_image_path()
    prompt = "Tạo một bức ảnh gọn gàng, sáng, ảnh nền phù hợp cho bài thuyết trình. "
    settings = Settings.get_settings()
    image_model = (current_app.config.get("IMAGE_MODEL", "") or "").lower()
    ref_image_path = None if image_model.startswith("gpt-image-") else str(test_image_path)
    result = ai_service.generate_image(
        prompt=prompt,
        ref_image_path=ref_image_path,
        aspect_ratio=settings.image_aspect_ratio or "16:9",
        resolution=settings.image_resolution or "2K"
    )

    if result is None:
        raise ValueError("Mô hình tạo ảnh trả về kết quả rỗng")

    return {"image_size": result.size}, "Kiểm tra mô hình tạo ảnh thành công"


def _test_mineru_pdf():
    """ Backend docstring """
    mineru_token = current_app.config.get("MINERU_TOKEN", "")
    if not mineru_token:
        raise ValueError("chưa cấu hình MINERU_TOKEN")

    parser = _create_file_parser()
    tmp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_file = Path(tmp.name)
        test_image_path = _get_test_image_path()
        with Image.open(test_image_path) as image:
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(tmp_file, format="PDF")

        batch_id, upload_url, error = parser._get_upload_url("mineru-test.pdf")
        if error:
            raise ValueError(error)

        upload_error = parser._upload_file(str(tmp_file), upload_url)
        if upload_error:
            raise ValueError(upload_error)

        markdown_content, extract_id, poll_error = parser._poll_result(batch_id, max_wait_time=30)
        if poll_error:
            if "timeout" in poll_error.lower():
                return {
                    "batch_id": batch_id,
                    "status": "processing",
                    "message": "dịch vụ hoạt động bình thường, Tệp đang được xử lý"
                }, "MinerU Dịch vụ khả dụng (Đang xử lý) "
            else:
                raise ValueError(poll_error)
        else:
            content_preview = (markdown_content or "").strip()[:120]
            return {
                "batch_id": batch_id,
                "extract_id": extract_id,
                "content_preview": content_preview,
            }, "MinerU Kiểm tra phân tích thành công"
    finally:
        if tmp_file and tmp_file.exists():
            tmp_file.unlink()


# Backend logic
TEST_FUNCTIONS = {
    "baidu-ocr": _test_baidu_ocr,
    "text-model": _test_text_model,
    "caption-model": _test_caption_model,
    "baidu-inpaint": _test_baidu_inpaint,
    "image-model": _test_image_model,
    "mineru-pdf": _test_mineru_pdf,
}


def _is_codex_settings_test(test_name: str, test_settings: dict, error_text: str) -> bool:
    test_source_keys = {
        "text-model": "text_model_source",
        "image-model": "image_model_source",
        "caption-model": "image_caption_model_source",
    }
    source_key = test_source_keys.get(test_name)
    if source_key:
        source = test_settings.get(source_key)
        if source is None:
            source = test_settings.get("ai_provider_format")
        is_codex_test = str(source).lower() == "codex" if source else False
    else:
        is_codex_test = False
    is_codex_endpoint = "chatgpt.com/backend-api/codex" in error_text or "/codex/responses" in error_text
    return is_codex_test or is_codex_endpoint


def _is_codex_oauth_unauthorized(error: Exception, test_name: str, test_settings: dict) -> bool:
    """Return True when a settings test failed because the Codex OAuth token is invalid."""
    response = getattr(error, "response", None)
    status_code = getattr(response, "status_code", None)
    error_text = str(error).lower()
    if not _is_codex_settings_test(test_name, test_settings, error_text):
        return False

    unauthorized = (
        status_code == 401
        or bool(re.search(r"\b401\b", error_text))
        or "unauthorized" in error_text
    )
    oauth_not_connected = (
        "openai oauth is not connected" in error_text
        or "please log in with your openai account" in error_text
    )
    return unauthorized or oauth_not_connected


def _disconnect_expired_openai_oauth() -> None:
    settings = Settings.get_settings()
    settings.clear_openai_oauth()
    db.session.flush()


def _run_test_async(task_id: str, test_name: str, test_settings: dict, app):
    """
    

    Args:
        task_id: ID
        test_name: 
        test_settings: 
        app: Flask app 
    """
    with app.app_context():
        try:
            # Backend logic
            task = Task.query.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return

            task.status = 'PROCESSING'
            db.session.commit()

            # Backend logic
            with temporary_settings_override(test_settings):
                # Backend logic
                test_func = TEST_FUNCTIONS.get(test_name)
                if not test_func:
                    raise ValueError(f"Loại kiểm tra không xác định: {test_name}")

                result_data, message = test_func()

                # Backend logic
                task = Task.query.get(task_id)
                if task:
                    task.status = 'COMPLETED'
                    task.completed_at = datetime.now(timezone.utc)
                    task.set_progress({
                        'result': result_data,
                        'message': message
                    })
                    db.session.commit()
                    logger.info(f"Test task {task_id} completed successfully")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Test task {task_id} failed: {error_msg}", exc_info=True)
            task = Task.query.get(task_id)
            if task:
                progress = {}
                if _is_codex_oauth_unauthorized(e, test_name, test_settings):
                    _disconnect_expired_openai_oauth()
                    error_msg = "Codex Phiên đăng nhập đã hết hạn hoặc không hợp lệ, đã ngắt kết nối OpenAI kết nối tài khoản. vui lòng đăng nhập lại OpenAI rồi kiểm tra lại. "
                    progress = {
                        "openai_oauth_disconnected": True,
                        "message": error_msg,
                    }
                    logger.info("OpenAI OAuth disconnected after Codex settings test reported invalid credentials")

                task.status = 'FAILED'
                task.error_message = error_msg
                task.set_progress(progress)
                task.completed_at = datetime.now(timezone.utc)
                db.session.commit()



@settings_bp.route("/tests/<test_name>", methods=["POST"], strict_slashes=False)
def run_settings_test(test_name: str):
    """
    POST /api/settings/tests/<test_name> - 

    Request Body (optional):
        , 
        {
            "api_key": "test-key",
            "api_base_url": "https://test.api.com",
            "text_model": "test-model",
            ...
        }

    Returns:
        {
            "data": {
                "task_id": "uuid",
                "status": "PENDING"
            }
        }
    """
    try:
        # Backend logic
        global_settings = Settings.get_settings()

        # Backend logic
        is_gemini_settings = (global_settings.ai_provider_format or "gemini").lower() == "gemini"
        test_settings = {
            "ai_provider_format": "gemini",
        }
        if is_gemini_settings:
            if global_settings.api_key:
                test_settings["api_key"] = global_settings.api_key
            if global_settings.api_base_url:
                test_settings["api_base_url"] = global_settings.api_base_url
        if global_settings.text_model:
            test_settings["text_model"] = global_settings.text_model
        if global_settings.image_model:
            test_settings["image_model"] = global_settings.image_model
        if global_settings.image_caption_model:
            test_settings["image_caption_model"] = global_settings.image_caption_model
        if global_settings.mineru_api_base:
            test_settings["mineru_api_base"] = global_settings.mineru_api_base
        if global_settings.mineru_token:
            test_settings["mineru_token"] = global_settings.mineru_token
        if global_settings.baidu_api_key:
            test_settings["baidu_api_key"] = global_settings.baidu_api_key
        if global_settings.image_resolution:
            test_settings["image_resolution"] = global_settings.image_resolution
        test_settings["image_quality"] = (
            global_settings.image_quality
            or current_app.config.get('IMAGE_QUALITY')
            or 'auto'
        )
        # Backend logic
        test_settings["enable_text_reasoning"] = global_settings.enable_text_reasoning
        test_settings["text_max_output_tokens"] = global_settings.text_max_output_tokens or Config.TEXT_MAX_OUTPUT_TOKENS
        test_settings["text_thinking_budget"] = global_settings.text_thinking_budget
        test_settings["enable_image_reasoning"] = global_settings.enable_image_reasoning
        test_settings["image_thinking_budget"] = global_settings.image_thinking_budget

        # Backend logic
        override_settings = request.get_json() or {}
        if override_settings:
            logger.info(f"Applying test setting overrides: {list(override_settings.keys())}")
            test_settings.update(override_settings)
        test_settings["ai_provider_format"] = "gemini"

        # Backend logic
        task = Task(
            project_id='settings-test',  # Backend logic
            task_type=f'TEST_{test_name.upper().replace("-", "_")}',
            status='PENDING'
        )
        db.session.add(task)
        db.session.commit()

        task_id = task.id

        # Backend logic
        task_manager.submit_task(
            task_id,
            _run_test_async,
            test_name,
            test_settings,
            current_app._get_current_object()
        )

        logger.info(f"Started test task {task_id} for {test_name}")

        return success_response({
            'task_id': task_id,
            'status': 'PENDING'
        }, 'Tác vụ kiểm tra đã được khởi chạy')

    except Exception as e:
        logger.error(f"Failed to start test: {str(e)}", exc_info=True)
        return error_response(
            "SETTINGS_TEST_ERROR",
            f"Khởi chạy kiểm tra thất bại: {str(e)}",
            500
        )


@settings_bp.route("/tests/<task_id>/status", methods=["GET"], strict_slashes=False)
def get_test_status(task_id: str):
    """
    GET /api/settings/tests/<task_id>/status - 

    Returns:
        {
            "data": {
                "status": "PENDING|PROCESSING|COMPLETED|FAILED",
                "result": {...},  # Backend logic
                "error": "...",   # Backend logic
                "message": "..."
            }
        }
    """
    try:
        task = Task.query.get(task_id)
        if not task:
            return error_response("TASK_NOT_FOUND", "Tác vụ kiểm tra không tồn tại", 404)

        # Backend logic
        from services.task_watchdog import reconcile_task_for_response
        reconcile_task_for_response(task)

        # Backend logic
        response_data = {
            'status': task.status,
            'task_type': task.task_type,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        }

        # Backend logic
        if task.status == 'COMPLETED':
            progress = task.get_progress()
            response_data['result'] = progress.get('result', {})
            response_data['message'] = progress.get('message', 'Kiểm tra hoàn tất')

        # Backend logic
        elif task.status == 'FAILED':
            progress = task.get_progress()
            from services.task_watchdog import localize_watchdog_payload
            localized = localize_watchdog_payload({
                'error_message': task.error_message,
                'progress': dict(progress or {}),
            })
            response_data['error'] = localized['error_message']
            progress = localized['progress']
            if progress:
                response_data.update(progress)

        return success_response(response_data)

    except Exception as e:
        logger.error(f"Failed to get test status: {str(e)}", exc_info=True)
        return error_response(
            "GET_TEST_STATUS_ERROR",
            f"Lấy trạng thái kiểm tra thất bại: {str(e)}",
            500
        )