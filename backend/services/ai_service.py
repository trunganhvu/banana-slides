"""
AI Service - handles all AI model interactions
Based on demo.py and gemini_genai.py
TODO: use structured output API
"""
import os
import json
import re
import logging
import requests
from typing import List, Dict, Optional, Union, Any
from textwrap import dedent
from PIL import Image
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from .prompts import (
    get_outline_generation_prompt,
    get_outline_parsing_prompt,
    get_page_description_prompt,
    get_all_descriptions_stream_prompt,
    get_image_generation_prompt,
    get_image_edit_prompt,
    get_description_to_outline_prompt,
    get_description_split_prompt,
    get_outline_refinement_prompt,
    get_descriptions_refinement_prompt,
    get_ppt_page_content_extraction_prompt,
    get_layout_caption_prompt,
    get_style_extraction_prompt,
    get_style_from_content_prompt,
    get_outline_generation_prompt_markdown,
    get_outline_parsing_prompt_markdown,
    get_description_to_outline_prompt_markdown,
    get_template_analysis_prompt,
    get_template_auto_match_prompt,
)
from .ai_providers import get_text_provider, get_image_provider, get_caption_provider, TextProvider, ImageProvider
from config import get_config

logger = logging.getLogger(__name__)


# Matches H1 headings that carry explicit part/section semantics, e.g.
# Backend logic
# opening chapter apart from a deck-level document title that has no such marker.
_PART_HEADER_RE = re.compile(
    r'^\s*(part|section|chapter|module|unit|chuong|phan)\b'
    r'|\s*(part|chapter|chuong|phan)\s*[0-9]+',
    re.IGNORECASE,
)


def _is_part_header(heading: str) -> bool:
    """Whether an H1 line reads as a part/section header rather than a deck title."""
    return bool(_PART_HEADER_RE.search(heading or ''))


def _describe_json_response_text(text: str) -> str:
    """Return a compact, non-secret hint about an AI response that failed JSON parsing."""
    stripped = str(text or "").strip()
    if not stripped:
        return "empty"
    if stripped.startswith("!["):
        return "markdown_image"
    if stripped.startswith("```"):
        return "markdown_fence"
    if stripped.startswith("<"):
        return "html_or_xml"
    if stripped[:1] in ("{", "["):
        return "json_like"
    return "plain_text"


class ProjectContext:
    """ Backend docstring """
    
    def __init__(self, project_or_dict, reference_files_content: Optional[List[Dict[str, str]]] = None):
        """
        Args:
            project_or_dict:  (Project model)  (project.to_dict()) 
            reference_files_content: 
        """
        # Backend logic
        if hasattr(project_or_dict, 'idea_prompt'):
            # Backend logic
            self.idea_prompt = project_or_dict.idea_prompt
            self.outline_text = project_or_dict.outline_text
            self.description_text = project_or_dict.description_text
            self.creation_type = project_or_dict.creation_type or 'idea'
            self.outline_requirements = project_or_dict.outline_requirements
            self.description_requirements = project_or_dict.description_requirements
        else:
            # Backend logic
            self.idea_prompt = project_or_dict.get('idea_prompt')
            self.outline_text = project_or_dict.get('outline_text')
            self.description_text = project_or_dict.get('description_text')
            self.creation_type = project_or_dict.get('creation_type', 'idea')
            self.outline_requirements = project_or_dict.get('outline_requirements')
            self.description_requirements = project_or_dict.get('description_requirements')

        self.reference_files_content = reference_files_content or []

    def to_dict(self) -> Dict:
        """ Backend docstring """
        return {
            'idea_prompt': self.idea_prompt,
            'outline_text': self.outline_text,
            'description_text': self.description_text,
            'creation_type': self.creation_type,
            'outline_requirements': self.outline_requirements,
            'description_requirements': self.description_requirements,
            'reference_files_content': self.reference_files_content
        }


class AIService:
    """Service for AI model interactions using pluggable providers"""
    
    def __init__(self, text_provider: TextProvider = None, image_provider: ImageProvider = None, caption_provider: TextProvider = None):
        """
        Initialize AI service with providers
        
        Args:
            text_provider: Optional pre-configured TextProvider. If None, created from factory.
            image_provider: Optional pre-configured ImageProvider. If None, created from factory.
        """
        config = get_config()

        # Backend logic
        try:
            from flask import current_app, has_app_context
        except ImportError:
            current_app = None  # type: ignore
            has_app_context = lambda: False  # type: ignore

        from .ai_providers import _resolve_setting
        if has_app_context() and current_app and hasattr(current_app, "config"):
            self.text_model = _resolve_setting("TEXT_MODEL") or current_app.config.get("TEXT_MODEL", config.TEXT_MODEL)
            self.image_model = _resolve_setting("IMAGE_MODEL") or current_app.config.get("IMAGE_MODEL", config.IMAGE_MODEL)
            # Backend logic
            self.enable_text_reasoning = current_app.config.get("ENABLE_TEXT_REASONING", False)
            self.text_thinking_budget = current_app.config.get("TEXT_THINKING_BUDGET", 1024)
            self.enable_image_reasoning = current_app.config.get("ENABLE_IMAGE_REASONING", False)
            self.image_thinking_budget = current_app.config.get("IMAGE_THINKING_BUDGET", 1024)
        else:
            self.text_model = _resolve_setting("TEXT_MODEL") or config.TEXT_MODEL
            self.image_model = _resolve_setting("IMAGE_MODEL") or config.IMAGE_MODEL
            self.enable_text_reasoning = False
            self.text_thinking_budget = 1024
            self.enable_image_reasoning = False
            self.image_thinking_budget = 1024
        
        # Caption model for multimodal (image→text) tasks
        if has_app_context() and current_app and hasattr(current_app, "config"):
            self.caption_model = _resolve_setting("IMAGE_CAPTION_MODEL") or current_app.config.get("IMAGE_CAPTION_MODEL", config.IMAGE_CAPTION_MODEL)
        else:
            self.caption_model = _resolve_setting("IMAGE_CAPTION_MODEL") or config.IMAGE_CAPTION_MODEL

        # Use provided providers or create from factory based on AI_PROVIDER_FORMAT (from Flask config or env var)
        self.text_provider = text_provider or get_text_provider(model=self.text_model)
        self.image_provider = image_provider or get_image_provider(model=self.image_model)
        self.caption_provider = caption_provider or get_caption_provider(model=self.caption_model)
    
    def _get_text_thinking_budget(self) -> int:
        """
        
        
        Returns:
             budget,  0
        """
        return self.text_thinking_budget if self.enable_text_reasoning else 0
    
    def _get_image_thinking_budget(self) -> int:
        """
        
        
        Returns:
             budget,  0
        """
        return self.image_thinking_budget if self.enable_image_reasoning else 0
    
    @staticmethod
    def extract_image_urls_from_markdown(text: str) -> List[str]:
        """
         markdown  URL
        
        Args:
            text: Markdown ,  ![](url) 
            
        Returns:
             URL  ( http/https URL  /files/ ) 
        """
        if not text:
            return []
        
        # Backend logic
        pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(pattern, text)
        
        # Backend logic
        urls = []
        for url in matches:
            url = url.strip()
            if url and (url.startswith('http://') or url.startswith('https://') or url.startswith('/files/')):
                urls.append(url)
        
        return urls
    
    @staticmethod
    def remove_markdown_images(text: str) -> str:
        """
         Markdown ,  alt text () 
        
        Args:
            text:  Markdown 
            
        Returns:
            , 
        """
        if not text:
            return text
        
        # Backend logic
        # Backend logic
        def replace_image(match):
            alt_text = match.group(1).strip()
            # Backend logic
            return alt_text if alt_text else ''
        
        pattern = r'!\[(.*?)\]\([^\)]+\)'
        cleaned_text = re.sub(pattern, replace_image, text)
        
        # Backend logic
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        
        return cleaned_text
    
    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        reraise=True
    )
    def generate_json(self, prompt: str, thinking_budget: int = 1000) -> Union[Dict, List]:
        """
        JSON, 
        
        Args:
            prompt: 
            thinking_budget:  ( enable_text_reasoning ) 
            
        Returns:
            JSON () 
            
        Raises:
            json.JSONDecodeError: JSON (3) 
        """
        # Backend logic
        actual_budget = self._get_text_thinking_budget()
        response_text = self.text_provider.generate_text(prompt, thinking_budget=actual_budget)
        
        # Backend logic
        cleaned_text = response_text.strip().strip("```json").strip("```").strip()
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSONphân tích thất bại, sẽ tạo lại. Văn bản gốc: {cleaned_text[:200]}... Lỗi: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        reraise=True
    )
    def generate_json_with_image(self, prompt: str, image_path: str, thinking_budget: int = 1000) -> Union[Dict, List]:
        """
        JSON,  (3) 
        
        Args:
            prompt: 
            image_path: 
            thinking_budget:  ( enable_text_reasoning ) 
            
        Returns:
            JSON () 
            
        Raises:
            json.JSONDecodeError: JSON (3) 
            ValueError: caption_provider 
        """
        # Backend logic
        actual_budget = self._get_text_thinking_budget()
        provider = self.caption_provider
        if hasattr(provider, 'generate_with_image'):
            response_text = provider.generate_with_image(
                prompt=prompt,
                image_path=image_path,
                thinking_budget=actual_budget
            )
        elif hasattr(provider, 'generate_text_with_images'):
            response_text = provider.generate_text_with_images(
                prompt=prompt,
                images=[image_path],
                thinking_budget=actual_budget
            )
        else:
            raise ValueError("caption_provider không hỗ trợ đầu vào hình ảnh")

        # Backend logic
        cleaned_text = (response_text or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        if not cleaned_text:
            logger.warning("Mô hình thị giác trả về phản hồi rỗng (kèm hình ảnh) , sẽ thử lại")
            raise ValueError("Mô hình thị giác trả về phản hồi rỗng")

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(
                "JSONphân tích thất bại (kèm hình ảnh) , sẽ tạo lại. provider=%s image=%s response_kind=%s response_len=%s "
                "Văn bản gốc: %s... Lỗi: %s",
                provider.__class__.__name__,
                os.path.basename(image_path),
                _describe_json_response_text(cleaned_text),
                len(cleaned_text),
                cleaned_text[:200],
                str(e),
            )
            raise
    
    @staticmethod
    def _convert_mineru_path_to_local(mineru_path: str) -> Optional[str]:
        """
         /files/mineru/{extract_id}/{rel_path}  () 
        
        Args:
            mineru_path: MinerU URL ,  /files/mineru/{extract_id}/{rel_path}
            
        Returns:
            ,  None
        """
        from utils.path_utils import find_mineru_file_with_prefix
        
        matched_path = find_mineru_file_with_prefix(mineru_path)
        return str(matched_path) if matched_path else None
    
    @staticmethod
    def download_image_from_url(url: str) -> Optional[Image.Image]:
        """
         URL  PIL Image 
        
        Args:
            url:  URL
            
        Returns:
            PIL Image ,  None
        """
        try:
            logger.debug(f"Downloading image from URL: {url}")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Backend logic
            image = Image.open(response.raw)
            # Backend logic
            image.load()
            logger.debug(f"Successfully downloaded image: {image.size}, {image.mode}")
            return image
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {str(e)}")
            return None
    
    def generate_outline(self, project_context: ProjectContext, language: str = None) -> List[Dict]:
        """
        Generate PPT outline from idea prompt
        Based on demo.py gen_outline()
        
        Args:
            project_context: , 
            
        Returns:
            List of outline items (may contain parts with pages or direct pages)
        """
        outline_prompt = get_outline_generation_prompt(project_context, language)
        outline = self.generate_json(outline_prompt, thinking_budget=1000)
        return outline

    @staticmethod
    def parse_markdown_outline(markdown: str) -> List[Dict]:
        """
        Parse markdown outline into structured page data.

        Format:
          # Part Name        → sets current part
          ## Page Title      → starts a new page
          - Point text       → adds a bullet point to current page
          Plain sentence     → also treated as a point for sentence-style outlines

        Returns list of dicts: [{"title": ..., "points": [...], "part": ...}, ...]
        """
        pages = []
        current_part = None
        current_page = None
        seen_page = False

        for line in markdown.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith('# ') and not stripped.startswith('## '):
                heading = stripped[2:].strip()
                # A bare H1 before the first page is the deck-level document title,
                # not a part — ignore it so it doesn't pollute the cover's part. But
                # Backend logic
                # directly with a section and has no separate cover.
                if not seen_page and not _is_part_header(heading):
                    continue
                current_part = heading
            elif stripped.startswith('## '):
                seen_page = True
                # New page — flush previous
                if current_page:
                    pages.append(current_page)
                current_page = {
                    'title': stripped[3:].strip(),
                    'points': [],
                }
                if current_part:
                    current_page['part'] = current_part
            elif stripped.startswith('- ') and current_page is not None:
                current_page['points'].append(stripped[2:].strip())
            elif current_page is not None:
                # Backward/forward compatible: support sentence-style outline lines
                # generated under each title (without "- " prefix).
                current_page['points'].append(stripped)

        # Flush last page
        if current_page:
            pages.append(current_page)

        return pages

    def generate_outline_stream(self, project_context: ProjectContext, language: str = None):
        """
        Stream outline generation, yielding each completed page as it's detected.

        Yields dicts: {"title": ..., "points": [...], "part": ...}
        """
        creation_type = project_context.creation_type or 'idea'

        extra_field_names = self._get_extra_field_names() if creation_type == 'descriptions' else []
        field_pattern = self._build_extra_field_pattern(
            self._get_parseable_field_names() if creation_type == 'descriptions' else []
        )

        if creation_type == 'outline':
            prompt = get_outline_parsing_prompt_markdown(project_context, language)
        elif creation_type == 'descriptions':
            prompt = get_description_to_outline_prompt_markdown(
                project_context,
                language,
                extra_fields=extra_field_names,
            )
        else:
            prompt = get_outline_generation_prompt_markdown(project_context, language)

        actual_budget = self._get_text_thinking_budget()
        buffer = ""
        current_part = None
        current_page = None
        current_mode = 'points'
        current_field = None
        stream_complete = False
        seen_page = False

        def _new_page(title: str) -> Dict:
            page = {
                'title': title,
                'points': [],
                'description_lines': [],
                'extra_fields': {},
            }
            if current_part:
                page['part'] = current_part
            return page

        def _finalize_page(page: Optional[Dict]) -> Optional[Dict]:
            if not page:
                return None
            result = {
                'title': page.get('title', ''),
                'points': page.get('points', []),
            }
            if page.get('part'):
                result['part'] = page['part']
            description_text = "\n".join(page.get('description_lines', [])).strip()
            if description_text:
                result['description_text'] = description_text
            if page.get('extra_fields'):
                result['extra_fields'] = dict(page['extra_fields'])
            return result

        def _process_line(line: str, stripped: str):
            nonlocal current_part, current_page, current_mode, current_field, stream_complete, seen_page

            if stripped == '<!-- END -->':
                stream_complete = True
                return None

            if stripped == '<!-- PAGE_END -->':
                finished = _finalize_page(current_page)
                current_page = None
                current_mode = 'points'
                current_field = None
                return finished

            if not stripped:
                if current_page is not None and current_mode == 'description':
                    if current_field:
                        current_page['extra_fields'][current_field] = (
                            current_page['extra_fields'].get(current_field, '') + "\n"
                        )
                    else:
                        current_page['description_lines'].append('')
                return None

            if stripped.startswith('# ') and not stripped.startswith('## '):
                heading = stripped[2:].strip()
                # A bare H1 before the first page is the deck-level document title,
                # not a part — ignore it so it doesn't pollute the cover's part. But
                # Backend logic
                # directly with a section and has no separate cover.
                if not seen_page and not _is_part_header(heading):
                    return None
                current_part = heading
                return None

            if stripped.startswith('## '):
                seen_page = True
                finished = _finalize_page(current_page)
                current_page = _new_page(stripped[3:].strip())
                current_mode = 'points'
                current_field = None
                return finished

            if current_page is None:
                return None

            marker = stripped.strip('*_').strip().lower().replace(': ', ':')
            if (
                marker == '<!-- outline_points -->'
                or marker in ('ý chính dàn ý:', 'dàn ý:', 'đại cương:', 'outline points:', '\u5927\u7eb2\u8981\u70b9:', '\u5927\u7eb2\u8981\u70b9\uff1a')
            ):
                current_mode = 'points'
                current_field = None
                return None

            if (
                marker == '<!-- page_description -->'
                or marker in ('mô tả trang:', 'nội dung trang:', 'page description:', '\u9875\u9762\u63cf\u8ff0:', '\u9875\u9762\u63cf\u8ff0\uff1a')
            ):
                current_mode = 'description'
                current_field = None
                return None

            if current_mode == 'description':
                if field_pattern:
                    field_match = field_pattern.match(stripped)
                    if field_match:
                        from models import Settings
                        current_field = Settings.LEGACY_FIELD_EQUIV.get(field_match.group(1), field_match.group(1))
                        value = field_match.group(2).strip()
                        if value:
                            current_page['extra_fields'][current_field] = value
                        return None

                if current_field:
                    current_page['extra_fields'][current_field] = (
                        current_page['extra_fields'].get(current_field, '') + "\n" + stripped
                    ).strip()
                    return None

                current_page['description_lines'].append(line.rstrip())
                return None

            if stripped.startswith('- '):
                current_page['points'].append(stripped[2:].strip())
            else:
                # Backward/forward compatible: support sentence-style outline lines
                # generated under each title (without "- " prefix).
                current_page['points'].append(stripped)
            return None

        for chunk in self.text_provider.generate_text_stream(prompt, thinking_budget=actual_budget):
            buffer += chunk

            # Process complete lines from buffer
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                finished_page = _process_line(line, line.strip())
                if finished_page:
                    yield finished_page

        # Process remaining buffer
        if buffer.strip():
            for line in buffer.split('\n'):
                finished_page = _process_line(line, line.strip())
                if finished_page:
                    yield finished_page

        # Yield last page
        finished_page = _finalize_page(current_page)
        if finished_page:
            yield finished_page

        # Yield completion sentinel
        yield {'__stream_complete__': stream_complete}
    
    def parse_outline_text(self, project_context: ProjectContext, language: str = None) -> List[Dict]:
        """
        Parse user-provided outline text into structured outline format
        This method analyzes the text and splits it into pages without modifying the original text
        
        Args:
            project_context: , 
        
        Returns:
            List of outline items (may contain parts with pages or direct pages)
        """
        parse_prompt = get_outline_parsing_prompt(project_context, language)
        outline = self.generate_json(parse_prompt, thinking_budget=1000)
        return outline
    
    @staticmethod
    def _normalize_outline_page(
        page: Any,
        page_index: str,
        part: Optional[str] = None,
        has_part: bool = False,
    ) -> Dict:
        if isinstance(page, str):
            title = page.strip()
            if not title:
                raise ValueError(f"Outline page {page_index} is an empty string")
            logger.warning("Normalizing string outline page at %s", page_index)
            normalized = {"title": title, "points": []}
        elif isinstance(page, dict):
            normalized = page.copy()
            title = normalized.get("title")
            if title is None:
                normalized["title"] = ""
            elif not isinstance(title, str):
                normalized["title"] = str(title).strip()
            else:
                normalized["title"] = title.strip()

            points = normalized.get("points", [])
            if points is None:
                normalized["points"] = []
            elif isinstance(points, list):
                normalized["points"] = [
                    str(point).strip()
                    for point in points
                    if point is not None and str(point).strip()
                ]
            elif isinstance(points, str):
                stripped_point = points.strip()
                if stripped_point:
                    logger.warning("Normalizing string outline points at %s", page_index)
                    normalized["points"] = [stripped_point]
                else:
                    normalized["points"] = []
            else:
                raise ValueError(
                    f"Outline page {page_index} points must be a list or string, got {type(points).__name__}"
                )
        else:
            raise ValueError(
                f"Outline page {page_index} must be an object or string, got {type(page).__name__}"
            )

        if has_part:
            normalized["part"] = str(part).strip() if part is not None else None
        elif normalized.get("part") is not None:
            normalized["part"] = str(normalized["part"]).strip()

        return normalized

    def flatten_outline(self, outline: List[Union[Dict[str, Any], str]]) -> List[Dict[str, Any]]:
        """
        Flatten outline structure to page list
        Based on demo.py flatten_outline()
        """
        if not isinstance(outline, list):
            raise ValueError(f"Outline must be a list, got {type(outline).__name__}")

        pages = []
        for item_index, item in enumerate(outline):
            if not isinstance(item, (dict, str)):
                raise ValueError(
                    f"Outline item {item_index} must be an object or string, got {type(item).__name__}"
                )

            if isinstance(item, dict) and "part" in item and "pages" in item:
                # This is a part, expand its pages
                if not isinstance(item["pages"], list):
                    raise ValueError(
                        f"Outline part {item_index} pages must be a list, got {type(item['pages']).__name__}"
                    )
                for page_index, page in enumerate(item["pages"]):
                    pages.append(
                        self._normalize_outline_page(
                            page,
                            f"{item_index}.pages[{page_index}]",
                            part=item["part"],
                            has_part=True,
                        )
                    )
            else:
                # This is a direct page
                pages.append(self._normalize_outline_page(item, str(item_index)))
        return pages
    
    @staticmethod
    def _parse_extra_fields(text: str, field_names: list) -> tuple:
        """
        ,  (cleaned_text, extra_fields_dict). 

         field_names, . 
        . 
        ——, 
        . 
        """
        if not field_names:
            return text, {}

        extra_fields = {}
        # Backend logic
        positions = []
        for name in field_names:
            match = re.search(rf'(?:^|\n){re.escape(name)}[: :]\s*', text)
            if match:
                positions.append((match.start(), match.end(), name))

        if not positions:
            return text, {}

        # Backend logic
        positions.sort(key=lambda x: x[0])

        # Backend logic
        for i, (start, end, name) in enumerate(positions):
            if i + 1 < len(positions):
                value = text[end:positions[i + 1][0]].strip()
            else:
                value = text[end:].strip()
            # Backend logic
            value = re.sub(r'<!--.*?-->', '', value).strip()
            if value:
                from models import Settings
                norm_name = Settings.LEGACY_FIELD_EQUIV.get(name, name)
                extra_fields[norm_name] = value

        # Backend logic
        cleaned_text = text[:positions[0][0]].strip()

        return cleaned_text, extra_fields

    @staticmethod
    def _get_extra_field_names() -> list:
        """ Backend docstring """
        try:
            from models import Settings
            settings = Settings.get_settings()
            return settings.get_description_extra_fields()
        except Exception:
            logger.warning("Failed to get extra field names from settings", exc_info=True)
            return ['Hình ảnh & Tư liệu', 'Bố cục & Trọng tâm', 'Ghi chú thuyết trình']

    @classmethod
    def _get_parseable_field_names(cls) -> list:
        """ =  + . 

         () , : 
        ,  extra_fields, 
        . 
        """
        from models import Settings
        return list(dict.fromkeys(
            [*cls._get_extra_field_names(), *Settings.LEGACY_FIELD_EQUIV.keys()]
        ))

    def generate_page_description(self, project_context: ProjectContext, outline: List[Dict],
                                 page_outline: Dict, page_index: int, language='zh',
                                 detail_level: str = 'default') -> Dict:
        """
        Generate description for a single page
        Based on demo.py gen_desc() logic

        Args:
            project_context: , 
            outline: Complete outline
            page_outline: Outline for this specific page
            page_index: Page number (1-indexed)
            detail_level: Description detail level (concise/default/detailed)

        Returns:
            Dict with 'text' and optional 'extra_fields'
        """
        extra_field_names = self._get_extra_field_names()
        part_info = f"\nThis page belongs to: {page_outline['part']}" if 'part' in page_outline else ""

        desc_prompt = get_page_description_prompt(
            project_context=project_context,
            outline=outline,
            page_outline=page_outline,
            page_index=page_index,
            part_info=part_info,
            language=language,
            detail_level=detail_level,
            extra_fields=extra_field_names,
        )

        # Backend logic
        actual_budget = self._get_text_thinking_budget()
        response_text = self.text_provider.generate_text(desc_prompt, thinking_budget=actual_budget)

        text = dedent(response_text)
        description_text, extra_fields = self._parse_extra_fields(text, self._get_parseable_field_names())

        result = {'text': description_text}
        if extra_fields:
            result['extra_fields'] = extra_fields
        return result

    def generate_descriptions_stream(self, project_context: ProjectContext,
                                     outline: List[Dict], flat_pages: List[Dict],
                                     language: str = 'zh',
                                     detail_level: str = 'default'):
        """
        Stream description generation for all pages, yielding each page as it's completed.

        Yields dicts: {page_index, description_text, extra_fields}
        Final yield: {__stream_complete__: bool}
        """
        extra_field_names = self._get_extra_field_names()

        prompt = get_all_descriptions_stream_prompt(
            project_context=project_context,
            outline=outline,
            flat_pages=flat_pages,
            language=language,
            detail_level=detail_level,
            extra_fields=extra_field_names,
        )

        # Build regex pattern to detect any configured extra field header
        field_pattern = self._build_extra_field_pattern(self._get_parseable_field_names())

        actual_budget = self._get_text_thinking_budget()
        buffer = ""
        page_index = -1
        current_lines: list = []
        current_field: Optional[str] = None  # None = description, str = field name
        extra_fields: Dict[str, str] = {}
        stream_complete = False

        def _build_page_result():
            """Build result dict from accumulated state."""
            desc_text = "\n".join(current_lines).strip()
            result: Dict = {
                'page_index': page_index,
                'description_text': desc_text,
            }
            if extra_fields:
                result['extra_fields'] = dict(extra_fields)
            return result

        def _reset_page_state():
            nonlocal current_lines, current_field, extra_fields
            current_lines = []
            current_field = None
            extra_fields = {}

        def _process_line(line: str, stripped: str):
            nonlocal page_index, current_field, stream_complete

            if stripped == '<!-- BEGIN -->':
                if page_index < 0:
                    page_index = 0
                return 'continue'

            if stripped == '<!-- END -->':
                stream_complete = True
                return 'continue'

            if stripped == '<!-- PAGE_END -->':
                if page_index >= 0 and (current_lines or extra_fields):
                    return 'yield_page'
                return 'continue'

            if page_index < 0:
                return 'continue'

            # Check for extra field header
            if field_pattern:
                field_match = field_pattern.match(stripped)
                if field_match:
                    from models import Settings
                    field_name = Settings.LEGACY_FIELD_EQUIV.get(field_match.group(1), field_match.group(1))
                    current_field = field_name
                    value = field_match.group(2).strip()
                    if value:
                        extra_fields[field_name] = value
                    return 'continue'

            if not stripped:
                return 'continue'

            if current_field:
                # Append to current extra field (multi-line)
                if current_field in extra_fields:
                    extra_fields[current_field] += "\n" + stripped
                else:
                    extra_fields[current_field] = stripped
            else:
                current_lines.append(line.rstrip())
            return 'continue'

        for chunk in self.text_provider.generate_text_stream(prompt, thinking_budget=actual_budget):
            buffer += chunk

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                stripped = line.strip()
                action = _process_line(line, stripped)

                if action == 'yield_page':
                    yield _build_page_result()
                    _reset_page_state()
                    page_index += 1

        # Process remaining buffer
        if buffer.strip():
            for line in buffer.split('\n'):
                stripped = line.strip()
                action = _process_line(line, stripped)
                if action == 'yield_page':
                    yield _build_page_result()
                    _reset_page_state()
                    page_index += 1

        # Yield last page if not yet yielded
        if page_index >= 0 and current_lines:
            yield _build_page_result()

        yield {'__stream_complete__': stream_complete}

    @staticmethod
    def _build_extra_field_pattern(field_names: list):
        """Build a compiled regex pattern that matches any extra field header."""
        if not field_names:
            return None
        escaped = '|'.join(re.escape(name) for name in field_names)
        return re.compile(rf'^({escaped})[: :]\s*(.*)')
    
    def generate_outline_text(self, outline: List[Dict]) -> str:
        """
        Convert outline to text format for prompts
        Based on demo.py gen_outline_text()
        """
        text_parts = []
        for i, item in enumerate(outline, 1):
            if "part" in item and "pages" in item:
                text_parts.append(f"{i}. {item['part']}")
            else:
                text_parts.append(f"{i}. {item.get('title', 'Untitled')}")
        result = "\n".join(text_parts)
        return dedent(result)
    
    def generate_image_prompt(self, outline: List[Dict], page: Dict,
                            page_desc: str, page_index: int,
                            has_material_images: bool = False,
                            extra_requirements: Optional[str] = None,
                            language='zh',
                            has_template: bool = True,
                            aspect_ratio: str = "16:9",
                            page_style_text: Optional[str] = None) -> str:
        """
        Generate image generation prompt for a page

        Args:
            has_template: (False=)
            page_style_text: (per-page-template  7);
                , template_style
        """
        outline_text = self.generate_outline_text(outline)
        if 'part' in page:
            current_section = page['part']
        else:
            current_section = f"{page.get('title', 'Untitled')}"

        cleaned_page_desc = self.remove_markdown_images(page_desc)

        prompt = get_image_generation_prompt(
            page_desc=cleaned_page_desc,
            outline_text=outline_text,
            current_section=current_section,
            has_material_images=has_material_images,
            extra_requirements=extra_requirements,
            language=language,
            has_template=has_template,
            page_index=page_index,
            aspect_ratio=aspect_ratio,
            page_style_text=page_style_text,
        )

        return prompt

    def review_generated_slide_image(
        self,
        image_path: str,
        generation_prompt: str,
        page_desc: str,
        page_outline: Optional[Dict] = None,
        page_index: Optional[int] = None,
    ) -> Dict:
        """Review a generated slide image before it is saved as a version."""
        prompt = dedent(f"""
        You are a strict quality-control reviewer for AI-generated presentation slide images.
        Inspect the provided image against the generation prompt used to create it.

        Reject the image if any of these problems are clearly present:
        1. Garbled, unreadable, nonsensical, or visibly corrupted text inside the slide image.
        2. Low-quality illustration or rendering, including obvious artifacts, malformed layouts, blurry key content, or amateur-looking visual style.
        3. The visual content, style, layout, or key objects are substantially inconsistent with the generation prompt.

        Accept the image if minor imperfections exist but it is usable as a presentation slide and broadly matches the request.

        Return only valid JSON in this exact shape:
        {{
          "passed": true,
          "issues": [],
          "reason": "short reason"
        }}

        Page number: {page_index if page_index is not None else ''}

        Generation prompt:
        {generation_prompt}
        """).strip()

        result = self.generate_json_with_image(prompt, image_path)
        if isinstance(result, list) and result and isinstance(result[0], dict):
            result = result[0]
        if not isinstance(result, dict):
            raise ValueError("Image quality review returned a non-object result")

        raw_passed = result.get('passed')
        if isinstance(raw_passed, bool):
            passed = raw_passed
        elif isinstance(raw_passed, (int, float)):
            passed = bool(raw_passed)
        elif isinstance(raw_passed, str):
            passed = raw_passed.strip().lower() in ('true', 'yes', 'pass', 'passed', '1')
        else:
            passed = False
        issues = result.get('issues') or []
        if not isinstance(issues, list):
            issues = [str(issues)]
        reason = str(result.get('reason') or '').strip()

        return {
            'passed': passed,
            'issues': [str(issue).strip() for issue in issues if str(issue).strip()],
            'reason': reason,
        }
    
    def generate_image(self, prompt: str, ref_image_path: Optional[str] = None, 
                      aspect_ratio: str = "16:9", resolution: str = "2K",
                      additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:
        """
        Generate image using configured image provider
        Based on gemini_genai.py gen_image()
        
        Args:
            prompt: Image generation prompt
            ref_image_path: Path to reference image (optional). If None, will generate based on prompt only.
            aspect_ratio: Image aspect ratio
            resolution: Image resolution (note: OpenAI format only supports 1K)
            additional_ref_images: , , URL  PIL Image 
        
        Returns:
            PIL Image object or None if failed
        
        Raises:
            Exception with detailed error message if generation fails
        """
        try:
            logger.debug(f"Reference image: {ref_image_path}")
            if additional_ref_images:
                logger.debug(f"Additional reference images: {len(additional_ref_images)}")
            logger.debug(f"Config - aspect_ratio: {aspect_ratio}, resolution: {resolution}")

            # Backend logic
            ref_images = []
            # Backend logic
            owned_images = []

            # Backend logic
            if ref_image_path:
                if not os.path.exists(ref_image_path):
                    raise FileNotFoundError(f"Reference image not found: {ref_image_path}")
                main_ref_image = Image.open(ref_image_path)
                ref_images.append(main_ref_image)
                owned_images.append(main_ref_image)

            # Backend logic
            if additional_ref_images:
                for ref_img in additional_ref_images:
                    if isinstance(ref_img, Image.Image):
                        # Backend logic
                        ref_images.append(ref_img)
                    elif isinstance(ref_img, str):
                        # Backend logic
                        if os.path.exists(ref_img):
                            # Backend logic
                            opened = Image.open(ref_img)
                            ref_images.append(opened)
                            owned_images.append(opened)
                        elif ref_img.startswith('http://') or ref_img.startswith('https://'):
                            # Backend logic
                            downloaded_img = self.download_image_from_url(ref_img)
                            if downloaded_img:
                                ref_images.append(downloaded_img)
                                owned_images.append(downloaded_img)
                            else:
                                logger.warning(f"Failed to download image from URL: {ref_img}, skipping...")
                        elif ref_img.startswith('/files/mineru/'):
                            # Backend logic
                            local_path = self._convert_mineru_path_to_local(ref_img)
                            if local_path and os.path.exists(local_path):
                                opened = Image.open(local_path)
                                ref_images.append(opened)
                                owned_images.append(opened)
                                logger.debug(f"Loaded MinerU image from local path: {local_path}")
                            else:
                                logger.warning(f"MinerU image file not found (with prefix matching): {ref_img}, skipping...")
                        elif ref_img.startswith('/files/'):
                            # Backend logic
                            upload_folder = get_config().UPLOAD_FOLDER
                            upload_folder_real = os.path.realpath(upload_folder)
                            relative_path = ref_img[len('/files/'):].lstrip('/\\')
                            local_path = os.path.realpath(os.path.join(upload_folder, relative_path))
                            try:
                                is_inside_upload_folder = (
                                    os.path.commonpath([local_path, upload_folder_real]) == upload_folder_real
                                )
                            except ValueError:
                                is_inside_upload_folder = False
                            if not is_inside_upload_folder:
                                logger.warning(f"Path traversal attempt blocked: {ref_img}, skipping...")
                            elif os.path.isfile(local_path):
                                opened = Image.open(local_path)
                                ref_images.append(opened)
                                owned_images.append(opened)
                                logger.debug(f"Loaded image from local path: {local_path}")
                            else:
                                logger.warning(f"Local file not found or not a file: {local_path} (from {ref_img}), skipping...")
                        else:
                            logger.warning(f"Invalid image reference: {ref_img}, skipping...")

            logger.debug(f"Calling image provider for generation with {len(ref_images)} reference images...")
            logger.debug(f"Enable image reasoning/thinking: {self.enable_image_reasoning}, budget: {self._get_image_thinking_budget()}")

            try:
                # Backend logic
                # Backend logic
                return self.image_provider.generate_image(
                    prompt=prompt,
                    ref_images=ref_images if ref_images else None,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    enable_thinking=self.enable_image_reasoning,
                    thinking_budget=self._get_image_thinking_budget()
                )
            finally:
                for img in owned_images:
                    try:
                        img.close()
                    except Exception:
                        pass

        except Exception as e:
            error_detail = f"Error generating image: {type(e).__name__}: {str(e)}"
            logger.error(error_detail, exc_info=True)
            raise Exception(error_detail) from e
    
    def edit_image(self, prompt: str, current_image_path: str,
                  aspect_ratio: str = "16:9", resolution: str = "2K",
                  original_description: str = None,
                  additional_ref_images: Optional[List[Union[str, Image.Image]]] = None) -> Optional[Image.Image]:
        """
        Edit existing image with natural language instruction
        Uses current image as reference
        
        Args:
            prompt: Edit instruction
            current_image_path: Path to current page image
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
            original_description: Original page description to include in prompt
            additional_ref_images: , , URL  PIL Image 
        
        Returns:
            PIL Image object or None if failed
        """
        # Build edit instruction with original description if available
        edit_instruction = get_image_edit_prompt(
            edit_instruction=prompt,
            original_description=original_description
        )
        return self.generate_image(edit_instruction, current_image_path, aspect_ratio, resolution, additional_ref_images)
    
    def parse_description_to_outline(self, project_context: ProjectContext, language='zh') -> List[Dict]:
        """
        
        
        Args:
            project_context: , 
        
        Returns:
            List of outline items (may contain parts with pages or direct pages)
        """
        parse_prompt = get_description_to_outline_prompt(project_context, language)
        outline = self.generate_json(parse_prompt, thinking_budget=1000)
        return outline
    
    def parse_description_to_page_descriptions(self, project_context: ProjectContext, 
                                               outline: List[Dict],
                                               language='zh') -> List[str]:
        """
        
        
        Args:
            project_context: , 
            outline: 
        
        Returns:
            List of page descriptions (strings), one for each page in the outline
        """
        split_prompt = get_description_split_prompt(project_context, outline, language)
        descriptions = self.generate_json(split_prompt, thinking_budget=1000)
        
        # Backend logic
        if isinstance(descriptions, list):
            return [str(desc) for desc in descriptions]
        else:
            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))
    
    def refine_outline(self, current_outline: List[Dict], user_requirement: str,
                      project_context: ProjectContext,
                      previous_requirements: Optional[List[str]] = None,
                      language='zh') -> List[Dict]:
        """
        
        
        Args:
            current_outline: 
            user_requirement: 
            project_context: , 
            previous_requirements:  () 
        
        Returns:
            
        """
        refinement_prompt = get_outline_refinement_prompt(
            current_outline=current_outline,
            user_requirement=user_requirement,
            project_context=project_context,
            previous_requirements=previous_requirements,
            language=language
        )
        outline = self.generate_json(refinement_prompt, thinking_budget=1000)
        return outline
    
    def refine_descriptions(self, current_descriptions: List[Dict], user_requirement: str,
                           project_context: ProjectContext,
                           outline: List[Dict] = None,
                           previous_requirements: Optional[List[str]] = None,
                           language='zh') -> List[Dict]:
        """
        

        Args:
            current_descriptions: ,  {index, title, description_content}
            user_requirement: 
            project_context: , 
            outline:  () 
            previous_requirements:  () 

        Returns:
            Danh sách mô tả trang sau khi chỉnh sửa, mỗi phần tử là {'text': ..., 'extra_fields': {...}}. 
            , . 
        """
        refinement_prompt = get_descriptions_refinement_prompt(
            current_descriptions=current_descriptions,
            user_requirement=user_requirement,
            project_context=project_context,
            outline=outline,
            previous_requirements=previous_requirements,
            language=language
        )
        descriptions = self.generate_json(refinement_prompt, thinking_budget=1000)

        if not isinstance(descriptions, list):
            raise ValueError("Expected a list of page descriptions, but got: " + str(type(descriptions)))

        field_names = self._get_parseable_field_names()
        results = []
        for desc in descriptions:
            # Backend logic
            # Backend logic
            if isinstance(desc, dict):
                lines = []
                for k, v in desc.items():
                    if not v:
                        continue
                    value = '\n'.join(str(i) for i in v) if isinstance(v, list) else str(v)
                    lines.append(f'{k}: {value}')
                desc_text = '\n'.join(lines)
            else:
                desc_text = str(desc)
            text, extra_fields = self._parse_extra_fields(desc_text, field_names)
            result = {'text': text}
            if extra_fields:
                result['extra_fields'] = extra_fields
            results.append(result)
        return results

    def extract_page_content(self, markdown_text: str, language: str = 'zh') -> Dict:
        """
         fileparser  markdown 

        Args:
            markdown_text:  PDF  markdown 
            language: 

        Returns:
            Dict with keys: title, points, description
        """
        prompt = get_ppt_page_content_extraction_prompt(markdown_text, language=language)
        result = self.generate_json(prompt, thinking_budget=1000)

        # Ensure required fields exist
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict, got {type(result)}")

        result.setdefault('title', '')
        result.setdefault('points', [])
        result.setdefault('description', '')

        return result

    def _generate_text_from_image(self, prompt: str, image_path: str) -> str:
        """Helper to generate text from a prompt and an image, using caption_provider."""
        actual_budget = self._get_text_thinking_budget()
        provider = self.caption_provider

        if hasattr(provider, 'generate_with_image'):
            response_text = provider.generate_with_image(
                prompt=prompt,
                image_path=image_path,
                thinking_budget=actual_budget
            )
        elif hasattr(provider, 'generate_text_with_images'):
            response_text = provider.generate_text_with_images(
                prompt=prompt,
                images=[image_path],
                thinking_budget=actual_budget
            )
        else:
            raise ValueError("caption_provider không hỗ trợ đầu vào hình ảnh")

        return response_text.strip()

    def generate_layout_caption(self, image_path: str) -> str:
        """ Backend docstring """
        return self._generate_text_from_image(get_layout_caption_prompt(), image_path)

    def extract_style_description(self, image_path: str) -> str:
        """ Backend docstring """
        return self._generate_text_from_image(get_style_extraction_prompt(), image_path)

    def generate_style_from_content(self, content: str, language: str = 'zh') -> str:
        """ Backend docstring """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty for style generation")
        prompt = get_style_from_content_prompt(content=content, language=language)
        response_text = self.text_provider.generate_text(prompt, thinking_budget=1000)
        return response_text.strip()

    # =========================================================================
    # Per-page template (PRD §5.3 / §8) — analysis + auto-match
    # =========================================================================

    def analyze_template(self, image_path: str, language: str = 'zh') -> Dict:
        """
        Analyze a template image into the 9-field schema (PRD §5.3).

        Reuses generate_json_with_image (3x soft retry). On model-declared
        failure returns {"error": "not_a_slide"}; on retry exhaustion raises
        json.JSONDecodeError.
        """
        prompt = get_template_analysis_prompt(language=language)
        result = self.generate_json_with_image(prompt, image_path)
        if isinstance(result, dict):
            return result
        raise ValueError(f"analyze_template expected dict, got {type(result).__name__}")

    def auto_match_templates(self, project_id: str, language: str = 'zh',
                              overwrite_existing: bool = True,
                              preserve_non_empty: bool = False) -> List[Dict]:
        """
        Auto-match every page in a project to a template (decision 5).

        - Candidates: ProjectTemplateAsset with analysis_status == 'completed'
          (decision 2 — failed/pending assets stay manual-only)
        - Pages: every Page with non-empty description_content
        - Batching: <=50 pages AND <=20 templates → single LLM call;
          otherwise 30-page batches, results concatenated in order
        - preserve_non_empty=True skips pages that already have template_asset_id

        Returns rows shaped like the prompt schema; caller (task) commits to DB.
        """
        from models import Project, Page, ProjectTemplateAsset

        project = Project.query.get(project_id)
        if not project:
            raise ValueError(f"project not found: {project_id}")

        templates_q = ProjectTemplateAsset.query.filter_by(
            project_id=project_id, analysis_status='completed'
        ).order_by(ProjectTemplateAsset.sort_order.asc()).all()
        if not templates_q:
            raise ValueError("NO_ANALYZED_TEMPLATES")

        pages_q = Page.query.filter_by(project_id=project_id).order_by(
            Page.order_index.asc()).all()

        eligible_pages = []
        for p in pages_q:
            desc = p.get_description_content() if hasattr(p, 'get_description_content') else None
            if not desc:
                continue
            if preserve_non_empty and p.template_asset_id:
                continue
            eligible_pages.append((p, desc))

        if not eligible_pages:
            return []

        templates_payload = [self._trim_template_for_match(t) for t in templates_q]
        pages_payload = [self._trim_page_for_match(p, desc) for p, desc in eligible_pages]

        BATCH_PAGES, BATCH_TEMPLATES = 50, 20
        if len(pages_payload) <= BATCH_PAGES and len(templates_payload) <= BATCH_TEMPLATES:
            batches = [pages_payload]
        else:
            batches = [pages_payload[i:i + 30] for i in range(0, len(pages_payload), 30)]

        all_results: List[Dict] = []
        for batch in batches:
            prompt = get_template_auto_match_prompt(
                templates=templates_payload, pages=batch, language=language)
            result = self.generate_json(prompt)
            if isinstance(result, dict):
                result = [result]
            if not isinstance(result, list):
                raise ValueError(f"auto_match_templates expected list, got {type(result).__name__}")
            all_results.extend(result)

        return all_results

    @staticmethod
    def _trim_template_for_match(asset) -> Dict:
        """PRD §5.3 → matcher-friendly subset (decision 5 trimming)."""
        analysis = asset.get_analysis() if hasattr(asset, 'get_analysis') else {}
        analysis = analysis or {}
        keywords = (analysis.get('style_keywords') or [])[:5]
        notes = (asset.analysis_notes or analysis.get('notes') or '')[:200]
        return {
            'asset_id': asset.id,
            'sort_order': asset.sort_order,
            'user_label': asset.user_label or '',
            'extracted_text': (analysis.get('extracted_text') or '')[:100],
            'template_role': analysis.get('template_role'),
            'layout_structure': analysis.get('layout_structure'),
            'content_capacity': analysis.get('content_capacity'),
            'visual_density': analysis.get('visual_density'),
            'style_keywords': keywords,
            'notes': notes,
        }

    @staticmethod
    def _trim_page_for_match(page, desc: Dict) -> Dict:
        """Page → matcher-friendly subset (decision 5: title + 100-char summary + density)."""
        title = (desc.get('title') or '').strip()
        text_blocks = desc.get('text_content') or []
        if isinstance(text_blocks, list):
            joined = ' / '.join(str(t) for t in text_blocks if t)
        else:
            joined = str(text_blocks)
        if not title and not joined:
            # Free-text description schema: {'text': ..., 'extra_fields': {...}}
            lines = [
                ln.strip() for ln in str(desc.get('text') or '').splitlines()
                if ln.strip() and not ln.strip().startswith('---')
                and not ln.strip().startswith('![')
            ]
            if lines:
                title = lines[0].strip('*').strip()
                joined = ' / '.join(lines[1:])
        summary = joined[:100]
        extra_fields = desc.get('extra_fields') or {}
        layout_hint = ' / '.join(
            f'{k}: {v}' for k, v in extra_fields.items()
            if v and k != 'Ghi chú thuyết trình'
        )[:300] if isinstance(extra_fields, dict) else ''
        body_len = len(joined)
        if body_len < 200:
            density = 'low'
        elif body_len < 600:
            density = 'medium'
        else:
            density = 'high'
        row = {
            'page_id': page.id,
            'order_index': page.order_index,
            'title': title,
            'summary': summary,
            'content_density': density,
        }
        if layout_hint:
            row['layout_hint'] = layout_hint
        return row