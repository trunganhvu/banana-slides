"""
HTML Slide Service - parse multi-slide HTML presentations into standalone slides,
extract structured content for AI reverse-description synthesis, and render slide images.
"""
import copy
import logging
import os
import re
import shutil
import subprocess
import tempfile
from math import gcd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

SLIDE_CLASS_TOKENS = {
    'slide',
    'ppt-slide',
    'slide-page',
    'slide-item',
    'slide-card',
    'slide-frame',
    'deck-slide',
    'swiper-slide',
    'remark-slide-container',
    'bespoke-slide',
}

SECONDARY_SLIDE_CLASS_TOKENS = {'page', 'step'}

SLIDE_ID_RE = re.compile(r'^(?:slide|page|frame|screen)[-_]?\d+$', re.IGNORECASE)

GLOBAL_NAV_CLASS_TOKENS = {
    'controls',
    'slide-controls',
    'slide-nav',
    'nav-controls',
    'navigation',
    'pagination',
    'pager',
    'toolbar',
    'progress-bar',
    'slide-counter',
    'deck-controls',
    'presenter-controls',
}

FRAME_STYLE_RE = re.compile(
    r'(?:100vh|min-h-screen|h-screen|aspect-video|1280px|1920px|720px|1080px|page-break-after)',
    re.IGNORECASE,
)

STYLE_OVERRIDE_CSS = """
html, body {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  height: 100% !important;
  overflow: hidden !important;
}
[data-banana-slide-root="true"] {
  margin: 0 !important;
  box-sizing: border-box !important;
  visibility: visible !important;
  opacity: 1 !important;
}
"""

INIT_VISIBILITY_SCRIPT = """
(function() {
  function revealSlide() {
    var root = document.querySelector('[data-banana-slide-root="true"]');
    if (!root) return;
    var el = root;
    while (el && el !== document.documentElement) {
      var cs = window.getComputedStyle(el);
      if (cs.display === 'none') {
        el.style.setProperty('display', el === root ? 'flex' : 'block', 'important');
      }
      if (cs.visibility === 'hidden') {
        el.style.setProperty('visibility', 'visible', 'important');
      }
      if (parseFloat(cs.opacity) === 0) {
        el.style.setProperty('opacity', '1', 'important');
      }
      el = el.parentElement;
    }
    var rootStyle = window.getComputedStyle(root);
    var rect = root.getBoundingClientRect();
    if (rootStyle.transform && rootStyle.transform !== 'none') {
      if (rect.right <= 0 || rect.left >= window.innerWidth || rect.bottom <= 0 || rect.top >= window.innerHeight) {
        root.style.setProperty('transform', 'none', 'important');
      }
    }
    if (rect.width < window.innerWidth * 0.6 || rect.height < window.innerHeight * 0.6) {
      root.style.setProperty('width', '100%', 'important');
      root.style.setProperty('height', '100%', 'important');
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', revealSlide);
  } else {
    revealSlide();
  }
  window.addEventListener('load', revealSlide);
  setTimeout(revealSlide, 120);
})();
"""


def _make_soup(html_content: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html_content, 'lxml')
    except Exception:
        return BeautifulSoup(html_content, 'html.parser')


def _get_classes(tag: Tag) -> List[str]:
    raw = tag.get('class')
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(c).strip() for c in raw if str(c).strip()]
    return [c.strip() for c in str(raw).split() if c.strip()]


def _has_any_class_token(tag: Tag, tokens: set) -> bool:
    return any(cls.lower() in tokens for cls in _get_classes(tag))


def _filter_outermost_tags(tags: List[Tag]) -> List[Tag]:
    """Keep order while removing descendants of already selected tags.
    If a single outer wrapper contains multiple selected inner tags, unwrap it.
    """
    unique: List[Tag] = []
    seen_ids = set()
    for t in tags:
        tid = id(t)
        if tid not in seen_ids:
            seen_ids.add(tid)
            unique.append(t)

    tag_set = set(seen_ids)
    outermost: List[Tag] = []
    for t in unique:
        has_selected_ancestor = any(id(anc) in tag_set for anc in t.parents)
        if not has_selected_ancestor:
            outermost.append(t)

    if len(outermost) == 1:
        outer = outermost[0]
        nested = [t for t in unique if t is not outer and outer in t.parents]
        if len(nested) >= 2:
            return _filter_outermost_tags(nested)

    return outermost


def _is_non_content_tag(tag: Tag) -> bool:
    return tag.name in {'script', 'style', 'link', 'meta', 'noscript', 'template'}


def _find_slide_elements(soup: BeautifulSoup) -> List[Tag]:
    """Detect slide elements inside a parsed HTML document using a priority chain."""
    body = soup.body or soup

    # 1. Explicit [data-slide] (excluding navigation buttons/links) or [aria-roledescription="slide"]
    explicit_slides: List[Tag] = []
    for el in body.find_all(True):
        if _is_non_content_tag(el):
            continue
        if el.name in {'button', 'a'} or el.has_attr('data-slide-to'):
            continue
        if el.has_attr('data-slide') or (el.get('aria-roledescription') or '').lower() == 'slide':
            explicit_slides.append(el)
    explicit_slides = _filter_outermost_tags(explicit_slides)
    if len(explicit_slides) >= 2:
        return explicit_slides

    # 2. Elements with standard slide classes
    class_slides: List[Tag] = []
    for el in body.find_all(['section', 'div', 'article', 'main', 'li']):
        if _has_any_class_token(el, SLIDE_CLASS_TOKENS):
            class_slides.append(el)
    class_slides = _filter_outermost_tags(class_slides)
    if len(class_slides) >= 2:
        return class_slides
    if len(class_slides) == 1 and not explicit_slides:
        # Check if secondary class tokens have >= 2 candidates before settling on 1
        pass

    # 2b. Secondary class tokens ('page', 'step') when >= 2 siblings
    secondary_slides = _filter_outermost_tags([
        el for el in body.find_all(['section', 'div', 'article', 'main', 'li'])
        if _has_any_class_token(el, SECONDARY_SLIDE_CLASS_TOKENS)
    ])
    if len(secondary_slides) >= 2:
        return secondary_slides

    # 3. Elements with slide/page/frame/screen + number IDs (>= 2)
    id_slides = _filter_outermost_tags([
        el for el in body.find_all(['div', 'section', 'article'])
        if el.get('id') and SLIDE_ID_RE.match(str(el.get('id')).strip())
    ])
    if len(id_slides) >= 2:
        return id_slides

    # 4. Reveal.js .reveal .slides > section (including nested vertical sections)
    reveal_slides_container = soup.select_one('.reveal .slides')
    if reveal_slides_container:
        reveal_sections: List[Tag] = []
        for top_sec in reveal_slides_container.find_all('section', recursive=False):
            nested_secs = top_sec.find_all('section', recursive=False)
            if nested_secs:
                reveal_sections.extend(nested_secs)
            else:
                reveal_sections.append(top_sec)
        if len(reveal_sections) >= 1:
            return reveal_sections

    # 4b. Top-level or sibling <section> tags (>= 2)
    direct_sections = [el for el in body.find_all('section', recursive=False)]
    if len(direct_sections) >= 2:
        return direct_sections
    all_sections = _filter_outermost_tags(list(body.find_all('section')))
    if len(all_sections) >= 2:
        return all_sections

    # 5. Repeating direct children with frame-like styling inside body or main wrapper
    container_candidates = [body]
    direct_children = [c for c in body.find_all(True, recursive=False) if not _is_non_content_tag(c)]
    if len(direct_children) == 1 and direct_children[0].name in {'div', 'main', 'section'}:
        container_candidates.append(direct_children[0])

    for container in container_candidates:
        children = [
            c for c in container.find_all(['div', 'section', 'article'], recursive=False)
            if not _has_any_class_token(c, GLOBAL_NAV_CLASS_TOKENS)
        ]
        if len(children) >= 2:
            frame_children = [
                c for c in children
                if FRAME_STYLE_RE.search(' '.join(_get_classes(c)) + ' ' + str(c.get('style') or ''))
            ]
            if len(frame_children) >= 2:
                return frame_children

            # Same tag + shared non-empty primary class across >= 2 siblings
            sig_groups: Dict[Tuple[str, Tuple[str, ...]], List[Tag]] = {}
            for c in children:
                classes = tuple(sorted(_get_classes(c)))
                if classes:
                    sig_groups.setdefault((c.name, classes), []).append(c)
            for group in sig_groups.values():
                if len(group) >= 2 and all(g.get_text(strip=True) for g in group):
                    return group

    if len(class_slides) == 1:
        return class_slides
    if len(explicit_slides) == 1:
        return explicit_slides

    # 6. Fallback: entire body as single slide
    return [body]


def _is_global_nav_element(tag: Tag) -> bool:
    if not isinstance(tag, Tag):
        return False
    if tag.name == 'nav':
        return True
    if (tag.get('role') or '').lower() == 'navigation':
        return True
    if _has_any_class_token(tag, GLOBAL_NAV_CLASS_TOKENS):
        return True
    if tag.name in {'button', 'div'} and tag.has_attr('data-slide-to'):
        return True
    return False


def _remove_non_target_nodes(
    root: Tag,
    target_slide: Tag,
    all_slides_set: set,
) -> None:
    """Prune sibling slides and global nav controls outside target_slide while keeping its ancestor chain."""
    target_ancestors = {id(target_slide)} | {id(anc) for anc in target_slide.parents}

    for child in list(root.children):
        if not isinstance(child, Tag):
            continue
        if id(child) == id(target_slide):
            continue
        if id(child) in all_slides_set:
            child.decompose()
            continue
        if id(child) in target_ancestors:
            _remove_non_target_nodes(child, target_slide, all_slides_set)
            continue
        if _is_non_content_tag(child):
            continue
        # Remove global controls/nav bars outside the target slide
        if _is_global_nav_element(child):
            child.decompose()
            continue
        # If this branch contains any other slide, inspect or prune it
        has_other_slide = any(id(desc) in all_slides_set for desc in child.find_all(True))
        if has_other_slide:
            _remove_non_target_nodes(child, target_slide, all_slides_set)
            # Clean up now-empty non-script wrappers
            if not child.get_text(strip=True) and not child.find(['img', 'svg', 'canvas', 'video', 'iframe']):
                child.decompose()


def _build_standalone_slide_html(
    original_html: str,
    slide_index: int,
    slide_count: int,
) -> str:
    """Clone the original DOM and isolate slide at `slide_index` with head styles intact."""
    soup = _make_soup(original_html)
    slides = _find_slide_elements(soup)
    if not slides:
        return original_html

    safe_idx = min(max(0, slide_index), len(slides) - 1)
    target = slides[safe_idx]
    all_slides_set = {id(s) for s in slides}

    body = soup.body
    if body is not None and target is not body:
        _remove_non_target_nodes(body, target, all_slides_set)

    target['data-banana-slide-root'] = 'true'
    existing_classes = _get_classes(target)
    for active_cls in ('active', 'current', 'present', 'visible'):
        if active_cls not in existing_classes:
            existing_classes.append(active_cls)
    target['class'] = existing_classes

    # Remove inline display:none / visibility:hidden on target and ancestors
    for node in [target, *target.parents]:
        if not isinstance(node, Tag) or node.name in {'html', '[document]'}:
            break
        inline_style = str(node.get('style') or '')
        if inline_style:
            cleaned_style = re.sub(r'display\s*:\s*none\s*;?', '', inline_style, flags=re.IGNORECASE)
            cleaned_style = re.sub(r'visibility\s*:\s*hidden\s*;?', '', cleaned_style, flags=re.IGNORECASE)
            cleaned_style = cleaned_style.strip()
            if cleaned_style:
                node['style'] = cleaned_style
            elif node.has_attr('style'):
                del node['style']

    # Inject style override + visibility helper script
    head = soup.head
    if head is None and soup.html is not None:
        head = soup.new_tag('head')
        soup.html.insert(0, head)
    if head is not None:
        if not head.find('meta', attrs={'charset': True}):
            meta_tag = soup.new_tag('meta', charset='utf-8')
            head.insert(0, meta_tag)
        style_tag = soup.new_tag('style', id='banana-slide-style')
        style_tag.string = STYLE_OVERRIDE_CSS
        head.append(style_tag)

    container = soup.body or soup.html or soup
    script_tag = soup.new_tag('script', id='banana-slide-init')
    script_tag.string = INIT_VISIBILITY_SCRIPT
    container.append(script_tag)

    result = str(soup)
    if '<!doctype' not in result[:100].lower():
        result = '<!DOCTYPE html>\n' + result
    return result


def _clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text or '').strip()


def _table_to_markdown(table_tag: Tag) -> str:
    rows: List[List[str]] = []
    for tr in table_tag.find_all('tr'):
        cells = [_clean_text(cell.get_text(' ', strip=True)) for cell in tr.find_all(['th', 'td'])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    col_count = max(len(r) for r in rows)
    normalized = [r + [''] * (col_count - len(r)) for r in rows]
    lines = [
        '| ' + ' | '.join(normalized[0]) + ' |',
        '| ' + ' | '.join(['---'] * col_count) + ' |',
    ]
    for r in normalized[1:]:
        lines.append('| ' + ' | '.join(r) + ' |')
    return '\n'.join(lines)


def _compact_slide_html(root: Tag, max_chars: int = 4000) -> str:
    cloned = copy.copy(root)
    # Build detached copy via soup parsing so mutations don't touch original root
    snippet_soup = _make_soup(str(cloned))
    snippet_root = snippet_soup.body.find(True, recursive=False) if snippet_soup.body else snippet_soup
    if snippet_root is None:
        return ''

    for tag in snippet_root.find_all(['script', 'style']):
        tag.decompose()
    for path_tag in snippet_root.find_all('path'):
        if path_tag.has_attr('d') and len(str(path_tag['d'])) > 60:
            path_tag['d'] = str(path_tag['d'])[:60] + '...'
    for img_tag in snippet_root.find_all('img'):
        src = str(img_tag.get('src') or '')
        if src.startswith('data:') and len(src) > 80:
            img_tag['src'] = src[:80] + '...'

    compact = re.sub(r'\s+', ' ', str(snippet_root)).strip()
    if len(compact) > max_chars:
        compact = compact[:max_chars] + '...'
    return compact


def extract_slide_structured_data(slide_el: Tag, index: int) -> Dict[str, Any]:
    """Extract structured title, part, points, markdown text, visuals, layout and notes from a slide element."""
    # Speaker notes
    speaker_notes_parts: List[str] = []
    data_notes = slide_el.get('data-notes')
    if data_notes and str(data_notes).strip():
        speaker_notes_parts.append(_clean_text(str(data_notes)))
    for note_el in slide_el.find_all(
        lambda t: isinstance(t, Tag) and (
            t.name == 'aside' and _has_any_class_token(t, {'notes', 'speaker-notes'})
            or _has_any_class_token(t, {'notes', 'speaker-notes', 'presenter-notes'})
        )
    ):
        txt = _clean_text(note_el.get_text(' ', strip=True))
        if txt:
            speaker_notes_parts.append(txt)
    speaker_notes = '\n'.join(dict.fromkeys(speaker_notes_parts))

    # Part / section label
    part = ''
    for part_el in slide_el.find_all(
        lambda t: isinstance(t, Tag) and any(
            kw in ' '.join(_get_classes(t)).lower()
            for kw in ('part', 'chapter', 'section-label', 'badge', 'eyebrow', 'kicker')
        )
    ):
        txt = _clean_text(part_el.get_text(' ', strip=True))
        if txt and len(txt) <= 80:
            part = txt
            break

    # Title
    title = ''
    for selector in ('h1', 'h2', '[class*="title"]', '[class*="heading"]', 'h3'):
        found = slide_el.select_one(selector)
        if found:
            candidate = _clean_text(found.get_text(' ', strip=True))
            if candidate:
                title = candidate
                break
    if not title:
        # Fallback to first short text block
        for candidate_el in slide_el.find_all(['p', 'div', 'span', 'strong']):
            if candidate_el.find(['h1', 'h2', 'p', 'ul', 'ol', 'table']):
                continue
            candidate = _clean_text(candidate_el.get_text(' ', strip=True))
            if 2 <= len(candidate) <= 120:
                title = candidate
                break
    if not title:
        title = f'Slide {index + 1}'

    # Points & markdown_text in DOM order
    points: List[str] = []
    md_lines: List[str] = []
    seen_texts = set()

    def _add_md_line(line: str) -> None:
        cleaned = line.strip()
        if not cleaned or cleaned in seen_texts:
            return
        seen_texts.add(cleaned)
        md_lines.append(cleaned)

    def _walk_blocks(node: Tag) -> None:
        for child in node.children:
            if isinstance(child, NavigableString):
                continue
            if not isinstance(child, Tag) or _is_non_content_tag(child):
                continue
            # Skip speaker note containers in main body markdown
            if (child.name == 'aside' and _has_any_class_token(child, {'notes', 'speaker-notes'})) or _has_any_class_token(
                child, {'notes', 'speaker-notes', 'presenter-notes'}
            ):
                continue

            if child.name == 'table':
                table_md = _table_to_markdown(child)
                if table_md:
                    md_lines.append(table_md)
                    # Add header/summary row as bullet if points still sparse
                    first_row = child.find('tr')
                    if first_row:
                        row_txt = ' | '.join(
                            _clean_text(c.get_text(' ', strip=True))
                            for c in first_row.find_all(['th', 'td'])
                            if _clean_text(c.get_text(' ', strip=True))
                        )
                        if row_txt and row_txt not in points:
                            points.append(row_txt)
                continue

            if child.name in {'h1', 'h2', 'h3', 'h4'}:
                txt = _clean_text(child.get_text(' ', strip=True))
                if txt:
                    prefix = '#' * int(child.name[1])
                    _add_md_line(f'{prefix} {txt}')
                continue

            if child.name in {'ul', 'ol'}:
                for li in child.find_all('li', recursive=False):
                    txt = _clean_text(li.get_text(' ', strip=True))
                    if txt:
                        _add_md_line(f'- {txt}')
                        if txt != title and txt not in points:
                            points.append(txt)
                continue

            if child.name == 'li':
                txt = _clean_text(child.get_text(' ', strip=True))
                if txt:
                    _add_md_line(f'- {txt}')
                    if txt != title and txt not in points:
                        points.append(txt)
                continue

            if child.name == 'p':
                txt = _clean_text(child.get_text(' ', strip=True))
                if txt:
                    _add_md_line(txt)
                    if txt != title and txt != part and txt not in points and len(txt) <= 220:
                        points.append(txt)
                continue

            # Leaf block container (card, stat box, etc.)
            nested_blocks = child.find(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table', 'div', 'section', 'article'])
            if nested_blocks is None:
                txt = _clean_text(child.get_text(' ', strip=True))
                if txt:
                    _add_md_line(txt)
                    if txt != title and txt != part and txt not in points and 3 <= len(txt) <= 180:
                        points.append(txt)
            else:
                _walk_blocks(child)

    _walk_blocks(slide_el)

    if not md_lines:
        fallback_txt = _clean_text(slide_el.get_text(' ', strip=True))
        if fallback_txt:
            md_lines.append(fallback_txt)

    markdown_text = '\n'.join(md_lines)
    points = points[:8]

    # Visual elements summary
    visual_items: List[str] = []
    imgs = slide_el.find_all('img')
    for img in imgs:
        alt = _clean_text(str(img.get('alt') or ''))
        src = str(img.get('src') or '')
        if alt:
            visual_items.append(f'Image: {alt}')
        elif src and not src.startswith('data:'):
            visual_items.append(f'Image ({Path(src).name})')
        else:
            visual_items.append('Embedded image')

    svgs = slide_el.find_all('svg')
    if svgs:
        visual_items.append(f'{len(svgs)} SVG illustration/icon element(s)')

    canvases = slide_el.find_all('canvas')
    if canvases:
        visual_items.append(f'{len(canvases)} interactive chart/canvas element(s)')

    tables = slide_el.find_all('table')
    if tables:
        visual_items.append(f'{len(tables)} data table(s)')

    visual_summary = '; '.join(visual_items)

    # Layout summary
    layout_clues: List[str] = []
    all_classes_lower = ' '.join(
        ' '.join(_get_classes(t)).lower() for t in [slide_el, *slide_el.find_all(True)]
    )
    all_styles_lower = ' '.join(
        str(t.get('style') or '').lower() for t in [slide_el, *slide_el.find_all(True)]
    )
    combined_hints = f'{all_classes_lower} {all_styles_lower}'

    if 'grid' in combined_hints:
        col_match = re.search(r'grid-cols-(\d+)', combined_hints)
        if col_match:
            layout_clues.append(f'{col_match.group(1)}-column grid layout')
        else:
            layout_clues.append('CSS grid layout')
    if 'flex' in combined_hints:
        if 'flex-row' in combined_hints or 'grid-cols-2' in combined_hints:
            layout_clues.append('multi-column flex alignment')
        else:
            layout_clues.append('flex container structure')
    if 'card' in combined_hints:
        card_count = len(slide_el.find_all(lambda t: isinstance(t, Tag) and 'card' in ' '.join(_get_classes(t)).lower()))
        if card_count:
            layout_clues.append(f'{card_count} content card block(s)')
    if 'chart' in combined_hints or canvases or svgs:
        layout_clues.append('includes visual diagram/chart region')

    bg_match = re.search(r'(?:background(?:-color)?:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\))|bg-(?:slate|gray|zinc|neutral|stone|blue|indigo|purple|emerald|amber|white|black)(?:-\d+)?)', combined_hints)
    if bg_match:
        layout_clues.append(f'background styling ({bg_match.group(0).strip()})')

    if index == 0 and len(points) <= 3 and ('center' in combined_hints or 'cover' in combined_hints or 'hero' in combined_hints):
        layout_clues.insert(0, 'cover slide centered composition')

    layout_summary = ', '.join(dict.fromkeys(layout_clues)) or 'structured single-slide layout'

    return {
        'index': index,
        'title': title,
        'part': part,
        'points': points,
        'markdown_text': markdown_text,
        'visual_summary': visual_summary,
        'layout_summary': layout_summary,
        'speaker_notes': speaker_notes,
        'compact_html': _compact_slide_html(slide_el),
    }


def split_html_to_slides(html_content: str) -> List[Dict[str, Any]]:
    """Split an HTML presentation string into standalone per-slide HTML docs and metadata."""
    if not html_content or not html_content.strip():
        raise ValueError("HTML content is empty")

    soup = _make_soup(html_content)
    slide_elements = _find_slide_elements(soup)
    slide_count = len(slide_elements)

    slides: List[Dict[str, Any]] = []
    for idx, slide_el in enumerate(slide_elements):
        data = extract_slide_structured_data(slide_el, idx)
        data['standalone_html'] = _build_standalone_slide_html(html_content, idx, slide_count)
        slides.append(data)

    return slides


def extract_slide_from_standalone_html(standalone_html: str, index: int = 0) -> Dict[str, Any]:
    """Extract structured slide data from a single saved standalone slide HTML file."""
    soup = _make_soup(standalone_html)
    root = soup.find(attrs={'data-banana-slide-root': 'true'})
    if root is None:
        slides = _find_slide_elements(soup)
        root = slides[0] if slides else (soup.body or soup)
    data = extract_slide_structured_data(root, index)
    data['standalone_html'] = standalone_html
    return data


def detect_html_aspect_ratio_and_size(html_content: str) -> Tuple[str, int, int]:
    """Detect slide aspect ratio and base pixel dimensions from HTML CSS/classes."""
    default_result = ('16:9', 1280, 720)
    if not html_content:
        return default_result

    # Check explicit CSS aspect-ratio: W / H
    ar_match = re.search(r'aspect-ratio\s*:\s*(\d+)\s*/\s*(\d+)', html_content, re.IGNORECASE)
    if ar_match:
        w = int(ar_match.group(1))
        h = int(ar_match.group(2))
        if w > 0 and h > 0:
            g = gcd(w, h)
            nw, nh = w // g, h // g
            ratio = f'{nw}:{nh}'
            if ratio == '4:3':
                return ('4:3', 1024, 768)
            if ratio == '1:1':
                return ('1:1', 1080, 1080)
            if ratio == '9:16':
                return ('9:16', 720, 1280)
            if ratio == '16:9':
                return ('16:9', 1280, 720)
            if 0.2 <= (nw / nh) <= 5.0:
                base_w = 1280 if nw >= nh else 720
                base_h = max(320, round(base_w * nh / nw))
                return (ratio, base_w, base_h)

    # Check CSS width & height pairs (e.g. .slide { width: 1024px; height: 768px; })
    w_match = re.search(r'(?:--slide-width|width)\s*:\s*(\d{3,4})px', html_content, re.IGNORECASE)
    h_match = re.search(r'(?:--slide-height|height)\s*:\s*(\d{3,4})px', html_content, re.IGNORECASE)
    if w_match and h_match:
        w = int(w_match.group(1))
        h = int(h_match.group(1))
        if 300 <= w <= 4096 and 300 <= h <= 4096:
            g = gcd(w, h)
            ratio = f'{w // g}:{h // g}'
            if ratio in {'16:9', '4:3', '1:1', '9:16', '3:2', '21:9', '3:4'}:
                return (ratio, w, h)
            # Snap close ratios
            val = w / h
            if abs(val - 16 / 9) < 0.08:
                return ('16:9', w, h)
            if abs(val - 4 / 3) < 0.08:
                return ('4:3', w, h)
            if abs(val - 1.0) < 0.08:
                return ('1:1', w, h)
            if abs(val - 9 / 16) < 0.08:
                return ('9:16', w, h)
            if 0.2 <= val <= 5.0 and len(ratio) <= 10:
                return (ratio, w, h)

    return default_result


def build_fallback_slide_content(
    slide_data: Dict[str, Any],
    index: int = 0,
    language: str = 'vi',
) -> Dict[str, Any]:
    """Build structured title/points/description/extra_fields directly from parsed HTML data."""
    is_en = (language or '').lower().startswith('en')
    title = (slide_data.get('title') or '').strip() or f'Slide {index + 1}'
    part = (slide_data.get('part') or '').strip()
    points = [str(p).strip() for p in (slide_data.get('points') or []) if str(p).strip()]
    md_text = (slide_data.get('markdown_text') or '').strip()

    if md_text:
        description = md_text
    elif points:
        description = '\n'.join(f'- {p}' for p in points)
    else:
        description = title

    visual_summary = (slide_data.get('visual_summary') or '').strip()
    layout_summary = (slide_data.get('layout_summary') or '').strip()
    speaker_notes = (slide_data.get('speaker_notes') or '').strip()

    extra_fields: Dict[str, str] = {}
    if visual_summary:
        extra_fields['Hình ảnh & Tư liệu'] = visual_summary
    else:
        extra_fields['Hình ảnh & Tư liệu'] = (
            'Minimalist visual layout matching the HTML slide design.'
            if is_en
            else 'Minh họa và biểu tượng tối giản đồng bộ với thiết kế của slide HTML.'
        )

    if layout_summary:
        extra_fields['Bố cục & Trọng tâm'] = layout_summary
    else:
        extra_fields['Bố cục & Trọng tâm'] = (
            'Clear title header with structured content region.'
            if is_en
            else 'Tiêu đề nổi bật phía trên, nội dung được sắp xếp rõ ràng theo bố cục gốc của slide HTML.'
        )

    if speaker_notes:
        extra_fields['Ghi chú thuyết trình'] = speaker_notes
    else:
        extra_fields['Ghi chú thuyết trình'] = (
            f'Present key takeaways for "{title}".'
            if is_en
            else f'Trình bày và nhấn mạnh các luận điểm chính của trang "{title}".'
        )

    return {
        'title': title,
        'part': part,
        'points': points,
        'description': description,
        'extra_fields': extra_fields,
    }


def _find_headless_browser() -> Optional[str]:
    """Locate an installed Chrome/Edge/Chromium binary for headless screenshots."""
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'msedge', 'chrome'):
        found = shutil.which(name)
        if found:
            return found

    candidate_paths = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/microsoft-edge',
    ]
    for path in candidate_paths:
        if os.path.isfile(path):
            return path
    return None


def _render_with_headless_browser(
    html_file_path: str,
    width: int,
    height: int,
    timeout: int = 18,
) -> Optional[Image.Image]:
    browser = _find_headless_browser()
    if not browser:
        return None

    file_uri = Path(html_file_path).resolve().as_uri()
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        out_png = tmp.name

    try:
        for headless_flag in ('--headless=new', '--headless'):
            cmd = [
                browser,
                headless_flag,
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--hide-scrollbars',
                '--virtual-time-budget=1500',
                f'--window-size={width},{height}',
                f'--screenshot={out_png}',
                file_uri,
            ]
            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                    check=False,
                )
                if proc.returncode == 0 and os.path.isfile(out_png) and os.path.getsize(out_png) > 200:
                    with Image.open(out_png) as img:
                        loaded = img.convert('RGB')
                    if loaded.size != (width, height):
                        loaded = loaded.resize((width, height), Image.Resampling.LANCZOS)
                    return loaded
            except subprocess.TimeoutExpired:
                logger.warning("Headless browser screenshot timed out for %s", html_file_path)
                break
            except Exception as exc:
                logger.debug("Headless browser attempt failed (%s): %s", headless_flag, exc)
    finally:
        try:
            os.remove(out_png)
        except OSError:
            pass

    return None


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates: List[str] = []
    if bold:
        candidates.extend([
            r'C:\Windows\Fonts\segoeuib.ttf',
            r'C:\Windows\Fonts\arialbd.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        ])
    else:
        candidates.extend([
            r'C:\Windows\Fonts\segoeui.ttf',
            r'C:\Windows\Fonts\arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ])
    repo_font = Path(__file__).resolve().parent.parent / 'fonts' / 'NotoSansSC-Regular.ttf'
    if repo_font.exists():
        candidates.append(str(repo_font))

    for font_path in candidates:
        if os.path.isfile(font_path):
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f'{current} {word}'
        bbox = draw.textbbox((0, 0), trial, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _render_slide_fallback_image(
    slide_data: Dict[str, Any],
    width: int = 1280,
    height: int = 720,
) -> Image.Image:
    """Render a clean slide preview PNG using Pillow when headless browser is unavailable."""
    raw_html = str(slide_data.get('standalone_html') or slide_data.get('compact_html') or '').lower()
    is_dark = any(
        hint in raw_html
        for hint in ('bg-slate-9', 'bg-gray-9', 'bg-zinc-9', 'bg-black', '#0f172a', '#111827', '#000000', '#1a1a')
    )
    bg_color = (15, 23, 42) if is_dark else (248, 250, 252)
    card_color = (30, 41, 59) if is_dark else (255, 255, 255)
    title_color = (248, 250, 252) if is_dark else (15, 23, 42)
    body_color = (203, 213, 225) if is_dark else (51, 65, 85)
    accent_color = (245, 158, 11)

    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    pad = max(36, int(width * 0.05))
    draw.rounded_rectangle(
        [(pad, pad), (width - pad, height - pad)],
        radius=20,
        fill=card_color,
        outline=(71, 85, 105) if is_dark else (226, 232, 240),
        width=2,
    )
    draw.rectangle([(pad, pad + 24), (pad + 10, pad + 88)], fill=accent_color)

    title_font = _load_font(max(24, int(height * 0.055)), bold=True)
    body_font = _load_font(max(16, int(height * 0.032)), bold=False)
    meta_font = _load_font(max(13, int(height * 0.022)), bold=False)

    title = (slide_data.get('title') or f"Slide {slide_data.get('index', 0) + 1}").strip()
    inner_x = pad + 36
    inner_max_w = width - (pad * 2) - 72
    y = pad + 28

    for tline in _wrap_text(draw, title, title_font, inner_max_w)[:2]:
        draw.text((inner_x, y), tline, font=title_font, fill=title_color)
        bbox = draw.textbbox((inner_x, y), tline, font=title_font)
        y += (bbox[3] - bbox[1]) + 10

    y += 12
    draw.line([(inner_x, y), (width - pad - 36, y)], fill=(51, 65, 85) if is_dark else (226, 232, 240), width=2)
    y += 24

    items = slide_data.get('points') or []
    if not items and slide_data.get('markdown_text'):
        items = [ln.lstrip('#- ').strip() for ln in str(slide_data['markdown_text']).splitlines() if ln.strip()]

    for item in items[:7]:
        wrapped = _wrap_text(draw, f'• {item}', body_font, inner_max_w)
        for line in wrapped[:2]:
            if y > height - pad - 56:
                break
            draw.text((inner_x, y), line, font=body_font, fill=body_color)
            bbox = draw.textbbox((inner_x, y), line, font=body_font)
            y += (bbox[3] - bbox[1]) + 8
        y += 6

    footer = f"HTML Slide {slide_data.get('index', 0) + 1}"
    draw.text((inner_x, height - pad - 34), footer, font=meta_font, fill=(148, 163, 184))
    return img


def render_html_slide_to_image(
    standalone_html: str,
    slide_data: Dict[str, Any],
    width: int = 1280,
    height: int = 720,
    html_file_path: Optional[str] = None,
    use_browser: bool = False,
) -> Image.Image:
    """Render a standalone HTML slide into a PIL Image (headless browser when requested, Pillow fallback)."""
    if use_browser:
        tmp_path = None
        target_path = html_file_path
        try:
            if not target_path or not os.path.isfile(target_path):
                with tempfile.NamedTemporaryFile('w', suffix='.html', encoding='utf-8', delete=False) as tf:
                    tf.write(standalone_html)
                    tmp_path = tf.name
                    target_path = tmp_path
            rendered = _render_with_headless_browser(target_path, width=width, height=height)
            if rendered is not None:
                return rendered
        finally:
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    return _render_slide_fallback_image(slide_data, width=width, height=height)
