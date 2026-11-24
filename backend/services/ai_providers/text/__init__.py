"""Text generation providers"""
import importlib

from .base import TextProvider, strip_think_tags

_LAZY_TEXT_EXPORTS = {
    'GenAITextProvider': '.genai_provider',
    'OpenAITextProvider': '.openai_provider',
    'AnthropicTextProvider': '.anthropic_provider',
    'LazyLLMTextProvider': '.lazyllm_provider',
    'CodexTextProvider': '.codex_provider',
}

__all__ = ['TextProvider', 'GenAITextProvider', 'OpenAITextProvider', 'AnthropicTextProvider', 'LazyLLMTextProvider', 'CodexTextProvider', 'strip_think_tags']


def __getattr__(name: str):
    """Lazily import concrete text provider classes on first access."""
    module_name = _LAZY_TEXT_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
