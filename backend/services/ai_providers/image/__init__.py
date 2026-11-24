"""Image generation providers"""
import importlib

from .base import ImageProvider

_LAZY_IMAGE_EXPORTS = {
    'GenAIImageProvider': '.genai_provider',
    'OpenAIImageProvider': '.openai_provider',
    'AnthropicImageProvider': '.anthropic_provider',
    'BaiduInpaintingProvider': '.baidu_inpainting_provider',
    'create_baidu_inpainting_provider': '.baidu_inpainting_provider',
    'LazyLLMImageProvider': '.lazyllm_provider',
    'CodexImageProvider': '.codex_provider',
    'SubjectExtractionProvider': '.subject_extraction_provider',
    'RmbgSegmentationProvider': '.rmbg_segmentation_provider',
    'create_rmbg_segmentation_provider': '.rmbg_segmentation_provider',
}

__all__ = [
    'ImageProvider',
    'GenAIImageProvider',
    'OpenAIImageProvider',
    'AnthropicImageProvider',
    'BaiduInpaintingProvider',
    'create_baidu_inpainting_provider',
    'LazyLLMImageProvider',
    'CodexImageProvider',
    'SubjectExtractionProvider',
    'RmbgSegmentationProvider',
    'create_rmbg_segmentation_provider',
]


def __getattr__(name: str):
    """Lazily import concrete image provider classes and helpers on first access."""
    module_name = _LAZY_IMAGE_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
