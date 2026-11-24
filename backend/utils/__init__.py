"""Utils package"""
import importlib

from .response import (
    success_response, 
    error_response, 
    bad_request, 
    not_found, 
    invalid_status,
    ai_service_error,
    rate_limit_error
)
from .validators import validate_project_status, validate_page_status, allowed_file
from .path_utils import convert_mineru_path_to_local, find_mineru_file_with_prefix, find_file_with_prefix
from .page_utils import parse_page_ids_from_query, parse_page_ids_from_body, get_filtered_pages

__all__ = [
    'success_response',
    'error_response',
    'bad_request',
    'not_found',
    'invalid_status',
    'ai_service_error',
    'rate_limit_error',
    'validate_project_status',
    'validate_page_status',
    'allowed_file',
    'convert_mineru_path_to_local',
    'find_mineru_file_with_prefix',
    'find_file_with_prefix',
    'PPTXBuilder',
    'parse_page_ids_from_query',
    'parse_page_ids_from_body',
    'get_filtered_pages'
]


def __getattr__(name: str):
    """Lazily import PPTXBuilder to avoid loading python-pptx at app startup."""
    if name == 'PPTXBuilder':
        module = importlib.import_module('.pptx_builder', __name__)
        value = module.PPTXBuilder
        globals()['PPTXBuilder'] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

