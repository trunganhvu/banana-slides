"""
Backend configuration file
"""
import os
import sys
from datetime import timedelta

# Backend logic
# Backend logic
_current_file = os.path.realpath(__file__)  # Backend logic
BASE_DIR = os.path.dirname(_current_file)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DEFAULT_FRONTEND_PORT = 3011
DEFAULT_BACKEND_PORT = 5011

# Backend logic
class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    
    # Backend logic
    # Use absolute path to avoid WSL path issues
    db_path = os.path.join(BASE_DIR, 'instance', 'database.db')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f'sqlite:///{db_path}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Backend logic
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False,  # Backend logic
            'timeout': 30  # Backend logic
        },
        'pool_pre_ping': True,  # Backend logic
        'pool_recycle': 3600,  # Backend logic
    }
    
    # Backend logic
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_REFERENCE_FILE_EXTENSIONS = {'pdf', 'docx', 'pptx', 'doc', 'ppt', 'xlsx', 'xls', 'csv', 'txt', 'md'}
    
    # Backend logic
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GOOGLE_API_BASE = os.getenv('GOOGLE_API_BASE') or ''
    
    # Provider format: gemini | openai | volcengine | vertex | lazyllm
    AI_PROVIDER_FORMAT = os.getenv('AI_PROVIDER_FORMAT', 'gemini')

    # Google Cloud Vertex AI (requires AI_PROVIDER_FORMAT=vertex)
    VERTEX_PROJECT_ID = os.getenv('VERTEX_PROJECT_ID', '')
    VERTEX_LOCATION = os.getenv('VERTEX_LOCATION', 'us-central1')
    
    # Backend logic
    GENAI_TIMEOUT = float(os.getenv('GENAI_TIMEOUT', '300.0'))  # Backend logic
    GENAI_MAX_RETRIES = int(os.getenv('GENAI_MAX_RETRIES', '2'))  # Backend logic
    
    # Backend logic
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')  # Backend logic
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE') or 'https://api.inferera.com/v1'
    OPENAI_TIMEOUT = float(os.getenv('OPENAI_TIMEOUT', '480.0'))  # Backend logic
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', '2'))  # Backend logic

    # Global output limit for text and image-understanding responses.
    TEXT_MAX_OUTPUT_TOKENS = int(os.getenv("TEXT_MAX_OUTPUT_TOKENS", os.getenv("ANTHROPIC_MAX_TOKENS", "32768")))

    # Backend logic
    VOLCENGINE_API_KEY = os.getenv('VOLCENGINE_API_KEY', '') or os.getenv('ARK_API_KEY', '')
    VOLCENGINE_API_BASE = os.getenv('VOLCENGINE_API_BASE') or 'https://ark.cn-beijing.volces.com/api/plan/v3'

    # Backend logic
    # Backend logic
    # Backend logic
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '') or os.getenv('ANTHROPIC_AUTH_TOKEN', '')
    ANTHROPIC_API_BASE = os.getenv('ANTHROPIC_API_BASE', '') or os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
    ANTHROPIC_VERSION = os.getenv('ANTHROPIC_VERSION', '2023-06-01')
    ANTHROPIC_MAX_TOKENS = TEXT_MAX_OUTPUT_TOKENS  # legacy alias

    # Backend logic
    TEXT_MODEL_SOURCE = os.getenv('TEXT_MODEL_SOURCE', '')                   # Backend logic
    IMAGE_MODEL_SOURCE = os.getenv('IMAGE_MODEL_SOURCE', '')                   # Backend logic
    IMAGE_CAPTION_MODEL_SOURCE = os.getenv('IMAGE_CAPTION_MODEL_SOURCE', '')   # Backend logic

    # Backend logic
    # Backend logic
    TEXT_API_KEY = os.getenv('TEXT_API_KEY', '')
    TEXT_API_BASE = os.getenv('TEXT_API_BASE', '')
    # Backend logic
    IMAGE_API_KEY = os.getenv('IMAGE_API_KEY', '')
    IMAGE_API_BASE = os.getenv('IMAGE_API_BASE', '')
    # Backend logic
    IMAGE_CAPTION_API_KEY = os.getenv('IMAGE_CAPTION_API_KEY', '')
    IMAGE_CAPTION_API_BASE = os.getenv('IMAGE_CAPTION_API_BASE', '')
    
    # Backend logic
    TEXT_MODEL = os.getenv('TEXT_MODEL', 'gemini-3-flash-preview')
    IMAGE_MODEL = os.getenv('IMAGE_MODEL', 'gemini-3-pro-image-preview')

    # Backend logic
    MINERU_TOKEN = os.getenv('MINERU_TOKEN', '')
    MINERU_API_BASE = os.getenv('MINERU_API_BASE', 'https://mineru.net')
    
    # Backend logic
    IMAGE_CAPTION_MODEL = os.getenv('IMAGE_CAPTION_MODEL', 'gemini-3-flash-preview')
    
    # Backend logic
    MAX_DESCRIPTION_WORKERS = int(os.getenv('MAX_DESCRIPTION_WORKERS', '20'))
    MAX_IMAGE_WORKERS = int(os.getenv('MAX_IMAGE_WORKERS', '20'))
    
    # Backend logic
    DEFAULT_ASPECT_RATIO = "16:9"
    DEFAULT_RESOLUTION = "2K"
    # Backend logic
    # Backend logic
    IMAGE_QUALITY = os.getenv('IMAGE_QUALITY', 'auto')
    
    # Backend logic
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    WERKZEUG_LOG_LEVEL = (os.getenv('WERKZEUG_LOG_LEVEL') or 'INFO').strip().upper()
    
    # Backend logic
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', f'http://localhost:{DEFAULT_FRONTEND_PORT}').split(',')
    
    # Backend logic
    # Backend logic
    OUTPUT_LANGUAGE = os.getenv('OUTPUT_LANGUAGE', 'vi')
    
    # Backend logic
    VOLCENGINE_ACCESS_KEY = os.getenv('VOLCENGINE_ACCESS_KEY', '')
    VOLCENGINE_SECRET_KEY = os.getenv('VOLCENGINE_SECRET_KEY', '')
    VOLCENGINE_INPAINTING_TIMEOUT = int(os.getenv('VOLCENGINE_INPAINTING_TIMEOUT', '60'))  # Backend logic
    VOLCENGINE_INPAINTING_MAX_RETRIES = int(os.getenv('VOLCENGINE_INPAINTING_MAX_RETRIES', '3'))  # Backend logic

    # Backend logic
    # Backend logic
    # Backend logic
    INPAINTING_PROVIDER = os.getenv('INPAINTING_PROVIDER', 'gemini')  # Backend logic

    # Backend logic
    BAIDU_API_KEY = os.getenv('BAIDU_API_KEY', '') or os.getenv('BAIDU_OCR_API_KEY', '')

    # Backend logic
    TTS_DEFAULT_VOICE_ZH = os.getenv('TTS_DEFAULT_VOICE_ZH', 'vi-VN-HoaiMyNeural')
    TTS_DEFAULT_VOICE_VI = os.getenv('TTS_DEFAULT_VOICE_VI', 'vi-VN-HoaiMyNeural')
    TTS_DEFAULT_VOICE_EN = os.getenv('TTS_DEFAULT_VOICE_EN', 'en-US-JennyNeural')
    TTS_DEFAULT_VOICE_JA = os.getenv('TTS_DEFAULT_VOICE_JA', 'ja-JP-NanamiNeural')
    TTS_DEFAULT_RATE = os.getenv('TTS_DEFAULT_RATE', '+0%')
    VIDEO_OUTPUT_WIDTH = int(os.getenv('VIDEO_OUTPUT_WIDTH', '1920'))
    VIDEO_OUTPUT_HEIGHT = int(os.getenv('VIDEO_OUTPUT_HEIGHT', '1080'))
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', '25'))
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
    DEFAULT_SILENT_CLIP_DURATION = float(os.getenv('DEFAULT_SILENT_CLIP_DURATION', '3.0'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Backend logic
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)