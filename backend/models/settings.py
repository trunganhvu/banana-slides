"""Settings model"""
import json
from datetime import datetime, timezone
from . import db
from config import is_placeholder_api_key


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Settings(db.Model):
    """
    Settings model - stores global application settings
    """
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True, default=1)
    ai_provider_format = db.Column(db.String(20), nullable=True)   # Backend logic
    api_base_url = db.Column(db.String(500), nullable=True)        # Backend logic
    api_key = db.Column(db.String(500), nullable=True)             # Backend logic
    image_resolution = db.Column(db.String(20), nullable=True)     # Backend logic
    image_aspect_ratio = db.Column(db.String(10), nullable=True)   # Backend logic
    image_quality = db.Column(db.String(10), nullable=True)        # Backend logic
    max_description_workers = db.Column(db.Integer, nullable=True)  # Backend logic
    max_image_workers = db.Column(db.Integer, nullable=True)        # Backend logic

    # Backend logic
    text_model = db.Column(db.String(100), nullable=True)  # Backend logic
    image_model = db.Column(db.String(100), nullable=True)  # Backend logic
    mineru_api_base = db.Column(db.String(255), nullable=True)  # Backend logic
    mineru_token = db.Column(db.String(500), nullable=True)  # Backend logic
    image_caption_model = db.Column(db.String(100), nullable=True)  # Backend logic
    output_language = db.Column(db.String(10), nullable=True)  # Backend logic
    
    # Backend logic
    enable_text_reasoning = db.Column(db.Boolean, nullable=False, default=False)  # Backend logic
    text_max_output_tokens = db.Column(db.Integer, nullable=True)  # NULL = environment/default 32768
    text_thinking_budget = db.Column(db.Integer, nullable=False, default=1024)  # Backend logic
    enable_image_reasoning = db.Column(db.Boolean, nullable=False, default=False)  # Backend logic
    image_thinking_budget = db.Column(db.Integer, nullable=False, default=1024)  # Backend logic
    enable_image_quality_control = db.Column(db.Boolean, nullable=False, default=False)  # Backend logic
    
    # Backend logic
    description_generation_mode = db.Column(db.String(20), nullable=True)

    # Backend logic
    description_extra_fields = db.Column(db.Text, nullable=True)
    image_prompt_extra_fields = db.Column(db.Text, nullable=True)  # Backend logic

    # Backend logic
    baidu_api_key = db.Column(db.String(500), nullable=True)  # Backend logic

    # Backend logic
    elevenlabs_enabled = db.Column(db.Boolean, nullable=False, default=False)
    elevenlabs_api_key = db.Column(db.String(500), nullable=True)
    elevenlabs_voice_id = db.Column(db.String(100), nullable=True)

    # Backend logic
    text_model_source = db.Column(db.String(50), nullable=True)           # Backend logic
    image_model_source = db.Column(db.String(50), nullable=True)          # Backend logic
    image_caption_model_source = db.Column(db.String(50), nullable=True)  # Backend logic
    lazyllm_api_keys = db.Column(db.Text, nullable=True)                  # JSON: {"qwen": "key1", "doubao": "key2", ...}

    # Backend logic
    text_api_key = db.Column(db.String(500), nullable=True)
    text_api_base_url = db.Column(db.String(500), nullable=True)
    image_api_key = db.Column(db.String(500), nullable=True)
    image_api_base_url = db.Column(db.String(500), nullable=True)
    image_caption_api_key = db.Column(db.String(500), nullable=True)
    image_caption_api_base_url = db.Column(db.String(500), nullable=True)

    # OpenAI image API protocol: auto (default), images (force images.generate), chat (force chat.completions)
    openai_image_api_protocol = db.Column(db.String(10), nullable=True)

    # OpenAI Codex OAuth credentials
    openai_oauth_access_token = db.Column(db.Text, nullable=True)
    openai_oauth_refresh_token = db.Column(db.Text, nullable=True)
    openai_oauth_expires_at = db.Column(db.DateTime, nullable=True)
    openai_oauth_account_id = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def _val(self, attr, defaults):
        """Return DB value, falling back to .env default when None."""
        v = getattr(self, attr)
        return v if v is not None else defaults.get(attr)

    # Backend logic
    DEFAULT_EXTRA_FIELDS = ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình']
    DEFAULT_IMAGE_PROMPT_FIELDS = ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm']  # Backend logic

    # Mapping legacy and multilingual field names to canonical Vietnamese names
    LEGACY_FIELD_EQUIV = {
        '\u914d\u56fe\u4e0e\u7d20\u6750': 'Hình ảnh & Tư liệu',
        '\u7248\u5f0f\u4e0e\u91cd\u70b9': 'Bố cục & Trọng tâm',
        '\u6f14\u8bb2\u8005\u5907\u6ce8': 'Ghi chú thuyết trình',
        '\u89c6\u89c9\u5143\u7d20': 'Hình ảnh & Tư liệu',
        '\u89c6\u89c9\u7126\u70b9': 'Bố cục & Trọng tâm',
        '\u6392\u7248\u5e03\u5c40': 'Bố cục & Trọng tâm',
        '\u6392\u7248\u5efa\u8bae': 'Bố cục & Trọng tâm',
        'Images & Materials': 'Hình ảnh & Tư liệu',
        'Layout & Focus': 'Bố cục & Trọng tâm',
        'Speaker Notes': 'Ghi chú thuyết trình',
        'Yếu tố thị giác': 'Hình ảnh & Tư liệu',
        'Tiêu điểm thị giác': 'Bố cục & Trọng tâm',
        'Bố cục trình bày': 'Bố cục & Trọng tâm',
        'Gợi ý bố cục': 'Bố cục & Trọng tâm',
    }

    def get_description_extra_fields(self):
        """Return parsed extra fields list."""
        if self.description_extra_fields:
            try:
                fields = json.loads(self.description_extra_fields)
                if isinstance(fields, list):
                    return fields
            except (json.JSONDecodeError, TypeError):
                pass
        return list(self.DEFAULT_EXTRA_FIELDS)

    def get_image_prompt_extra_fields(self):
        """Return parsed list of extra fields to include in image prompts."""
        if self.image_prompt_extra_fields:
            try:
                fields = json.loads(self.image_prompt_extra_fields)
                if isinstance(fields, list):
                    return fields
            except (json.JSONDecodeError, TypeError):
                pass
        return list(self.DEFAULT_IMAGE_PROMPT_FIELDS)

    def to_dict(self):
        """Convert to dictionary, merging .env defaults for None fields."""
        d = Settings._get_config_defaults()
        effective_provider = self._val('ai_provider_format', d)
        provider_defaults = Settings._get_api_defaults_for_provider(effective_provider)
        api_base_url = self.api_base_url if self.api_base_url is not None else provider_defaults['api_base_url']
        api_key = self.api_key if self.api_key is not None else provider_defaults['api_key']
        mineru_token = self._val('mineru_token', d)
        baidu_api_key = self._val('baidu_api_key', d)
        elevenlabs_api_key = self._val('elevenlabs_api_key', d)
        text_model_source = self._val('text_model_source', d)
        image_model_source = self._val('image_model_source', d)
        image_caption_model_source = self._val('image_caption_model_source', d)
        text_api_defaults = Settings._get_api_defaults_for_provider(text_model_source, 'TEXT')
        image_api_defaults = Settings._get_api_defaults_for_provider(image_model_source, 'IMAGE')
        image_caption_api_defaults = Settings._get_api_defaults_for_provider(
            image_caption_model_source, 'IMAGE_CAPTION'
        )
        text_api_key = self.text_api_key if self.text_api_key is not None else text_api_defaults['api_key']
        image_api_key = self.image_api_key if self.image_api_key is not None else image_api_defaults['api_key']
        image_caption_api_key = (
            self.image_caption_api_key
            if self.image_caption_api_key is not None
            else image_caption_api_defaults['api_key']
        )
        text_api_base_url = (
            self.text_api_base_url
            if self.text_api_base_url is not None
            else text_api_defaults['api_base_url']
        )
        image_api_base_url = (
            self.image_api_base_url
            if self.image_api_base_url is not None
            else image_api_defaults['api_base_url']
        )
        image_caption_api_base_url = (
            self.image_caption_api_base_url
            if self.image_caption_api_base_url is not None
            else image_caption_api_defaults['api_base_url']
        )
        def _key_len(k):
            return len(k) if k and not is_placeholder_api_key(k) else 0

        return {
            'id': self.id,
            'ai_provider_format': effective_provider,
            'api_base_url': api_base_url,
            'raw_api_base_url': self.api_base_url,
            'raw_text_api_base_url': self.text_api_base_url,
            'raw_image_api_base_url': self.image_api_base_url,
            'raw_image_caption_api_base_url': self.image_caption_api_base_url,
            'api_key_length': _key_len(api_key),
            'image_resolution': self._val('image_resolution', d),
            'image_aspect_ratio': self._val('image_aspect_ratio', d),
            'image_quality': self._val('image_quality', d) or 'auto',
            'max_description_workers': self._val('max_description_workers', d),
            'max_image_workers': self._val('max_image_workers', d),
            'text_model': self._val('text_model', d),
            'image_model': self._val('image_model', d),
            'mineru_api_base': self._val('mineru_api_base', d),
            'mineru_token_length': len(mineru_token) if mineru_token else 0,
            'image_caption_model': self._val('image_caption_model', d),
            'output_language': self._val('output_language', d),
            'description_generation_mode': self._val('description_generation_mode', d) or 'streaming',
            'description_extra_fields': self.get_description_extra_fields(),
            'image_prompt_extra_fields': self.get_image_prompt_extra_fields(),
            'enable_text_reasoning': self.enable_text_reasoning,
            'text_max_output_tokens': self._val('text_max_output_tokens', d),
            'text_thinking_budget': self.text_thinking_budget,
            'enable_image_reasoning': self.enable_image_reasoning,
            'image_thinking_budget': self.image_thinking_budget,
            'enable_image_quality_control': self.enable_image_quality_control,
            'baidu_api_key_length': _key_len(baidu_api_key),
            'text_model_source': text_model_source,
            'image_model_source': image_model_source,
            'image_caption_model_source': image_caption_model_source,
            'lazyllm_api_keys_info': self._get_lazyllm_api_keys_info(self._val('lazyllm_api_keys', d)),
            'text_api_key_length': _key_len(text_api_key),
            'text_api_base_url': text_api_base_url,
            'image_api_key_length': _key_len(image_api_key),
            'image_api_base_url': image_api_base_url,
            'image_caption_api_key_length': _key_len(image_caption_api_key),
            'image_caption_api_base_url': image_caption_api_base_url,
            'openai_image_api_protocol': self._val('openai_image_api_protocol', d) or 'auto',
            'elevenlabs_enabled': self.elevenlabs_enabled,
            'elevenlabs_api_key_length': _key_len(elevenlabs_api_key),
            'elevenlabs_voice_id': self.elevenlabs_voice_id or '',
            'openai_oauth_connected': self.is_openai_oauth_connected(),
            'openai_oauth_account_id': self.openai_oauth_account_id if self.is_openai_oauth_connected() else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def _get_api_defaults_for_provider(provider, prefix=None):
        """Return API defaults for an explicit provider/source selection."""
        from config import Config

        provider = (provider or '').lower()
        if not provider:
            return {
                'api_base_url': None,
                'api_key': None,
            }
        specific_key = getattr(Config, f'{prefix}_API_KEY', None) if prefix else None
        specific_base = getattr(Config, f'{prefix}_API_BASE', None) if prefix else None
        if provider == 'gemini':
            return {
                'api_base_url': specific_base or Config.GOOGLE_API_BASE or None,
                'api_key': specific_key or Config.GOOGLE_API_KEY or None,
            }
        if provider == 'openai':
            return {
                'api_base_url': specific_base or Config.OPENAI_API_BASE or None,
                'api_key': specific_key or Config.OPENAI_API_KEY or None,
            }
        if provider == 'volcengine':
            return {
                'api_base_url': specific_base or Config.VOLCENGINE_API_BASE or None,
                'api_key': specific_key or Config.VOLCENGINE_API_KEY or None,
            }
        if provider == 'lazyllm':
            return {
                'api_base_url': None,
                'api_key': None,
            }
        return {
            'api_base_url': None,
            'api_key': None,
        }

    def _get_lazyllm_api_keys_info(self, raw=None):
        """Return vendor names and key lengths (no plaintext) for frontend display."""
        data = raw if raw is not None else self.lazyllm_api_keys
        if not data:
            return {}
        try:
            keys = json.loads(data)
            return {vendor: len(key) for vendor, key in keys.items() if key and not is_placeholder_api_key(key)}
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_lazyllm_api_keys_dict(self):
        """Parse lazyllm_api_keys JSON into a dict."""
        if not self.lazyllm_api_keys:
            return {}
        try:
            return json.loads(self.lazyllm_api_keys)
        except (json.JSONDecodeError, TypeError):
            return {}

    def get_openai_oauth_token(self):
        """Return a valid OAuth access token, or None if not connected / expired without refresh."""
        if not self.openai_oauth_access_token:
            return None
        if self.openai_oauth_expires_at:
            now = _utcnow_naive()
            if self.openai_oauth_expires_at < now:
                if self.openai_oauth_refresh_token:
                    return self._refresh_openai_oauth()
                return None
        return self.openai_oauth_access_token

    def is_openai_oauth_connected(self):
        """Return whether stored OpenAI OAuth credentials can still be presented as connected."""
        if not self.openai_oauth_access_token:
            return False
        if self.openai_oauth_expires_at:
            now = _utcnow_naive()
            if self.openai_oauth_expires_at < now and not self.openai_oauth_refresh_token:
                return False
        return True

    def clear_openai_oauth(self):
        """Clear stored OpenAI OAuth credentials."""
        self.openai_oauth_access_token = None
        self.openai_oauth_refresh_token = None
        self.openai_oauth_expires_at = None
        self.openai_oauth_account_id = None

    def _refresh_openai_oauth(self):
        """Refresh the OpenAI OAuth token using the refresh token."""
        import requests
        from urllib.parse import urlencode
        try:
            resp = requests.post('https://auth.openai.com/oauth/token',
                data=urlencode({
                    'grant_type': 'refresh_token',
                    'refresh_token': self.openai_oauth_refresh_token,
                    'client_id': 'app_EMoamEEZ73f0CkXaXp7hrann',
                }),
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            self.openai_oauth_access_token = data['access_token']
            if 'refresh_token' in data:
                self.openai_oauth_refresh_token = data['refresh_token']
            expires_in = data.get('expires_in', 3600)
            from datetime import timedelta
            self.openai_oauth_expires_at = _utcnow_naive() + timedelta(seconds=expires_in)
            db.session.commit()
            return self.openai_oauth_access_token
        except requests.exceptions.HTTPError as exc:
            status_code = getattr(getattr(exc, 'response', None), 'status_code', None)
            if status_code in (400, 401):
                self.clear_openai_oauth()
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            return None
        except Exception:
            return None

    @staticmethod
    def _get_config_defaults():
        """Return a dict of default values from Config/env for settings fields."""
        from config import Config
        from services.ai_providers.lazyllm_env import collect_env_lazyllm_api_keys

        provider = (Config.AI_PROVIDER_FORMAT or '').lower()
        if provider == 'openai':
            api_base = Config.OPENAI_API_BASE or None
            api_key = Config.OPENAI_API_KEY or None
        elif provider == 'volcengine':
            api_base = Config.VOLCENGINE_API_BASE or None
            api_key = Config.VOLCENGINE_API_KEY or None
        elif provider == 'lazyllm':
            api_base = None
            api_key = None
        else:
            api_base = Config.GOOGLE_API_BASE or None
            api_key = Config.GOOGLE_API_KEY or None

        return {
            'ai_provider_format': Config.AI_PROVIDER_FORMAT,
            'api_base_url': api_base,
            'api_key': api_key,
            'image_resolution': Config.DEFAULT_RESOLUTION,
            'image_aspect_ratio': Config.DEFAULT_ASPECT_RATIO,
            'image_quality': Config.IMAGE_QUALITY,
            'max_description_workers': Config.MAX_DESCRIPTION_WORKERS,
            'max_image_workers': Config.MAX_IMAGE_WORKERS,
            'text_max_output_tokens': Config.TEXT_MAX_OUTPUT_TOKENS,
            'text_model': Config.TEXT_MODEL,
            'image_model': Config.IMAGE_MODEL,
            'mineru_api_base': Config.MINERU_API_BASE,
            'mineru_token': Config.MINERU_TOKEN,
            'image_caption_model': Config.IMAGE_CAPTION_MODEL,
            'output_language': Config.OUTPUT_LANGUAGE,
            'baidu_api_key': Config.BAIDU_API_KEY or None,
            'text_model_source': getattr(Config, 'TEXT_MODEL_SOURCE', None),
            'image_model_source': getattr(Config, 'IMAGE_MODEL_SOURCE', None),
            'image_caption_model_source': getattr(Config, 'IMAGE_CAPTION_MODEL_SOURCE', None),
            'lazyllm_api_keys': collect_env_lazyllm_api_keys(),
        }

    @staticmethod
    def get_settings():
        """
        Get or create the single settings instance.

        Returns the ORM object as-is from the database.  ``.env``
        defaults for ``None`` fields are merged only at serialisation
        time in ``to_dict()``, so this method has no write side-effects.
        """
        settings = Settings.query.first()

        if settings is None:
            settings = Settings(id=1)
            db.session.add(settings)
            db.session.commit()

        return settings

    def __repr__(self):
        return f'<Settings id={self.id}>'