"""
Utilities for building concise, human-friendly export filenames.
"""
import re
import unicodedata
from typing import Any, Iterable, Optional

from werkzeug.utils import secure_filename

GENERIC_SLIDE_TITLE_RE = re.compile(r'^(?:page|slide|trang)\s*\d+$', re.IGNORECASE)
SLIDE_PREFIX_RE = re.compile(r'^(?:trang|page|slide)\s*\d+\s*[:\-–.]?\s*', re.IGNORECASE)


def slugify_filename(
    text: Optional[str],
    max_length: int = 48,
    default: str = 'presentation',
) -> str:
    """Convert arbitrary title text into a concise, ASCII, URL-safe kebab-case slug."""
    raw = str(text or '').strip()
    if raw:
        raw = raw.lstrip('#*- \t\r\n"\'“”‘’')
        raw = SLIDE_PREFIX_RE.sub('', raw).strip().strip('"\'“”‘’')

    if not raw:
        return default

    # Transliterate Vietnamese d/D before NFKD combining mark removal
    raw = raw.replace('đ', 'd').replace('Đ', 'D')
    normalized = unicodedata.normalize('NFKD', raw)
    ascii_text = ''.join(
        ch for ch in normalized
        if unicodedata.category(ch) != 'Mn'
    ).lower()

    slug = re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')
    if not slug:
        return default

    if max_length > 0 and len(slug) > max_length:
        cut = slug[:max_length]
        last_dash = cut.rfind('-')
        if last_dash >= max_length // 2:
            cut = cut[:last_dash]
        slug = cut.strip('-')

    return slug or default


def _extract_first_page_title(pages: Optional[Iterable[Any]]) -> str:
    if not pages:
        return ''
    sorted_pages = sorted(pages, key=lambda p: getattr(p, 'order_index', 0) or 0)
    first_page = sorted_pages[0]
    outline = None
    if hasattr(first_page, 'get_outline_content') and callable(first_page.get_outline_content):
        outline = first_page.get_outline_content()
    elif hasattr(first_page, 'outline_content'):
        outline = first_page.outline_content
    if isinstance(outline, dict):
        return str(outline.get('title') or '').strip()
    return ''


def _extract_concise_prompt_line(value: Optional[str]) -> str:
    text = str(value or '').strip()
    if not text:
        return ''
    for line in text.splitlines():
        cleaned = line.strip().lstrip('#*- \t"\'“”')
        cleaned = SLIDE_PREFIX_RE.sub('', cleaned).strip()
        if cleaned:
            # Prefer first sentence/clause when line is very long
            for sep in ('. ', ' - ', ' — ', ': ', '; '):
                if sep in cleaned and len(cleaned) > 60:
                    head = cleaned.split(sep, 1)[0].strip()
                    if len(head) >= 8:
                        return head
            return cleaned
    return ''


def get_project_display_name(project: Any, pages: Optional[Iterable[Any]] = None) -> str:
    """Resolve the best concise display title for a project."""
    project_title = str(getattr(project, 'project_title', None) or '').strip()
    if project_title:
        return project_title

    page_list = pages if pages is not None else getattr(project, 'pages', None)
    first_page_title = _extract_first_page_title(page_list)
    if first_page_title and not GENERIC_SLIDE_TITLE_RE.match(first_page_title):
        return first_page_title

    for attr in ('idea_prompt', 'outline_text', 'description_text'):
        candidate = _extract_concise_prompt_line(getattr(project, attr, None))
        if candidate:
            return candidate

    if first_page_title:
        return first_page_title

    project_id = str(getattr(project, 'id', '') or '')[:8]
    return f'banana-slides-{project_id}' if project_id else 'presentation'


def build_export_filename(
    project: Any,
    ext: str,
    requested_filename: Optional[str] = None,
    suffix: str = '',
    pages: Optional[Iterable[Any]] = None,
    max_base_length: int = 48,
) -> str:
    """Build a concise, human-friendly, secure_filename-safe export filename."""
    clean_ext = (ext or '').strip().lower()
    if clean_ext and not clean_ext.startswith('.'):
        clean_ext = f'.{clean_ext}'

    project_id = str(getattr(project, 'id', '') or '')[:8]
    default_base = f'banana-slides-{project_id}' if project_id else 'presentation'

    req = str(requested_filename or '').strip()
    if req:
        stem = req[:-len(clean_ext)] if (clean_ext and req.lower().endswith(clean_ext)) else req
        slug = slugify_filename(stem, max_length=64, default=default_base)
        safe = secure_filename(f'{slug}{clean_ext}')
        return safe if safe and (not clean_ext or safe.lower().endswith(clean_ext)) else f'{default_base}{clean_ext}'

    display_name = get_project_display_name(project, pages=pages)
    base = slugify_filename(display_name, max_length=max_base_length, default=default_base)

    suffix_slug = slugify_filename(suffix, max_length=24, default='') if suffix and suffix.strip() else ''
    suffix_part = f'-{suffix_slug}' if suffix_slug else ''

    safe = secure_filename(f'{base}{suffix_part}{clean_ext}')
    if not safe or (clean_ext and not safe.lower().endswith(clean_ext)):
        return secure_filename(f'{default_base}{suffix_part}{clean_ext}')
    return safe
