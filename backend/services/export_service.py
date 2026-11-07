"""
Export Service - handles PPTX and PDF export
Based on demo.py create_pptx_from_images()
"""
import math
import os
import json
import logging
import random
import re
import tempfile
import time
import base64
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from textwrap import dedent
from dataclasses import dataclass, field
from pptx import Presentation
from pptx.util import Inches
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
from PIL import Image
import io
import tempfile
import img2pdf
import fitz  # PyMuPDF
from utils.pptx_math import latex_to_display_text, looks_like_latex_math
logger = logging.getLogger(__name__)

# Backend logic
ELEMENT_PROGRESS_INTERVAL = 50


class ExportError(Exception):
    """
    

     fail_fast=True , , 
    . 
    """
    def __init__(
        self,
        message: str,
        error_type: str = 'unknown',
        details: Dict[str, Any] = None,
        help_text: str = None,
        error_code: str = 'EXPORT_FAILED',
        stage: str = None,
    ):
        """
        Args:
            message: 
            error_type:  (style_extraction, text_render, image_add, inpaint, config, service)
            details: 
            help_text: 
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.help_text = help_text or self._get_default_help_text(error_type)
        self.error_code = error_code
        self.stage = stage or self.details.get('stage') or 'export'

    def _get_default_help_text(self, error_type: str) -> str:
        """ Backend docstring """
        help_texts = {
            'style_extraction': 'Trích xuất kiểu thất bại có thể do BaiduOCR APIvấn đề cấu hình. Vui lòng kiểm traCài đặt dự án -> Cài đặt xuấtcấu hình trong, hoặc thử chuyển sangMinerUtrích xuấtphương pháp. ',
            'text_render': 'Kết xuất văn bản thất bại có thể do lỗi phông chữ hoặc bảng mã. Vui lòng kiểm tra nội dung trang có chứa ký tự đặc biệt hay không. ',
            'image_add': 'Thêm hình ảnh thất bại có thể do tệp ảnh bị hỏng hoặc sai đường dẫn. Vui lòng thử tạo lại hình ảnh của trang này. ',
            'inpaint': 'Phục hồi nền thất bại có thể doAPIvấn đề cấu hình. Vui lòng kiểm traCài đặt dự án -> Cài đặt xuấtcấu hình phương thức lấy ảnh nền trong. ',
            'config': 'Lỗi cấu hình. Vui lòng kiểm traCài đặt dự án -> Cài đặt xuấtcấu hình liên quan trong. ',
            'service': 'dịch vụ không khả dụng. Vui lòng thử lại sau hoặc liên hệ quản trị viên. ',
        }
        return help_texts.get(error_type, 'Nếu sự cố vẫn tiếp diễn, Có thể tạiCài đặt dự án -> Cài đặt xuấtbật trongtrả về kết quả từng phầnđể bỏ qua lỗi và tiếp tục xuất. ')

    def to_dict(self) -> Dict[str, Any]:
        """ Backend docstring """
        return {
            'message': self.message,
            'error_type': self.error_type,
            'error_code': self.error_code,
            'stage': self.stage,
            'details': self.details,
            'help_text': self.help_text
        }


@dataclass
class ExportWarnings:
    """
    
    
    , 
    """
    # Backend logic
    style_extraction_failed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Backend logic
    text_render_failed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Backend logic
    image_add_failed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Backend logic
    json_parse_failed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Backend logic
    other_warnings: List[str] = field(default_factory=list)
    
    def add_style_extraction_failed(self, element_id: str, reason: str):
        """ Backend docstring """
        self.style_extraction_failed.append({
            'element_id': element_id,
            'reason': reason
        })
    
    def add_text_render_failed(self, text: str, reason: str):
        """ Backend docstring """
        self.text_render_failed.append({
            'text': text[:50] + '...' if len(text) > 50 else text,
            'reason': reason
        })
    
    def add_image_failed(self, path: str, reason: str):
        """ Backend docstring """
        self.image_add_failed.append({
            'path': path,
            'reason': reason
        })
    
    def add_json_parse_failed(self, context: str, reason: str):
        """ Backend docstring """
        self.json_parse_failed.append({
            'context': context,
            'reason': reason
        })
    
    def add_warning(self, message: str):
        """ Backend docstring """
        self.other_warnings.append(message)
    
    def has_warnings(self) -> bool:
        """ Backend docstring """
        return bool(
            self.style_extraction_failed or 
            self.text_render_failed or 
            self.image_add_failed or
            self.json_parse_failed or
            self.other_warnings
        )
    
    def to_summary(self) -> List[str]:
        """ Backend docstring """
        summary = []
        
        if self.style_extraction_failed:
            summary.append(f"{len(self.style_extraction_failed)} phần tử văn bản trích xuất kiểu thất bại")
        
        if self.text_render_failed:
            summary.append(f"{len(self.text_render_failed)} phần tử văn bản kết xuất thất bại")
        
        if self.image_add_failed:
            summary.append(f"{len(self.image_add_failed)} hình ảnh thêm thất bại")
        
        if self.json_parse_failed:
            summary.append(f"{len(self.json_parse_failed)} lần AI Phân tích phản hồi thất bại")
        
        for warning in self.other_warnings[:5]:  # Backend logic
            summary.append(f"{warning}")
        
        if len(self.other_warnings) > 5:
            summary.append(f" ...còn {len(self.other_warnings) - 5} cảnh báo khác")
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """ Backend docstring """
        return {
            'style_extraction_failed': self.style_extraction_failed,
            'text_render_failed': self.text_render_failed,
            'image_add_failed': self.image_add_failed,
            'json_parse_failed': self.json_parse_failed,
            'other_warnings': self.other_warnings,
            'total_warnings': (
                len(self.style_extraction_failed) + 
                len(self.text_render_failed) + 
                len(self.image_add_failed) +
                len(self.json_parse_failed) +
                len(self.other_warnings)
            )
        }


def _get_page_size_inches(aspect_ratio: str = '16:9', base: float = 10.0) -> Tuple[float, float]:
    """Return (width, height) in inches for a given aspect ratio string."""
    try:
        w, h = (float(x) for x in aspect_ratio.split(':'))
        if not (math.isfinite(w) and math.isfinite(h) and w > 0 and h > 0):
            raise ValueError(f"invalid dimensions: {w}:{h}")
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid aspect ratio '{aspect_ratio}', falling back to 16:9: {e}")
        w, h = 16.0, 9.0
    if w >= h:
        return base, base * h / w
    else:
        return base * w / h, base


class ExportService:
    """Service for exporting presentations"""

    PPTX_TRANSITION_EFFECTS = {
        'fade',
        'page_turn',
        'push',
        'wipe',
        'split',
        'blinds',
        'checker',
        'wheel',
    }

    @staticmethod
    def _apply_slide_transition(slide, effect: str) -> None:
        """Add a PowerPoint slide transition node to a slide XML element."""
        transition = OxmlElement('p:transition')
        transition.set('spd', 'med')

        if effect == 'fade':
            transition.append(OxmlElement('p:fade'))
        elif effect == 'page_turn':
            cover = OxmlElement('p:cover')
            cover.set('dir', 'l')
            transition.append(cover)
        elif effect == 'push':
            push = OxmlElement('p:push')
            push.set('dir', 'l')
            transition.append(push)
        elif effect == 'wipe':
            wipe = OxmlElement('p:wipe')
            wipe.set('dir', 'l')
            transition.append(wipe)
        elif effect == 'split':
            split = OxmlElement('p:split')
            split.set('orient', 'horz')
            split.set('dir', 'out')
            transition.append(split)
        elif effect == 'blinds':
            blinds = OxmlElement('p:blinds')
            blinds.set('dir', 'vert')
            transition.append(blinds)
        elif effect == 'checker':
            checker = OxmlElement('p:checker')
            checker.set('dir', 'horz')
            transition.append(checker)
        elif effect == 'wheel':
            wheel = OxmlElement('p:wheel')
            wheel.set('spokes', '1')
            transition.append(wheel)
        else:
            return

        slide_element = slide._element
        existing = slide_element.find(qn('p:transition'))
        if existing is not None:
            slide_element.remove(existing)

        clr_map_ovr = slide_element.find(qn('p:clrMapOvr'))
        if clr_map_ovr is not None:
            insert_at = slide_element.index(clr_map_ovr) + 1
        else:
            c_sld = slide_element.find(qn('p:cSld'))
            insert_at = slide_element.index(c_sld) + 1 if c_sld is not None else 0

        slide_element.insert(insert_at, transition)

    # Backend logic
    # Backend logic
    # Backend logic
    # Backend logic

    @staticmethod
    def _classify_external_failure(message: str) -> Dict[str, Any]:
        """Classify an upstream failure without collapsing every case into a timeout."""
        lowered = str(message or '').lower()

        classifications = (
            (
                'unsupported_model',
                (
                    'không hỗ trợ đầu vào hình ảnh', 'does not support image', 'support image input',
                    'unsupported image', 'image_url is only supported',
                ),
                'MODEL_UNSUPPORTED',
                'Mô hình nhận diện ảnh không hỗ trợ đầu vào hình ảnh',
                False,
            ),
            (
                'configuration_missing',
                (
                    'api key is required', 'api_key is required',
                    'google_api_key (from database settings or environment) is required',
                    'openai_api_key (from database settings or environment) is required',
                    'not configured', 'missing api key', 'chưa cấu hình', 'thiếu api key',
                ),
                'CONFIGURATION_MISSING',
                'Thiếu cấu hình dịch vụ nhận diện ảnh',
                False,
            ),
            (
                'authentication',
                (
                    '401', '403', 'unauthorized', 'forbidden', 'authentication',
                    'invalid api key', 'invalid_api_key', 'api key not valid',
                    'token expired', 'Phiên đăng nhập đã hết hạn',
                ),
                'AUTHENTICATION',
                'Xác thực dịch vụ nhận diện ảnh thất bại hoặc phiên đăng nhập đã hết hạn',
                False,
            ),
            (
                'rate_limit',
                ('429', 'rate limit', 'too many requests', 'qps request limit', 'Yêu cầu quá thường xuyên'),
                'RATE_LIMIT',
                'Dịch vụ nhận diện ảnh bị giới hạn tần suất (rate limit)',
                True,
            ),
            (
                'timeout',
                ('timeout', 'timed out', 'deadline exceeded', 'gateway timeout'),
                'TIMEOUT',
                'Yêu cầu dịch vụ nhận diện ảnh đã quá thời gian chờ',
                True,
            ),
            (
                'network',
                (
                    'ssl', 'connection aborted', 'connection reset', 'connection error',
                    'network error', 'unexpected_eof', 'eof occurred', 'chunkedencoding',
                    'remote end closed', 'max retries exceeded', 'connection refused',
                ),
                'NETWORK',
                'Mất kết nối mạng khi kết nối tới dịch vụ nhận diện ảnh',
                True,
            ),
            (
                'invalid_response',
                (
                    'json', 'không thể phân tích', 'invalid control character', 'empty response',
                    'phản hồi rỗng', 'expected dict',
                ),
                'INVALID_RESPONSE',
                'Mô hình nhận diện ảnh trả về nội dung không thể phân tích',
                True,
            ),
            (
                'incomplete_response',
                ('Chưa trả về kết quả đầy đủ', 'missing result', 'incomplete'),
                'INCOMPLETE_RESPONSE',
                'Mô hình nhận diện ảnh trả về kết quả không đầy đủ',
                True,
            ),
            (
                'upstream_service',
                ('500', '502', '503', '504', 'service unavailable', 'bad gateway'),
                'UPSTREAM_SERVICE',
                'Dịch vụ nhận diện ảnh tạm thời không khả dụng',
                True,
            ),
        )

        for reason, needles, code_suffix, summary, retryable in classifications:
            if any(needle in lowered for needle in needles):
                return {
                    'reason': reason,
                    'code_suffix': code_suffix,
                    'summary': summary,
                    'retryable': retryable,
                }

        return {
            'reason': 'unknown',
            'code_suffix': 'FAILED',
            'summary': 'Gọi dịch vụ nhận diện ảnh thất bại',
            'retryable': False,
        }

    @staticmethod
    def _safe_technical_message(message: str) -> str:
        """Keep a short diagnostic hint while removing common credential shapes."""
        text = str(message or '').strip()
        text = re.sub(
            r'(?i)(authorization|api[_ -]?key|access[_ -]?token|refresh[_ -]?token)'
            r'(\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+',
            r'\1\2***',
            text,
        )
        text = re.sub(r'(?i)\bbearer\s+[a-z0-9._~+/=-]+', 'Bearer ***', text)
        text = re.sub(r'\b(?:sk|AIza|ya29\.)[-_A-Za-z0-9.]{12,}\b', '***', text)
        return text[:500]

    @staticmethod
    def _style_extractor_context(text_attribute_extractor: Any) -> Dict[str, Any]:
        ai_service = getattr(text_attribute_extractor, 'ai_service', None)
        provider = getattr(ai_service, 'caption_provider', None)
        model = getattr(ai_service, 'caption_model', None) or getattr(provider, 'model', None)
        context: Dict[str, Any] = {}
        if provider is not None:
            context['provider'] = provider.__class__.__name__
        if model:
            context['model'] = str(model)
        timeout_seconds = getattr(provider, 'request_timeout_seconds', None)
        max_attempts = getattr(provider, 'max_attempts', None)
        if timeout_seconds is not None:
            context['request_timeout_seconds'] = timeout_seconds
        if max_attempts is not None:
            context['max_attempts'] = max_attempts
        return context

    @staticmethod
    def _build_style_extraction_error(
        message: str,
        *,
        element_id: Optional[str] = None,
        text_content: Optional[str] = None,
        page_idx: Optional[int] = None,
        text_attribute_extractor: Any = None,
        operation: str = 'style_extraction',
    ) -> ExportError:
        classification = ExportService._classify_external_failure(message)
        details: Dict[str, Any] = {
            'stage': 'style_extraction',
            'operation': operation,
            'reason': classification['reason'],
            'retryable': classification['retryable'],
            'technical_message': ExportService._safe_technical_message(message),
            **ExportService._style_extractor_context(text_attribute_extractor),
        }
        if element_id:
            details['element_id'] = element_id
        if text_content:
            details['text_content'] = text_content[:50]
        if page_idx is not None:
            details['page'] = page_idx + 1

        reason = classification['reason']
        if reason == 'unsupported_model':
            help_text = (
                'Hiện được dùng để trích xuất kiểu ảnh caption/image_caption Mô hình không hỗ trợ đầu vào hình ảnh. '
                'Vui lòng đổi sang mô hình hỗ trợ đầu vào thị giác trong phần Cài đặt, hoặc kiểm tra OpenAI trong định dạng image caption provider / model Cấu hình. '
            )
        elif reason == 'configuration_missing':
            help_text = (
                'Dịch vụ nhận diện ảnh thiếu cấu hình cần thiết. Vui lòng kiểm tra trong phần Cài đặt image caption provider, mô hình và API Key, '
                'Lưu và xác minh cấu hình rồi xuất lại. '
            )
        elif reason == 'authentication':
            help_text = (
                'Thông tin xác thực của dịch vụ nhận diện ảnh không hợp lệ hoặc đã hết hạn. Vui lòng kiểm tra trong phần Cài đặt image caption provider, '
                'Nếu sử dụng Codex, vui lòng đăng nhập lại OpenAI tài khoản. '
            )
        elif reason == 'rate_limit':
            help_text = (
                'Dịch vụ nhận diện ảnh hiện đang có quá nhiều yêu cầu. Hệ thống đã hoàn tất tự động thử lại; Vui lòng xuất lại sau, '
                'hoặc giảm số trang trong một lần xuất. '
            )
        elif reason in {'timeout', 'network', 'upstream_service'}:
            help_text = (
                'Dịch vụ nhận diện hình ảnh tạm thời không phản hồi ổn định ở giai đoạn trích xuất kiểu văn bản. vui lòng thử lại sau; '
                'Nếu lặp lại nhiều lần, vui lòng kiểm tra kết nối mạng, proxy và image caption provider trạng thái. '
                'Nếu chỉ muốn nhận trước kết quả có thể chỉnh sửa, Cũng có thể trongCài đặt dự án -> Cài đặt xuấtbật trongtrả về kết quả từng phần. '
            )
        elif reason in {'invalid_response', 'incomplete_response'}:
            help_text = (
                'Mô hình nhận diện ảnh trả về kết quả có cấu trúc không đầy đủ hoặc không thể phân tích. Vui lòng thử lại, hoặc chuyển sang mô hình thị giác ổn định hơn; '
                'Cũng có thể bậttrả về kết quả từng phầnđể bỏ qua kiểu dáng bị lỗi. '
            )
        else:
            help_text = (
                'Trích xuất kiểu văn bản dựa vào mô hình thị giác để phân tích ảnh chụp văn bản. Vui lòng kiểm tra image caption provider, tên mô hình và API quyền; '
                'Nếu chỉ muốn nhận trước kết quả có thể chỉnh sửa, Cũng có thể trongCài đặt dự án -> Cài đặt xuấtbật trongtrả về kết quả từng phần. '
            )

        return ExportError(
            message=f"Trích xuất kiểu văn bản thất bại: {classification['summary']}",
            error_type='style_extraction',
            details=details,
            help_text=help_text,
            error_code=f"EXPORT_STYLE_{classification['code_suffix']}",
            stage='style_extraction',
        )

    @staticmethod
    def _build_unexpected_export_error(message: str, stage: str) -> ExportError:
        classification = ExportService._classify_external_failure(message)
        is_external = classification['reason'] != 'unknown'
        summary = classification['summary'] if is_external else 'Đã xảy ra lỗi nội bộ trong quá trình xuất'
        details = {
            'stage': stage or 'export',
            'reason': classification['reason'],
            'retryable': classification['retryable'],
            'technical_message': ExportService._safe_technical_message(message),
        }
        if classification['reason'] == 'configuration_missing':
            help_text = (
                'Vui lòng bổ sung trong phần Cài đặt image caption provider, mô hình và API Key, Lưu và xác minh cấu hình rồi xuất lại. '
            )
        else:
            help_text = (
                'Vui lòng kiểm tra dịch vụ tương ứng theo giai đoạn lỗi rồi thử lại. Nếu chỉ muốn nhận trước kết quả có thể chỉnh sửa, '
                'Có thể tạiCài đặt dự án -> Cài đặt xuấtbật trongtrả về kết quả từng phần. '
            )
        return ExportError(
            message=f"{stage or ''}: {summary}",
            error_type='service' if is_external else 'unknown',
            details=details,
            help_text=help_text,
            error_code=f"EXPORT_{classification['code_suffix']}" if is_external else 'EXPORT_INTERNAL_ERROR',
            stage=stage or 'export',
        )

    @staticmethod
    def _build_text_render_error(
        message: str,
        *,
        text: str,
        bbox: List[int],
        element_kind: str,
    ) -> ExportError:
        return ExportError(
            message=f"Ghi nội dung thất bại: Không thể thêm{element_kind}",
            error_type='text_render',
            details={
                'stage': 'text_render',
                'element_kind': element_kind,
                'text': text[:50],
                'bbox': bbox,
                'retryable': False,
                'technical_message': ExportService._safe_technical_message(message),
            },
            help_text='Vui lòng kiểm tra ký tự đặc biệt trong phần tử bị lỗi, công thức hoặc phông chữ; Cũng có thể bậttrả về kết quả từng phầnbỏ qua phần tử này. ',
            error_code='EXPORT_TEXT_RENDER_FAILED',
            stage='text_render',
        )
    
    @staticmethod
    def create_pptx_from_images(
        image_paths: List[str],
        output_file: str = None,
        aspect_ratio: str = '16:9',
        transition_effects: Optional[List[str]] = None,
    ) -> bytes:
        """
        Create PPTX file from image paths
        Based on demo.py create_pptx_from_images()
        
        Args:
            image_paths: List of absolute paths to images
            output_file: Optional output file path (if None, returns bytes)
        
        Returns:
            PPTX file as bytes if output_file is None
        """
        # Create presentation
        prs = Presentation()
        
        # Set author/date metadata for exported PPTX
        try:
            core = prs.core_properties
            now = datetime.now(timezone.utc)
            core.author = "banana-slides"
            core.last_modified_by = "banana-slides"
            core.created = now
            core.modified = now
            core.last_printed = None
        except Exception as e:
            logger.warning(f"Failed to set core properties: {e}")
        
        # Set slide dimensions based on aspect ratio
        page_w, page_h = _get_page_size_inches(aspect_ratio)
        prs.slide_width = Inches(page_w)
        prs.slide_height = Inches(page_h)
        
        valid_transition_effects = [
            effect for effect in (transition_effects or [])
            if effect in ExportService.PPTX_TRANSITION_EFFECTS
        ]
        transition_effect_queue: List[str] = []

        # Add each image as a slide
        for image_path in image_paths:
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                continue
            
            # Add blank slide layout (layout 6 is typically blank)
            blank_slide_layout = prs.slide_layouts[6]
            slide = prs.slides.add_slide(blank_slide_layout)
            
            # Add image to fill entire slide
            slide.shapes.add_picture(
                image_path,
                left=0,
                top=0,
                width=prs.slide_width,
                height=prs.slide_height
            )

            if valid_transition_effects:
                if not transition_effect_queue:
                    transition_effect_queue = valid_transition_effects[:]
                    random.shuffle(transition_effect_queue)
                ExportService._apply_slide_transition(
                    slide,
                    transition_effect_queue.pop(),
                )
        
        # Save or return bytes
        if output_file:
            prs.save(output_file)
            return None
        else:
            # Save to bytes
            pptx_bytes = io.BytesIO()
            prs.save(pptx_bytes)
            pptx_bytes.seek(0)
            return pptx_bytes.getvalue()
    
    @staticmethod
    def create_pdf_from_images(image_paths: List[str], output_file: str = None, aspect_ratio: str = '16:9') -> Optional[bytes]:
        """
        Create PDF file from image paths using img2pdf (low memory usage)

        Args:
            image_paths: List of absolute paths to images
            output_file: Optional output file path (if None, returns bytes)

        Returns:
            PDF file as bytes if output_file is None, otherwise None
        """
        # Validate images exist and log warnings for missing files
        valid_paths = []
        for p in image_paths:
            if os.path.exists(p):
                valid_paths.append(p)
            else:
                logger.warning(f"Image not found and will be skipped for PDF export: {p}")

        if not valid_paths:
            raise ValueError("No valid images found for PDF export")

        try:
            logger.info(f"Using img2pdf for PDF export ({len(valid_paths)} pages, low memory mode)")

            page_w, page_h = _get_page_size_inches(aspect_ratio)
            layout_fun = img2pdf.get_layout_fun(
                pagesize=(img2pdf.in_to_pt(page_w), img2pdf.in_to_pt(page_h)),
                fit=img2pdf.FitMode.fill,
            )

            # Convert images to PDF
            pdf_bytes = img2pdf.convert(valid_paths, layout_fun=layout_fun)

            # Add metadata
            pdf_bytes = ExportService._add_pdf_metadata(pdf_bytes)

            if output_file:
                with open(output_file, "wb") as f:
                    f.write(pdf_bytes)
                return None
            else:
                return pdf_bytes
        except (img2pdf.ImageOpenError, ValueError, IOError) as e:
            logger.warning(f"img2pdf conversion failed: {e}. Falling back to Pillow (high memory usage).")
            return ExportService.create_pdf_from_images_pillow(valid_paths, output_file, aspect_ratio)

    @staticmethod
    def _add_pdf_metadata(pdf_bytes: bytes) -> bytes:
        """Add author metadata to PDF (including XMP for Windows compatibility)"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            doc.set_metadata({
                "author": "banana-slides",
                "producer": "banana-slides",
                "creator": "banana-slides"
            })

            now = datetime.now(timezone.utc)
            iso_time = now.isoformat()

            content_hash = hashlib.md5(pdf_bytes[:1024]).hexdigest()

            xmp = dedent(f'''\
                <?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
                <x:xmpmeta xmlns:x="adobe:ns:meta/">
                  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
                    <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">
                      <dc:creator><rdf:Seq><rdf:li>banana-slides</rdf:li></rdf:Seq></dc:creator>
                    </rdf:Description>
                    <rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">
                      <pdf:Producer>banana-slides</pdf:Producer>
                    </rdf:Description>
                    <rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/">
                      <xmp:CreatorTool>banana-slides</xmp:CreatorTool>
                      <xmp:CreateDate>{iso_time}</xmp:CreateDate>
                      <xmp:MetadataDate>{iso_time}</xmp:MetadataDate>
                    </rdf:Description>
                    <rdf:Description rdf:about="" xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/">
                      <xmpMM:DocumentID>uuid:{content_hash}</xmpMM:DocumentID>
                    </rdf:Description>
                  </rdf:RDF>
                </x:xmpmeta>
                <?xpacket end="w"?>''')
            doc.set_xml_metadata(xmp)

            return doc.tobytes()
        except Exception as e:
            logger.warning(f"Failed to add PDF metadata: {e}")
            return pdf_bytes

    @staticmethod
    def create_pdf_from_images_pillow(image_paths: List[str], output_file: str = None, aspect_ratio: str = '16:9') -> Optional[bytes]:
        """
        Create PDF file from image paths using Pillow (original method)

        Note: This method loads all images into memory at once.
        For large projects (50+ pages with 20MB/page), use create_pdf_from_images instead.

        Args:
            image_paths: List of absolute paths to images
            output_file: Optional output file path (if None, returns bytes)

        Returns:
            PDF file as bytes if output_file is None, otherwise None
        """
        images = []
        page_w, page_h = _get_page_size_inches(aspect_ratio)

        # Load all images
        for image_path in image_paths:
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                continue

            img = Image.open(image_path)

            # Convert to RGB if necessary (PDF requires RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Set DPI so PDF page matches target dimensions
            img.info['dpi'] = (img.width / page_w, img.height / page_h)

            images.append(img)

        if not images:
            raise ValueError("No valid images found for PDF export")

        # Save as PDF
        if output_file:
            images[0].save(
                output_file,
                save_all=True,
                append_images=images[1:],
                format='PDF'
            )
            return None
        else:
            # Save to bytes
            pdf_bytes = io.BytesIO()
            images[0].save(
                pdf_bytes,
                save_all=True,
                append_images=images[1:],
                format='PDF'
            )
            pdf_bytes.seek(0)
            return ExportService._add_pdf_metadata(pdf_bytes.getvalue())
       
    @staticmethod
    def _add_mineru_text_to_slide(builder, slide, text_item: Dict[str, Any], scale_x: float = 1.0, scale_y: float = 1.0):
        """
        Add text item from MinerU to slide
        
        Args:
            builder: PPTXBuilder instance
            slide: Target slide
            text_item: Text item from MinerU content_list
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor
        """
        text = text_item.get('text', '').strip()
        if not text:
            return
        
        bbox = text_item.get('bbox')
        if not bbox or len(bbox) != 4:
            logger.warning(f"Invalid bbox for text item: {text_item}")
            return
        
        original_bbox = bbox.copy()
        
        # Apply scale factors to bbox
        x0, y0, x1, y1 = bbox
        bbox = [
            int(x0 * scale_x),
            int(y0 * scale_y),
            int(x1 * scale_x),
            int(y1 * scale_y)
        ]
        
        if scale_x != 1.0 or scale_y != 1.0:
            logger.debug(f"Text bbox scaled: {original_bbox} -> {bbox} (scale: {scale_x:.3f}x{scale_y:.3f})")
        
        # Determine text level (only used for styling like bold, NOT for font size)
        # Font size is purely calculated from bbox dimensions
        item_type = text_item.get('type', 'text')
        text_level = text_item.get('text_level')
        
        # Map to level for styling purposes (bold titles)
        if item_type == 'title' or text_level == 1:
            level = 'title'  # Will be bold
        else:
            level = 'default'
        
        # Add text element
        # Note: text_level is only used for bold styling, not font size calculation
        try:
            builder.add_text_element(
                slide=slide,
                text=text,
                bbox=bbox,
                text_level=level  # For styling (bold) only, not font size
            )
        except Exception as e:
            logger.error(f"Failed to add text element: {str(e)}")
    
    @staticmethod
    def _add_table_cell_elements_to_slide(
        builder,
        slide,
        cell_elements: List[Dict[str, Any]],
        scale_x: float = 1.0,
        scale_y: float = 1.0
    ):
        """
        Add table cell elements as individual text boxes to slide
        bbox
        
        Args:
            builder: PPTXBuilder instance
            slide: Target slide
            cell_elements: List of EditableElement (table_cell type)
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor
        """
        from pptx.util import Pt
        from pptx.dml.color import RGBColor
        
        logger.info(f"Bắt đầu thêm các phần tử ô bảng, Tổng {len(cell_elements)} ")
        
        for cell_elem in cell_elements:
            text = cell_elem.get('content', '')
            bbox_global = cell_elem.get('bbox_global', {})
            
            if not text.strip():
                continue
            
            # Backend logic
            x0 = bbox_global.get('x0', 0)
            y0 = bbox_global.get('y0', 0)
            x1 = bbox_global.get('x1', 0)
            y1 = bbox_global.get('y1', 0)
            
            # Backend logic
            bbox = [
                int(x0 * scale_x),
                int(y0 * scale_y),
                int(x1 * scale_x),
                int(y1 * scale_y)
            ]
            
            try:
                # Backend logic
                builder.add_text_element(
                    slide=slide,
                    text=text,
                    bbox=bbox,
                    text_level=None,
                    align='center'
                )
                
                logger.debug(f" Thêm ô: '{text[:10]}...' at bbox {bbox}")
                
            except Exception as e:
                logger.warning(f"Thêm ô thất bại: {e}")
        
        logger.info(f"✓ Hoàn tất thêm các ô bảng, Tổng {len(cell_elements)} ")
    
    @staticmethod
    def _add_mineru_image_to_slide(
        builder,
        slide,
        image_item: Dict[str, Any],
        mineru_dir: Path,
        scale_x: float = 1.0,
        scale_y: float = 1.0
    ):
        """
        Add image or table item from MinerU to slide
        
        Args:
            builder: PPTXBuilder instance
            slide: Target slide
            image_item: Image/table item from MinerU content_list
            mineru_dir: MinerU result directory
            scale_x: X-axis scale factor
            scale_y: Y-axis scale factor
        """
        bbox = image_item.get('bbox')
        if not bbox or len(bbox) != 4:
            logger.warning(f"Invalid bbox for image item: {image_item}")
            return
        
        original_bbox = bbox.copy()
        
        # Apply scale factors to bbox
        x0, y0, x1, y1 = bbox
        bbox = [
            int(x0 * scale_x),
            int(y0 * scale_y),
            int(x1 * scale_x),
            int(y1 * scale_y)
        ]
        
        if scale_x != 1.0 or scale_y != 1.0:
            logger.debug(f"Item bbox scaled: {original_bbox} -> {bbox} (scale: {scale_x:.3f}x{scale_y:.3f})")
        
        # Backend logic
        item_type = image_item.get('element_type') or image_item.get('type', 'image')
        children = image_item.get('children', [])
        
        logger.debug(f"Processing {item_type} element, has {len(children)} children")
        
        if children and item_type == 'table':
            # Add editable table from child elements (cells)
            try:
                # Filter only table_cell elements
                cell_elements = [child for child in children if child.get('element_type') == 'table_cell']
                
                if cell_elements:
                    logger.info(f"Thêm bảng có thể chỉnh sửa ({len(cell_elements)}ô bảng) ")
                    ExportService._add_table_cell_elements_to_slide(
                        builder=builder,
                        slide=slide,
                        cell_elements=cell_elements,
                        scale_x=scale_x,
                        scale_y=scale_y
                    )
                    return  # Table added successfully
            except Exception as e:
                logger.exception("Failed to add table cells, falling back to image")
                # Fall through to add as image instead
        
        # Check if this is a table with HTML data (legacy)
        html_table = image_item.get('html_table')
        if html_table and item_type == 'table':
            # Add editable table from HTML
            try:
                builder.add_table_element(
                    slide=slide,
                    html_table=html_table,
                    bbox=bbox
                )
                logger.info(f"Added editable table at bbox {bbox}")
                return  # Table added successfully
            except Exception as e:
                logger.error(f"Failed to add table: {str(e)}, falling back to image")
                # Fall through to add as image instead
        
        # Add as image (either image type or table fallback)
        img_path_str = image_item.get('img_path', '')
        if not img_path_str:
            logger.warning(f"No img_path in item: {image_item}")
            return
        
        # Try to find the image file
        # MinerU may store images in 'images/' subdirectory
        possible_paths = [
            mineru_dir / img_path_str,
            mineru_dir / 'images' / Path(img_path_str).name,
            mineru_dir / Path(img_path_str).name,
        ]
        
        image_path = None
        for path in possible_paths:
            if path.exists():
                image_path = str(path)
                break
        
        if not image_path:
            logger.warning(f"Image file not found: {img_path_str}")
            # Add placeholder
            builder.add_image_placeholder(slide, bbox)
            return
        
        # Add image element
        try:
            builder.add_image_element(
                slide=slide,
                image_path=image_path,
                bbox=bbox
            )
        except Exception as e:
            logger.error(f"Failed to add image element: {str(e)}")
    
    @staticmethod
    def _collect_text_elements_for_extraction(
        elements: List,  # List[EditableElement]
        depth: int = 0
    ) -> List[tuple]:
        """
        
        
        Args:
            elements: EditableElement
            depth: 
        
        Returns:
            ,  (element_id, image_path, text_content)
        """
        text_items = []
        
        for elem in elements:
            elem_type = elem.element_type
            
            # Backend logic
            if elem_type in ['text', 'title', 'table_cell', 'list', 'paragraph', 'header', 'footer', 'heading', 'table_caption', 'image_caption']:
                if elem.content and elem.image_path and os.path.exists(elem.image_path):
                    text = elem.content.strip()
                    if text:
                        text_items.append((elem.element_id, elem.image_path, text))
            
            # Backend logic
            if hasattr(elem, 'children') and elem.children:
                child_items = ExportService._collect_text_elements_for_extraction(
                    elements=elem.children,
                    depth=depth + 1
                )
                text_items.extend(child_items)
        
        return text_items
    
    @staticmethod
    def _batch_extract_text_styles(
        text_items: List[tuple],
        text_attribute_extractor,
        max_workers: int = 8
    ) -> Dict[str, Any]:
        """
         () 
        
        . 
        , , . 
        
        : _batch_extract_text_styles_with_full_image . 
        
        Args:
            text_items: ,  (element_id, image_path, text_content)
            text_attribute_extractor: 
            max_workers: 
        
        Returns:
            , keyelement_id, valueTextStyleResult
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        if not text_items or not text_attribute_extractor:
            return {}
        
        logger.info(f"Trích xuất song song {len(text_items)} kiểu của phần tử văn bản (Số luồng đồng thời: {max_workers}) ...")
        
        results = {}
        
        def extract_single(item):
            element_id, image_path, text_content = item
            try:
                style = text_attribute_extractor.extract(
                    image=image_path,
                    text_content=text_content
                )
                return element_id, style
            except Exception as e:
                logger.warning(f"Trích xuất kiểu văn bản thất bại [{element_id}]: {e}")
                return element_id, None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(extract_single, item): item[0] for item in text_items}
            
            for future in as_completed(futures):
                element_id, style = future.result()
                if style is not None:
                    results[element_id] = style
        
        logger.info(f"✓ Hoàn tất trích xuất kiểu văn bản, thành công {len(results)}/{len(text_items)} ")
        return results
    
    @staticmethod
    def _collect_text_elements_for_batch_extraction(
        elements: List,  # List[EditableElement]
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
         (, bbox) 
        
        Args:
            elements: EditableElement
            depth: 
        
        Returns:
            ,  element_id, bbox, content
        """
        text_items = []
        
        for elem in elements:
            elem_type = elem.element_type
            
            # Backend logic
            if elem_type in ['text', 'title', 'table_cell', 'list', 'paragraph', 'header', 'footer', 'heading', 'table_caption', 'image_caption']:
                if elem.content:
                    text = elem.content.strip()
                    if text:
                        # Backend logic
                        bbox = elem.bbox_global if hasattr(elem, 'bbox_global') and elem.bbox_global else elem.bbox
                        text_items.append({
                            'element_id': elem.element_id,
                            'bbox': [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                            'content': text
                        })
            
            # Backend logic
            if hasattr(elem, 'children') and elem.children:
                child_items = ExportService._collect_text_elements_for_batch_extraction(
                    elements=elem.children,
                    depth=depth + 1
                )
                text_items.extend(child_items)
        
        return text_items
    
    @staticmethod
    def _batch_extract_text_styles_with_full_image(
        editable_images: List,  # List[EditableImage]
        text_attribute_extractor,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
         [] 
        
        :  caption model ,  bbox , 
         (, , ) . 
        
        : , . 
        
        Args:
            editable_images: EditableImage, PPT
            text_attribute_extractor:  ( extract_batch_with_full_image ) 
            max_workers: 
        
        Returns:
            , keyelement_id, valueTextStyleResult
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        if not editable_images or not text_attribute_extractor:
            return {}
        
        # Backend logic
        if not hasattr(text_attribute_extractor, 'extract_batch_with_full_image'):
            logger.warning("Bộ trích xuất không hỗ trợ extract_batch_with_full_image phương pháp, chuyển dự phòng về logic cũ")
            # Backend logic
            all_text_items = []
            for editable_img in editable_images:
                text_items = ExportService._collect_text_elements_for_extraction(editable_img.elements)
                all_text_items.extend(text_items)
            return ExportService._batch_extract_text_styles(
                text_items=all_text_items,
                text_attribute_extractor=text_attribute_extractor,
                max_workers=max_workers * 2
            )
        
        logger.info(f"[logic mới]Sử dụng phân tích hàng loạt toàn ảnh {len(editable_images)} kiểu văn bản của trang...")
        
        all_results = {}
        
        def process_single_page(editable_img, page_idx):
            """ Backend docstring """
            try:
                # Backend logic
                text_elements = ExportService._collect_text_elements_for_batch_extraction(
                    editable_img.elements
                )
                
                if not text_elements:
                    logger.info(f" Trang {page_idx + 1}: Không có phần tử văn bản")
                    return {}
                
                logger.info(f" Trang {page_idx + 1}: Phân tích {len(text_elements)} phần tử văn bản...")
                
                # Backend logic
                full_image_path = editable_img.image_path
                
                # Backend logic
                page_results = text_attribute_extractor.extract_batch_with_full_image(
                    full_image=full_image_path,
                    text_elements=text_elements
                )
                
                logger.info(f" Trang {page_idx + 1}: Trích xuất thành công {len(page_results)} kiểu của phần tử")
                return page_results
                
            except Exception as e:
                logger.error(f"Trang {page_idx + 1} Trích xuất kiểu văn bản thất bại: {e}", exc_info=True)
                return {}
        
        # Backend logic
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single_page, img, idx): idx 
                for idx, img in enumerate(editable_images)
            }
            
            for future in as_completed(futures):
                page_idx = futures[future]
                try:
                    page_results = future.result()
                    all_results.update(page_results)
                except Exception as e:
                    logger.error(f"Trang {page_idx + 1} Xử lý thất bại: {e}")
        
        total_elements = sum(
            len(ExportService._collect_text_elements_for_batch_extraction(img.elements))
            for img in editable_images
        )
        logger.info(f"✓ Hoàn tất trích xuất kiểu văn bản hàng loạt trên toàn ảnh, thành công {len(all_results)}/{total_elements} ")
        
        return all_results
    
    @staticmethod
    def _batch_extract_text_styles_hybrid(
        editable_images: List,  # List[EditableImage]
        text_attribute_extractor,
        max_workers: int = 8,
        fail_fast: bool = False,
        on_progress=None,  # Backend logic
    ) -> Tuple[Dict[str, Any], List[Tuple[str, str]]]:
        """
         [] 
        
        : 
        -  () :  is_bold, is_italic, is_underline, text_alignment
          
        - :  font_color
          
        
        Args:
            editable_images: EditableImage, PPT
            text_attribute_extractor: 
            max_workers: 
            fail_fast: 
            on_progress:  (done, total, label), 
        
        Returns:
            (results, failed_extractions):
            - results: , keyelement_id, valueTextStyleResult () 
            - failed_extractions: ,  (element_id, error_reason)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from services.image_editability.text_attribute_extractors import TextStyleResult
        
        if not editable_images or not text_attribute_extractor:
            return {}, []
        
        # Backend logic
        if not hasattr(text_attribute_extractor, 'extract_batch_with_full_image'):
            logger.warning("Bộ trích xuất không hỗ trợ chiến lược kết hợp, chuyển dự phòng sang nhận diện cắt từng phần tử")
            all_text_items = []
            for editable_img in editable_images:
                text_items = ExportService._collect_text_elements_for_extraction(editable_img.elements)
                all_text_items.extend(text_items)
            results = ExportService._batch_extract_text_styles(
                text_items=all_text_items,
                text_attribute_extractor=text_attribute_extractor,
                max_workers=max_workers
            )
            return results, []  # Backend logic
        
        logger.info(f"[Chiến lược kết hợp]Bắt đầu phân tích {len(editable_images)} kiểu văn bản của trang...")
        logger.info(f" - Nhận diện toàn cục: is_bold, is_italic, is_underline, text_alignment")
        logger.info(f" - Nhận diện đơn lẻ: font_color")
        
        # Backend logic
        all_text_items = []  # Backend logic
        page_text_elements = {}  # Backend logic
        
        for page_idx, editable_img in enumerate(editable_images):
            # Backend logic
            text_items = ExportService._collect_text_elements_for_extraction(editable_img.elements)
            all_text_items.extend(text_items)
            
            # Backend logic
            batch_elements = ExportService._collect_text_elements_for_batch_extraction(editable_img.elements)
            if batch_elements:
                page_text_elements[page_idx] = {
                    'image_path': editable_img.image_path,
                    'elements': batch_elements
                }
        
        if not all_text_items:
            return {}, []
        
        # Backend logic
        global_results = {}  # Backend logic
        local_results = {}   # Backend logic
        
        def extract_global_for_page(page_idx, page_data):
            """ Backend docstring """
            max_global_attempts = 3
            expected_element_ids = {
                element['element_id'] for element in page_data['elements']
            }
            best_results = {}
            had_model_response = False
            last_exception = None

            for attempt in range(1, max_global_attempts + 1):
                if attempt > 1:
                    time.sleep(1)
                try:
                    raw_results = text_attribute_extractor.extract_batch_with_full_image(
                        full_image=page_data['image_path'],
                        text_elements=page_data['elements']
                    )
                    if raw_results is not None and not isinstance(raw_results, dict):
                        raise ValueError("Expected dict or None from style extractor")
                    results = {
                        key: value for key, value in raw_results.items()
                        if value is not None
                    } if raw_results is not None else {}
                    had_model_response = True
                    best_results.update(results)
                    missing_element_ids = expected_element_ids - set(best_results.keys())

                    logger.info(
                        "Nhận diện toàn cục trang %s trang %s/%s lần hoàn tất: expected=%s returned=%s accumulated=%s missing=%s",
                        page_idx + 1,
                        attempt,
                        max_global_attempts,
                        len(expected_element_ids),
                        len(results),
                        len(best_results),
                        len(missing_element_ids),
                    )

                    if not missing_element_ids:
                        return page_idx, best_results, None

                    last_exception = None
                    logger.warning(
                        "Nhận diện toàn cục trang %s trang %s/%s lần trả về không đầy đủ, sẽ thử lại: missing_sample=%s",
                        page_idx + 1,
                        attempt,
                        max_global_attempts,
                        list(missing_element_ids)[:5],
                    )
                except Exception as e:
                    last_exception = str(e)
                    logger.warning(
                        "Nhận diện toàn cục trang %s trang %s/%s lần thất bại, sẽ thử lại: %s",
                        page_idx + 1,
                        attempt,
                        max_global_attempts,
                        e,
                    )

            logger.error(
                "Nhận diện toàn cục trang %s Đã hết lượt thử lại: expected=%s returned=%s last_error=%s",
                page_idx + 1,
                len(expected_element_ids),
                len(best_results),
                last_exception or "Nhận diện toàn cục không trả về kết quả đầy đủ",
            )
            page_error = last_exception if (not best_results or not had_model_response) else None
            return page_idx, best_results, page_error
        
        # Backend logic
        failed_extractions = []  # [(element_id, reason), ...]
        
        def extract_local_single(item):
            """ Backend docstring """
            element_id, image_path, text_content = item
            try:
                style = text_attribute_extractor.extract(
                    image=image_path,
                    text_content=text_content
                )
                # Check for real success: style must exist and not be an error result
                # (CaptionModelTextAttributeExtractor returns TextStyleResult(confidence=0.0, metadata={'error':...}) on failure)
                is_error = style and style.confidence == 0.0 and style.metadata.get('error')
                if style and not is_error:
                    return element_id, style, None
                else:
                    error_msg = style.metadata.get('error', 'Trích xuất kiểu trả về rỗng') if style else "Trích xuất kiểu trả về rỗng"
                    if fail_fast:
                        raise ExportService._build_style_extraction_error(
                            error_msg,
                            element_id=element_id,
                            text_content=text_content,
                            text_attribute_extractor=text_attribute_extractor,
                            operation='local_element_style',
                        )
                    return element_id, None, error_msg
            except ExportError:
                raise  # Backend logic
            except Exception as e:
                logger.warning(f"Nhận diện đơn lẻ thất bại [{element_id}]: {e}")
                if fail_fast:
                    raise ExportService._build_style_extraction_error(
                        str(e),
                        element_id=element_id,
                        text_content=text_content,
                        text_attribute_extractor=text_attribute_extractor,
                        operation='local_element_style',
                    )
                return element_id, None, str(e)
        
        # Backend logic
        logger.info(f" Thực thi đồng thời: Nhận diện toàn cục {len(page_text_elements)} trang + Nhận diện đơn lẻ {len(all_text_items)} phần tử...")

        total_tasks = len(page_text_elements) + len(all_text_items)
        completed_tasks = 0

        def notify_progress(label: str):
            nonlocal completed_tasks
            completed_tasks += 1
            if on_progress:
                try:
                    on_progress(completed_tasks, total_tasks, label)
                except Exception as exc:
                    logger.debug(f"Callback tiến độ trích xuất kiểu thất bại: {exc}")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Backend logic
            global_futures = {
                executor.submit(extract_global_for_page, idx, data): ('global', idx)
                for idx, data in page_text_elements.items()
            }
            
            # Backend logic
            local_futures = {
                executor.submit(extract_local_single, item): ('local', item[0])
                for item in all_text_items
            }
            
            # Backend logic
            for future in as_completed(global_futures):
                task_type, page_idx = global_futures[future]
                notify_progress(f"Nhận diện toàn cục trang {page_idx + 1} trang")
                try:
                    _, page_results, page_error = future.result()
                    global_results.update(page_results)
                    expected_element_ids = {
                        element['element_id'] for element in page_text_elements[page_idx]['elements']
                    }
                    missing_element_ids = expected_element_ids - set(page_results.keys())
                    if page_error:
                        if fail_fast:
                            raise ExportService._build_style_extraction_error(
                                page_error,
                                page_idx=page_idx,
                                text_attribute_extractor=text_attribute_extractor,
                                operation='global_page_style',
                            )
                        failed_extractions.extend(
                            (element_id, f"Nhận diện toàn cục thất bại: {page_error}")
                            for element_id in expected_element_ids
                        )
                    elif missing_element_ids:
                        reason = "Nhận diện toàn cục không trả về kết quả đầy đủ"
                        if fail_fast:
                            raise ExportService._build_style_extraction_error(
                                reason,
                                page_idx=page_idx,
                                text_attribute_extractor=text_attribute_extractor,
                                operation='global_page_style',
                            )
                        failed_extractions.extend((element_id, reason) for element_id in missing_element_ids)
                except Exception as e:
                    logger.error(f"Tác vụ nhận diện toàn cục thất bại: {e}")
                    if fail_fast:
                        if isinstance(e, ExportError):
                            raise
                        raise ExportService._build_style_extraction_error(
                            str(e),
                            page_idx=page_idx,
                            text_attribute_extractor=text_attribute_extractor,
                            operation='global_page_style',
                        ) from e
                    expected_element_ids = [
                        element['element_id'] for element in page_text_elements[page_idx]['elements']
                    ]
                    failed_extractions.extend(
                        (element_id, f"Nhận diện toàn cục thất bại: {e}")
                        for element_id in expected_element_ids
                    )
            
            # Backend logic
            for future in as_completed(local_futures):
                task_type, element_id = local_futures[future]
                notify_progress("Nhận diện phần tử đơn lẻ")
                try:
                    elem_id, style, error = future.result()
                    if style is not None:
                        local_results[elem_id] = style
                    if error:
                        failed_extractions.append((elem_id, error))
                except Exception as e:
                    logger.error(f"Tác vụ nhận diện đơn lẻ thất bại: {e}")
                    if fail_fast:
                        raise
                    failed_extractions.append((element_id, str(e)))
        
        # Backend logic
        # Backend logic
        merged_results = {}
        
        all_element_ids = set(global_results.keys()) | set(local_results.keys())
        
        for element_id in all_element_ids:
            global_style = global_results.get(element_id)
            local_style = local_results.get(element_id)
            
            if global_style and local_style:
                # Backend logic
                merged_results[element_id] = TextStyleResult(
                    font_color_rgb=local_style.font_color_rgb,  # Backend logic
                    colored_segments=local_style.colored_segments,  # Backend logic
                    is_bold=global_style.is_bold,              # Backend logic
                    is_italic=global_style.is_italic,          # Backend logic
                    is_underline=global_style.is_underline,    # Backend logic
                    text_alignment=global_style.text_alignment, # Backend logic
                    confidence=0.9,
                    metadata={
                        'source': 'hybrid',
                        'color_source': 'local',
                        'layout_source': 'global'
                    }
                )
            elif local_style:
                # Backend logic
                merged_results[element_id] = local_style
            elif global_style:
                # Backend logic
                merged_results[element_id] = global_style
        
        logger.info(f"✓ Hoàn tất chiến lược kết hợp: Nhận diện toàn cục {len(global_results)} , Nhận diện đơn lẻ {len(local_results)} , gộp {len(merged_results)} , thất bại {len(failed_extractions)} ")
        
        return merged_results, failed_extractions
    
    @staticmethod
    def create_editable_pptx_with_recursive_analysis(
        image_paths: List[str] = None,
        output_file: str = None,
        slide_width_pixels: int = 1920,
        slide_height_pixels: int = 1080,
        max_depth: int = 2,
        max_workers: int = 8,
        editable_images: List = None,  # Backend logic
        text_attribute_extractor = None,  # Backend logic
        progress_callback = None,  # Backend logic
        heartbeat_callback = None,  # Backend logic
        export_extractor_method: str = 'hybrid',  # Backend logic
        export_inpaint_method: str = 'hybrid',  # Backend logic
        enable_icon_subject_extraction: bool = False,  # Backend logic
        fail_fast: bool = True  # Backend logic
    ) -> Tuple[Optional[bytes], ExportWarnings]:
        """
        PPTX
        
        , ImageEditabilityService. 
        
        : 
        1.  image_paths: PPTX
        2.  editable_images:  () 
        
         ( MinerU token)  Flask app.config . 
        
        Args:
            image_paths:  (, editable_images) 
            output_file:  () 
            slide_width_pixels: 
            slide_height_pixels: 
            max_depth: 
            max_workers: 
            editable_images: EditableImage (, image_paths) 
            text_attribute_extractor:  () , , , 
                 TextAttributeExtractorFactory.create_caption_model_extractor() 
            heartbeat_callback:  () . /, 
                 () 
            export_extractor_method: Phương pháp trích xuất thành phần ('mineru' hoặc 'hybrid', mặc định 'hybrid')
            export_inpaint_method: Phương pháp phục hồi nền ('generative', 'baidu', 'hybrid', mặc định 'hybrid')
            fail_fast:  ( True) .  False . 

        Returns:
            (pptx_bytes, warnings): ,  PPTX 
            - pptx_bytes: PPTX  ( output_file  None) ,  None
            - warnings: ExportWarnings , 
        """
        from services.image_editability import ServiceConfig, ImageEditabilityService
        from utils.pptx_builder import PPTXBuilder
        
        # Backend logic
        warnings = ExportWarnings()
        
        # Backend logic
        def report_progress(step: str, message: str, percent: int):
            logger.info(f"[Tiến độ {percent}%] {step}: {message}")
            if progress_callback:
                try:
                    progress_callback(step, message, percent)
                except Exception as e:
                    logger.warning(f"Callback tiến độ thất bại: {e}")

        # Backend logic
        def beat(step: str):
            if heartbeat_callback:
                try:
                    heartbeat_callback(step)
                except Exception as e:
                    logger.debug(f"Callback heartbeat thất bại: {e}")
        
        # Backend logic
        if editable_images is not None:
            logger.info(f"Sử dụng có sẵn {len(editable_images)} kết quả phân tích để tạoPPTX")
            report_progress("Chuẩn bị", f"Sử dụng kết quả phân tích có sẵn ({len(editable_images)} trang) ", 10)
        else:
            if not image_paths:
                raise ValueError("Phải cung cấp image_paths hoặc editable_images một trong")
            
            total_pages = len(image_paths)
            logger.info(f"Bắt đầu tạo tệp có thể chỉnh sửa bằng phương pháp phân tích đệ quyPPTX, Tổng {total_pages} trang")
            report_progress("Bắt đầu", f"Chuẩn bị phân tích {total_pages} trang slide...", 0)
            
            # Backend logic
            logger.info(
                f"Sử dụng cài đặt xuất: extractor={export_extractor_method}, "
                f"inpaint={export_inpaint_method}, "
                f"icon_subject_extraction={enable_icon_subject_extraction}"
            )
            config = ServiceConfig.from_defaults(
                max_depth=max_depth,
                extractor_method=export_extractor_method,
                inpaint_method=export_inpaint_method,
                enable_icon_subject_extraction=enable_icon_subject_extraction,
            )
            editability_service = ImageEditabilityService(config)
            
            # Backend logic
            report_progress("Phân tích bố cục", f"Bắt đầu phân tích {total_pages} hình ảnh (Số luồng đồng thời: {max_workers}) ...", 5)
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            editable_images = []
            completed_count = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(editability_service.make_image_editable, img_path): idx
                    for idx, img_path in enumerate(image_paths)
                }
                
                results = [None] * len(image_paths)
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        results[idx] = future.result()
                        completed_count += 1
                        beat("Phân tích bố cục")
                        # Backend logic
                        percent = 5 + int(35 * completed_count / total_pages)
                        report_progress("Phân tích bố cục", f"Đã hoàn thành trang {completed_count}/{total_pages} phân tích bố cục trang", percent)
                    except Exception as e:
                        logger.error(f"Xử lý ảnh {image_paths[idx]} thất bại: {e}")
                        raise
                
                editable_images = results
        
        # Backend logic
        # Backend logic
        text_styles_cache = {}
        if text_attribute_extractor:
            report_progress("Trích xuất kiểu", "Bắt đầu trích xuất kiểu văn bản (Chiến lược kết hợp) ...", 45)
            
            # Backend logic
            total_text_count = sum(
                len(ExportService._collect_text_elements_for_extraction(img.elements))
                for img in editable_images
            )
            
            if total_text_count > 0:
                report_progress("Trích xuất kiểu", f"Phân tích theo chiến lược kết hợp cho {total_text_count} phần tử văn bản...", 50)

                def style_progress(done: int, total: int, label: str):
                    """ Backend docstring """
                    beat("Trích xuất kiểu")
                    if done % 10 == 0 or done >= total:
                        percent = 50 + int(20 * done / max(total, 1))
                        report_progress("Trích xuất kiểu", f"{label} ({done}/{total}) ", min(percent, 70))

                text_styles_cache, failed_extractions = ExportService._batch_extract_text_styles_hybrid(
                    editable_images=editable_images,
                    text_attribute_extractor=text_attribute_extractor,
                    max_workers=max_workers * 2,
                    fail_fast=fail_fast,
                    on_progress=style_progress
                )
                
                # Backend logic
                for element_id, reason in failed_extractions:
                    warnings.add_style_extraction_failed(element_id, reason)
                
                # Backend logic
                extracted_count = len(text_styles_cache)
                failed_count = len(failed_extractions)
                if failed_count > 0:
                    logger.warning(f"Trích xuất kiểu: {failed_count}/{total_text_count} phần tử thất bại")
                
                report_progress("Trích xuất kiểu", f"Hoàn tất {extracted_count}/{total_text_count} trích xuất kiểu văn bản ({failed_count} thất bại) ", 70)
        
        report_progress("DựngPPTX", "Bắt đầu dựng tệp có thể chỉnh sửaPPTXTệp...", 75)
        
        # Backend logic
        builder = PPTXBuilder()
        builder.create_presentation()
        builder.setup_presentation_size(slide_width_pixels, slide_height_pixels)
        
        # Backend logic
        total_pages = len(editable_images)
        for page_idx, editable_img in enumerate(editable_images):
            # Backend logic
            percent = 75 + int(20 * page_idx / total_pages)
            report_progress("DựngPPTX", f"Đang dựng trang {page_idx + 1}/{total_pages} trang...", percent)
            logger.info(f" Đang dựng trang {page_idx + 1}/{total_pages} trang...")

            # Backend logic
            page_element_count = 0

            def on_element(_page_idx=page_idx, _percent=percent):
                nonlocal page_element_count
                page_element_count += 1
                beat("DựngPPTX")
                if page_element_count % ELEMENT_PROGRESS_INTERVAL == 0:
                    report_progress(
                        "DựngPPTX",
                        f"Đang dựng trang {_page_idx + 1}/{total_pages} trang"
                        f" (Đã xử lý {page_element_count} phần tử) ...",
                        _percent,
                    )
            
            # Backend logic
            slide = builder.add_blank_slide()
            
            # Backend logic
            if editable_img.clean_background and os.path.exists(editable_img.clean_background):
                logger.info(f" Thêmclean background: {editable_img.clean_background}")
                try:
                    slide.shapes.add_picture(
                        editable_img.clean_background,
                        left=0,
                        top=0,
                        width=builder.prs.slide_width,
                        height=builder.prs.slide_height
                    )
                except Exception as e:
                    logger.error(f"Failed to add background: {e}")
            else:
                # Backend logic
                logger.info(f" Sử dụng ảnh gốc làm nền: {editable_img.image_path}")
                try:
                    slide.shapes.add_picture(
                        editable_img.image_path,
                        left=0,
                        top=0,
                        width=builder.prs.slide_width,
                        height=builder.prs.slide_height
                    )
                except Exception as e:
                    logger.error(f"Failed to add background: {e}")
            
            # Backend logic
            # Backend logic
            # Backend logic
            scale_x = slide_width_pixels / editable_img.width
            scale_y = slide_height_pixels / editable_img.height
            logger.info(f" Số lượng phần tử: {len(editable_img.elements)}, Kích thước ảnh: {editable_img.width}x{editable_img.height}, "
                       f"Kích thước slide: {slide_width_pixels}x{slide_height_pixels}, Tỷ lệ thu phóng: {scale_x:.3f}x{scale_y:.3f}")
            
            ExportService._add_editable_elements_to_slide(
                builder=builder,
                slide=slide,
                elements=editable_img.elements,
                scale_x=scale_x,
                scale_y=scale_y,
                depth=0,
                text_styles_cache=text_styles_cache,  # Backend logic
                warnings=warnings,  # Backend logic
                fail_fast=fail_fast,  # Backend logic
                on_element=on_element  # Backend logic
            )
            
            logger.info(f" ✓ trang {page_idx + 1} trang hoàn tất, Đã thêm {len(editable_img.elements)} phần tử")
        
        # Backend logic
        report_progress("Lưu tệp", "Đang lưuPPTXTệp...", 95)
        if output_file:
            builder.save(output_file)
            report_progress("Hoàn tất", f"có thể chỉnh sửaPPTXđã lưu", 100)
            logger.info(f"✓ có thể chỉnh sửaPPTXđã lưu: {output_file}")
            
            # Backend logic
            if warnings.has_warnings():
                logger.warning(f"Xuất hoàn tất, nhưng có {len(warnings.to_summary())} cảnh báo")
            
            return None, warnings
        else:
            pptx_bytes = builder.to_bytes()
            report_progress("Hoàn tất", f"có thể chỉnh sửaPPTXĐã tạo", 100)
            logger.info(f"✓ có thể chỉnh sửaPPTXĐã tạo ({len(pptx_bytes)} byte) ")
            
            # Backend logic
            if warnings.has_warnings():
                logger.warning(f"Xuất hoàn tất, nhưng có {len(warnings.to_summary())} cảnh báo")
            
            return pptx_bytes, warnings
    
    @staticmethod
    def _add_editable_elements_to_slide(
        builder,
        slide,
        elements: List,  # List[EditableElement]
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        depth: int = 0,
        text_styles_cache: Dict[str, Any] = None,  # Backend logic
        warnings: 'ExportWarnings' = None,  # Backend logic
        fail_fast: bool = False,  # Backend logic
        on_element=None,  # Backend logic
    ):
        """
        EditableElement
        
        Args:
            builder: PPTXBuilder
            slide: 
            elements: EditableElement
            scale_x: X
            scale_y: Y
            depth: 
            text_styles_cache:  () ,  _batch_extract_text_styles 
            on_element: ,  () 
        
        Note:
            elem.image_path , 
        """
        if text_styles_cache is None:
            text_styles_cache = {}

        def choose_formula_text(text: str, text_style: Any = None) -> Optional[str]:
            candidates = [text]
            if text_style and getattr(text_style, 'colored_segments', None):
                styled_text = ''.join(seg.text for seg in text_style.colored_segments).strip()
                if styled_text and styled_text not in candidates:
                    candidates.append(styled_text)

            def score(candidate: str) -> int:
                if not looks_like_latex_math(candidate):
                    return -1
                return (
                    len(re.findall(r"\\[A-Za-z]+", candidate)) * 10
                    + candidate.count("\\") * 4
                    + len(re.findall(r"[_^]\s*(?:\{[^{}]+\}|[A-Za-z0-9+\-=()*])", candidate)) * 3
                    + len(re.findall(r"[∀∃∈∉≤≥≠≈∑∏∫∞∂∇πΠΣ√]", candidate)) * 2
                    - len(re.findall(r"\b[A-Za-z]{5,}\b", candidate)) * 2
                )

            scored = [(score(candidate), candidate) for candidate in candidates if candidate]
            scored = [item for item in scored if item[0] >= 0]
            if not scored:
                return None
            return max(scored, key=lambda item: item[0])[1]

        def add_text_or_formula(elem, text, bbox_list, text_level='default', align='left'):
            text_style = text_styles_cache.get(elem.element_id)
            if text_style:
                logger.debug(f"{' ' * depth} Sử dụng kiểu văn bản trong bộ nhớ đệm: color={text_style.font_color_rgb}, bold={text_style.is_bold}")

            formula_text = choose_formula_text(text, text_style)
            if formula_text:
                if builder.add_math_element(
                    slide=slide,
                    latex=formula_text,
                    bbox=bbox_list,
                    text_style=text_style
                ):
                    return

                fallback_text = latex_to_display_text(formula_text)
                builder.add_text_element(
                    slide=slide,
                    text=fallback_text,
                    bbox=bbox_list,
                    text_level=text_level,
                    align=align,
                    text_style=text_style,
                    allow_math_conversion=False
                )
                if warnings:
                    warnings.add_text_render_failed(
                        formula_text,
                        'Công thức tạm thời chưa hỗ trợ chuyển đổi gốc, đã dùng văn bản dễ đọc thay thế'
                    )
                return

            builder.add_text_element(
                slide=slide,
                text=text,
                bbox=bbox_list,
                text_level=text_level,
                align=align,
                text_style=text_style
            )
        
        for elem in elements:
            elem_type = elem.element_type
            
            # Backend logic
            # Backend logic
            # Backend logic
            if depth == 0:
                bbox = elem.bbox  # Backend logic
            else:
                bbox = elem.bbox_global if hasattr(elem, 'bbox_global') and elem.bbox_global else elem.bbox
            
            # Backend logic
            bbox_list = [
                int(bbox.x0 * scale_x),
                int(bbox.y0 * scale_y),
                int(bbox.x1 * scale_x),
                int(bbox.y1 * scale_y)
            ]
            
            logger.info(f"{' ' * depth} Thêm phần tử: type={elem_type}, bbox={bbox_list}, content={elem.content[:30] if elem.content else None}, image_path={elem.image_path}, Sử dụng{'toàn cục' if depth > 0 else 'cục bộ'}tọa độ")

            # Backend logic
            if elem_type in ['text', 'title', 'list', 'paragraph', 'header', 'footer', 'heading', 'table_caption', 'image_caption', 'equation', 'interline_equation', 'inline_equation']:
                # Backend logic
                if elem.content:
                    text = elem.content.strip()
                    if text:
                        try:
                            # Backend logic
                            level = 'title' if elem_type in ['title', 'heading'] else 'default'

                            add_text_or_formula(elem, text, bbox_list, text_level=level)
                        except Exception as e:
                            logger.warning(f"Thêm phần tử văn bản thất bại: {e}")
                            if fail_fast:
                                raise ExportService._build_text_render_error(
                                    str(e),
                                    text=text,
                                    bbox=bbox_list,
                                    element_kind='Phần tử văn bản',
                                )
                            if warnings:
                                warnings.add_text_render_failed(text, str(e))
            
            elif elem_type == 'table_cell':
                # Backend logic
                if elem.content:
                    text = elem.content.strip()
                    if text:
                        try:
                            # Backend logic
                            # Backend logic
                            add_text_or_formula(
                                elem,
                                text,
                                bbox_list,
                                text_level=None,
                                align='center'
                            )

                        except Exception as e:
                            logger.warning(f"Thêm ô thất bại: {e}")
                            if fail_fast:
                                raise ExportService._build_text_render_error(
                                    str(e),
                                    text=text,
                                    bbox=bbox_list,
                                    element_kind='Ô bảng',
                                )
                            if warnings:
                                warnings.add_text_render_failed(text, str(e))
            
            elif elem_type == 'table':
                # Backend logic
                if elem.children and elem.inpainted_background_path:
                    logger.info(f"{' ' * depth} bảng có {len(elem.children)} ô bảng, sử dụng định dạng có thể chỉnh sửa")
                    
                    # Backend logic
                    if os.path.exists(elem.inpainted_background_path):
                        try:
                            builder.add_image_element(
                                slide=slide,
                                image_path=elem.inpainted_background_path,
                                bbox=bbox_list
                            )
                        except Exception as e:
                            logger.error(f"Failed to add table background: {e}")
                    
                    # Backend logic
                    ExportService._add_editable_elements_to_slide(
                        builder=builder,
                        slide=slide,
                        elements=elem.children,
                        scale_x=scale_x,
                        scale_y=scale_y,
                        depth=depth + 1,
                        text_styles_cache=text_styles_cache,
                        warnings=warnings,
                        fail_fast=fail_fast,
                        on_element=on_element
                    )
                else:
                    # Backend logic
                    # Backend logic
                    if elem.image_path and os.path.exists(elem.image_path):
                        try:
                            builder.add_image_element(
                                slide=slide,
                                image_path=elem.image_path,
                                bbox=bbox_list
                            )
                        except Exception as e:
                            logger.error(f"Failed to add table image: {e}")
                    else:
                        logger.warning(f"Table image not found: {elem.image_path}")
                        builder.add_image_placeholder(slide, bbox_list)
            
            elif elem_type in ['image', 'figure', 'chart']:
                # Backend logic
                should_use_recursive_render = False
                
                if elem.children and elem.inpainted_background_path:
                    # Backend logic
                    parent_area = (bbox.x1 - bbox.x0) * (bbox.y1 - bbox.y0)
                    max_child_coverage_ratio = 0.85  # Backend logic
                    has_dominant_child = False
                    
                    for child in elem.children:
                        if hasattr(child, 'bbox_global') and child.bbox_global:
                            child_bbox = child.bbox_global
                        else:
                            child_bbox = child.bbox
                        
                        child_area = child_bbox.area
                        coverage_ratio = child_area / parent_area if parent_area > 0 else 0
                        
                        if coverage_ratio > max_child_coverage_ratio:
                            logger.info(f"{' ' * depth} phần tử con {child.element_id} chiếm diện tích phần tử cha {coverage_ratio*100:.1f}% (>{max_child_coverage_ratio*100:.0f}%), Bỏ qua kết xuất đệ quy, Sử dụng trực tiếp ảnh gốc")
                            has_dominant_child = True
                            break
                    
                    should_use_recursive_render = not has_dominant_child
                
                # Backend logic
                if should_use_recursive_render:
                    logger.debug(f"{' ' * depth} phần tử có {len(elem.children)} phần tử con, Thêm đệ quy")
                    
                    # Backend logic
                    if os.path.exists(elem.inpainted_background_path):
                        try:
                            builder.add_image_element(slide, elem.inpainted_background_path, bbox_list)
                        except Exception as e:
                            logger.error(f"Failed to add inpainted background: {e}")
                    
                    # Backend logic
                    ExportService._add_editable_elements_to_slide(
                        builder=builder,
                        slide=slide,
                        elements=elem.children,
                        scale_x=scale_x,
                        scale_y=scale_y,
                        depth=depth + 1,
                        text_styles_cache=text_styles_cache,
                        warnings=warnings,
                        fail_fast=fail_fast,
                        on_element=on_element
                    )
                else:
                    # Backend logic
                    # Backend logic
                    if elem.image_path and os.path.exists(elem.image_path):
                        try:
                            builder.add_image_element(
                                slide=slide,
                                image_path=elem.image_path,
                                bbox=bbox_list
                            )
                        except Exception as e:
                            logger.error(f"Failed to add image: {e}")
                    else:
                        logger.warning(f"Image file not found: {elem.image_path}")
                        builder.add_image_placeholder(slide, bbox_list)
            
            else:
                # Backend logic
                logger.debug(f"{' ' * depth} Bỏ qua loại không xác định: {elem_type}")

            if on_element:
                try:
                    on_element()
                except Exception as e:
                    logger.debug(f"Callback tiến độ phần tử thất bại: {e}")
    