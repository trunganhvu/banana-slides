"""Services package"""
import importlib

from .ai_service import AIService, ProjectContext
from .file_service import FileService

__all__ = ['AIService', 'ProjectContext', 'FileService', 'ExportService']


def __getattr__(name: str):
    """Lazily import ExportService so heavy export deps load only when exporting."""
    if name == 'ExportService':
        module = importlib.import_module('.export_service', __name__)
        value = module.ExportService
        globals()['ExportService'] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

