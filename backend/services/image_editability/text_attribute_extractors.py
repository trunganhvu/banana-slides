"""
 - 

: 
- TextStyleResult: 
- TextAttributeExtractor: 
- CaptionModelTextAttributeExtractor: Caption Model
- TextAttributeExtractorRegistry: 
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image
from services.prompts import get_text_attribute_extraction_prompt

logger = logging.getLogger(__name__)


@dataclass
class ColoredSegment:
    """
    
    
    ,  LaTeX 
    """
    text: str  # Backend logic
    color_rgb: Tuple[int, int, int] = (0, 0, 0)  # Backend logic
    is_latex: bool = False  # Backend logic
    
    def to_dict(self) -> Dict[str, Any]:
        """ Backend docstring """
        result = {
            'text': self.text,
            'color': f"#{self.color_rgb[0]:02x}{self.color_rgb[1]:02x}{self.color_rgb[2]:02x}"
        }
        if self.is_latex:
            result['is_latex'] = True
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColoredSegment':
        """ Backend docstring """
        text = data.get('text', '')
        color = data.get('color', '#000000')
        is_latex = bool(data.get('is_latex', False))
        
        # Backend logic
        if isinstance(color, str):
            color = color.lstrip('#')
            if len(color) == 3:
                color = ''.join(c * 2 for c in color)
            try:
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                color_rgb = (r, g, b)
            except (ValueError, IndexError):
                color_rgb = (0, 0, 0)
        else:
            color_rgb = (0, 0, 0)
        return cls(text=text, color_rgb=color_rgb, is_latex=is_latex)


@dataclass
class TextStyleResult:
    """
    
    
    
    
    Note:
        , , . 
         PPTXBuilder.calculate_font_size bbox. 
    """
    # Backend logic
    font_color_rgb: Tuple[int, int, int] = (0, 0, 0)
    
    # Backend logic
    # Backend logic
    colored_segments: List[ColoredSegment] = field(default_factory=list)
    
    # Backend logic
    is_bold: bool = False
    
    # Backend logic
    is_italic: bool = False
    
    # Backend logic
    is_underline: bool = False
    
    # Backend logic
    text_alignment: Optional[str] = None
    
    # Backend logic
    confidence: float = 1.0
    
    # Backend logic
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """ Backend docstring """
        result = asdict(self)
        # Backend logic
        result['font_color_rgb'] = list(self.font_color_rgb)
        # Backend logic
        result['colored_segments'] = [seg.to_dict() if isinstance(seg, ColoredSegment) else seg for seg in self.colored_segments]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextStyleResult':
        """ Backend docstring """
        if 'font_color_rgb' in data and isinstance(data['font_color_rgb'], list):
            data['font_color_rgb'] = tuple(data['font_color_rgb'])
        # Backend logic
        if 'colored_segments' in data:
            data['colored_segments'] = [
                ColoredSegment.from_dict(seg) if isinstance(seg, dict) else seg 
                for seg in data['colored_segments']
            ]
        return cls(**data)
    
    def get_hex_color(self) -> str:
        """ Backend docstring """
        r, g, b = self.font_color_rgb
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def get_full_text(self) -> str:
        """ Backend docstring """
        if self.colored_segments:
            return ''.join(seg.text for seg in self.colored_segments)
        return ""
    
    def has_multi_color(self) -> bool:
        """ Backend docstring """
        if not self.colored_segments or len(self.colored_segments) <= 1:
            return False
        colors = set(seg.color_rgb for seg in self.colored_segments)
        return len(colors) > 1


class TextAttributeExtractor(ABC):
    """
    
    
    , : 
    - CaptionModelTextAttributeExtractor:  (Gemini) 
    - : CV, OCR
    """
    
    @abstractmethod
    def extract(
        self,
        image: Union[str, Image.Image],
        text_content: Optional[str] = None,
        **kwargs
    ) -> TextStyleResult:
        """
        
        
        Args:
            image: , PIL Image
            text_content:  (, ) 
            **kwargs: 
        
        Returns:
            TextStyleResult, 
        """
        pass
    
    @abstractmethod
    def supports_batch(self) -> bool:
        """
        
        
        Returns:
            True
        """
        pass
    
    def extract_batch(
        self,
        items: List[Tuple[Union[str, Image.Image], Optional[str]]],
        **kwargs
    ) -> List[TextStyleResult]:
        """
        
        
        : extract
        
        
        Args:
            items: ,  (image, text_content) 
            **kwargs: 
        
        Returns:
            TextStyleResult
        """
        results = []
        for image, text_content in items:
            try:
                result = self.extract(image, text_content, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Trích xuất hàng loạt thuộc tính văn bản thất bại: {e}")
                # Backend logic
                results.append(TextStyleResult(confidence=0.0))
        return results


class CaptionModelTextAttributeExtractor(TextAttributeExtractor):
    """
    Caption Model () 
    
     (Gemini) , 
    JSON, , . 
    """
    @staticmethod
    def build_prompt(text_content: Optional[str] = None) -> str:
        """
        prompt
        text_content, 
        """
        if text_content:
            content_hint = f'Nội dung văn bản trong ảnh là: "{text_content}"'
        else:
            content_hint = ""
        return get_text_attribute_extraction_prompt(content_hint=content_hint)
    
    def __init__(self, ai_service, prompt_template: Optional[str] = None):
        """
        Caption Model
        
        Args:
            ai_service: AIService (generate_json) 
            prompt_template: prompt () ,  {content_hint} 
        """
        self.ai_service = ai_service
        self.prompt_template = prompt_template
    
    def supports_batch(self) -> bool:
        """ Backend docstring """
        return False
    
    def extract(
        self,
        image: Union[str, Image.Image],
        text_content: Optional[str] = None,
        **kwargs
    ) -> TextStyleResult:
        """
        Caption Model
        
        Args:
            image: 
            text_content:  (, ) 
            **kwargs: 
                - thinking_budget: int, , 500
        
        Returns:
            TextStyleResult
        """
        thinking_budget = kwargs.get('thinking_budget', 500)
        
        try:
            # Backend logic
            if isinstance(image, str):
                pil_image = Image.open(image)
            else:
                pil_image = image
            
            # Backend logic
            # Backend logic
            if text_content:
                content_hint = f'Nội dung văn bản trong ảnh là: "{text_content}"'
            else:
                content_hint = ""
            
            if self.prompt_template:
                # Backend logic
                prompt = self.prompt_template.format(content_hint=content_hint)
            else:
                prompt = get_text_attribute_extraction_prompt(content_hint=content_hint)
            
            # Backend logic
            # Backend logic
            result_json = self._call_vision_model(pil_image, prompt, thinking_budget)
            
            # Backend logic
            return self._parse_result(result_json)
        
        except Exception as e:
            logger.error(f"CaptionModelTextAttributeExtractortrích xuất thất bại: {e}", exc_info=True)
            return TextStyleResult(confidence=0.0, metadata={'error': str(e)})
    
    def _call_vision_model(self, image: Image.Image, prompt: str, thinking_budget: int) -> Dict[str, Any]:
        """
        ,  ai_service.generate_json_with_image () 
        
        Args:
            image: PIL Image
            prompt: 
            thinking_budget: 
        
        Returns:
            JSON
        """
        import tempfile
        import os
        
        # Backend logic
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            image.save(tmp_path)
        
        try:
            # Backend logic
            result = self.ai_service.generate_json_with_image(
                prompt=prompt,
                image_path=tmp_path,
                thinking_budget=thinking_budget
            )
            return result if isinstance(result, dict) else {}

        except ValueError as e:
            if "không hỗ trợ đầu vào hình ảnh" in str(e):
                raise RuntimeError(f"Mô hình trích xuất kiểu ảnh hiện tại không hỗ trợ đầu vào hình ảnh: {e}") from e
            raise RuntimeError(f"Nội dung trả về từ mô hình thị giác không thể phân tích: {e}") from e

        except Exception as e:
            raise RuntimeError(f"Gọi mô hình thị giác để trích xuất kiểu văn bản thất bại: {e}") from e
        
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        RGB
        
        Args:
            hex_color: Màu hệ thập lục phân (Hex), như "#FF6B6B" hoặc "FF6B6B"
        
        Returns:
            RGB (R, G, B)
        """
        # Backend logic
        hex_color = hex_color.lstrip('#')
        
        # Backend logic
        if len(hex_color) == 3:
            hex_color = ''.join(c * 2 for c in hex_color)
        
        if len(hex_color) != 6:
            return (0, 0, 0)  # Backend logic
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        except ValueError:
            return (0, 0, 0)
    
    def _parse_result(self, result_json: Dict[str, Any]) -> TextStyleResult:
        """
        AIJSON
        
        Args:
            result_json: AIJSON, : 
                - :  colored_segments  (-) 
                - :  font_color 
        
        Returns:
            TextStyleResult
        """
        if not result_json:
            return TextStyleResult(
                confidence=0.0,
                metadata={'error': 'Mô hình thị giác không trả về kết quả kiểu dáng có thể phân tích'}
            )
        
        try:
            # Backend logic
            colored_segments = []
            segments_data = result_json.get('colored_segments', [])
            
            if segments_data and isinstance(segments_data, list):
                for seg in segments_data:
                    if isinstance(seg, dict):
                        colored_segments.append(ColoredSegment.from_dict(seg))
            
            # Backend logic
            if colored_segments:
                font_color_rgb = colored_segments[0].color_rgb
            else:
                # Backend logic
                font_color_hex = result_json.get('font_color', '#000000')
                if isinstance(font_color_hex, str):
                    font_color_rgb = self._hex_to_rgb(font_color_hex)
                else:
                    font_color_rgb = (0, 0, 0)
            
            # Backend logic
            is_bold = bool(result_json.get('is_bold', False))
            is_italic = bool(result_json.get('is_italic', False))
            is_underline = bool(result_json.get('is_underline', False))
            
            # Backend logic
            text_alignment = result_json.get('text_alignment')
            if text_alignment not in ('left', 'center', 'right', 'justify', None):
                text_alignment = None
            
            return TextStyleResult(
                font_color_rgb=font_color_rgb,
                colored_segments=colored_segments,
                is_bold=is_bold,
                is_italic=is_italic,
                is_underline=is_underline,
                text_alignment=text_alignment,
                confidence=0.9,  # Backend logic
                metadata={'source': 'caption_model', 'raw_response': result_json}
            )
        
        except Exception as e:
            logger.error(f"Phân tích kết quả thất bại: {e}")
            return TextStyleResult(confidence=0.0, metadata={'error': str(e)})
    
    def extract_batch_with_full_image(
        self,
        full_image: Union[str, Image.Image],
        text_elements: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, TextStyleResult]:
        """
         [] 
        
        : , 
        
        Args:
            full_image: , PIL Image
            text_elements: , : 
                - element_id: 
                - bbox:  [x0, y0, x1, y1]
                - content: 
            **kwargs:
                - thinking_budget: int, , 1000
        
        Returns:
            , keyelement_id, valueTextStyleResult
        """
        import json
        import tempfile
        from services.prompts import get_batch_text_attribute_extraction_prompt
        
        thinking_budget = kwargs.get('thinking_budget', 1000)
        
        if not text_elements:
            return {}
        
        try:
            # Backend logic
            if isinstance(full_image, str):
                pil_image = Image.open(full_image)
                tmp_path = full_image  # Backend logic
                need_cleanup = False
            else:
                pil_image = full_image
                # Backend logic
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_path = tmp_file.name
                    pil_image.save(tmp_path)
                need_cleanup = True
            
            # Backend logic
            elements_for_prompt = []
            for elem in text_elements:
                elements_for_prompt.append({
                    'element_id': elem['element_id'],
                    'bbox': elem['bbox'],
                    'content': elem['content']
                })
            
            text_elements_json = json.dumps(elements_for_prompt, ensure_ascii=False, indent=2)
            
            # Backend logic
            prompt = get_batch_text_attribute_extraction_prompt(text_elements_json)
            
            # Backend logic
            try:
                result = self.ai_service.generate_json_with_image(
                    prompt=prompt,
                    image_path=tmp_path,
                    thinking_budget=thinking_budget
                )
                
                # Backend logic
                if isinstance(result, list):
                    result_list = result
                elif isinstance(result, dict):
                    # Backend logic
                    result_list = result.get('results', [result])
                else:
                    result_list = []
                
                # Backend logic
                return self._parse_batch_result(result_list, text_elements)

            except ValueError as e:
                if "không hỗ trợ đầu vào hình ảnh" in str(e):
                    raise RuntimeError(f"Mô hình trích xuất kiểu ảnh hiện tại không hỗ trợ đầu vào hình ảnh: {e}") from e
                raise RuntimeError(f"Nội dung trả về từ mô hình thị giác không thể phân tích: {e}") from e

            except Exception as e:
                raise RuntimeError(f"Gọi hàng loạt mô hình thị giác để trích xuất kiểu văn bản thất bại: {e}") from e
                
            finally:
                if need_cleanup:
                    import os
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
        
        except Exception as e:
            logger.error(f"Trích xuất hàng loạt thuộc tính văn bản thất bại: {e}", exc_info=True)
            raise
    
    def _parse_batch_result(
        self,
        result_list: List[Dict[str, Any]],
        original_elements: List[Dict[str, Any]]
    ) -> Dict[str, TextStyleResult]:
        """
         AI 
        
        Args:
            result_list: AI  JSON , 
            original_elements: ,  element_id
        
        Returns:
            , key  element_id, value  TextStyleResult
        """
        results = {}
        
        # Backend logic
        original_map = {elem['element_id']: elem for elem in original_elements}
        
        for item in result_list:
            try:
                element_id = item.get('element_id')
                if not element_id:
                    continue
                
                # Backend logic
                font_color_hex = item.get('font_color', '#000000')
                if isinstance(font_color_hex, str):
                    font_color_rgb = self._hex_to_rgb(font_color_hex)
                else:
                    font_color_rgb = (0, 0, 0)
                
                # Backend logic
                is_bold = bool(item.get('is_bold', False))
                is_italic = bool(item.get('is_italic', False))
                is_underline = bool(item.get('is_underline', False))
                
                # Backend logic
                text_alignment = item.get('text_alignment')
                if text_alignment not in ('left', 'center', 'right', 'justify', None):
                    text_alignment = None
                
                results[element_id] = TextStyleResult(
                    font_color_rgb=font_color_rgb,
                    is_bold=is_bold,
                    is_italic=is_italic,
                    is_underline=is_underline,
                    text_alignment=text_alignment,
                    confidence=0.9,
                    metadata={'source': 'batch_caption_model', 'raw_response': item}
                )
                
            except Exception as e:
                logger.warning(f"Phân tích phần tử {item.get('element_id', 'unknown')} kiểu dáng thất bại: {e}")
                continue
        
        logger.info(f"Hoàn tất phân tích hàng loạt: thành công {len(results)}/{len(original_elements)} phần tử")
        return results


class TextAttributeExtractorRegistry:
    """
    
    
    : 
    -  → CaptionModelTextAttributeExtractor
    -  → 
    -  → 
    
    : 
        >>> registry = TextAttributeExtractorRegistry()
        >>> registry.register('text', caption_extractor)
        >>> registry.register('title', title_extractor)
        >>> registry.register_default(caption_extractor)
        >>> 
        >>> extractor = registry.get_extractor('text')
        >>> extractor = registry.get_extractor('unknown_type')  # Backend logic
    """
    
    # Backend logic
    TEXT_TYPES = {'text', 'title', 'paragraph', 'heading', 'header', 'footer', 'list'}
    TABLE_TEXT_TYPES = {'table_cell'}
    
    def __init__(self):
        """ Backend docstring """
        self._type_mapping: Dict[str, TextAttributeExtractor] = {}
        self._default_extractor: Optional[TextAttributeExtractor] = None
    
    def register(self, element_type: str, extractor: TextAttributeExtractor) -> 'TextAttributeExtractorRegistry':
        """
        
        
        Args:
            element_type: Loại phần tử ( như 'text', 'title' v.v.) 
            extractor: 
        
        Returns:
            self, 
        """
        self._type_mapping[element_type] = extractor
        logger.debug(f"Đăng ký bộ trích xuất thuộc tính văn bản: {element_type} -> {extractor.__class__.__name__}")
        return self
    
    def register_types(self, element_types: List[str], extractor: TextAttributeExtractor) -> 'TextAttributeExtractorRegistry':
        """
        
        
        Args:
            element_types: 
            extractor: 
        
        Returns:
            self, 
        """
        for t in element_types:
            self.register(t, extractor)
        return self
    
    def register_default(self, extractor: TextAttributeExtractor) -> 'TextAttributeExtractorRegistry':
        """
         () 
        
        Args:
            extractor: 
        
        Returns:
            self, 
        """
        self._default_extractor = extractor
        logger.debug(f"Đăng ký bộ trích xuất thuộc tính văn bản mặc định: {extractor.__class__.__name__}")
        return self
    
    def get_extractor(self, element_type: Optional[str]) -> Optional[TextAttributeExtractor]:
        """
        
        
        Args:
            element_type: , None
        
        Returns:
            , 
        """
        if element_type is None:
            return self._default_extractor
        
        # Backend logic
        if element_type in self._type_mapping:
            return self._type_mapping[element_type]
        
        # Backend logic
        return self._default_extractor
    
    def get_all_extractors(self) -> List[TextAttributeExtractor]:
        """
         () 
        
        Returns:
            
        """
        extractors = list(set(self._type_mapping.values()))
        if self._default_extractor and self._default_extractor not in extractors:
            extractors.append(self._default_extractor)
        return extractors
    
    @classmethod
    def create_default(
        cls,
        caption_extractor: Optional[TextAttributeExtractor] = None
    ) -> 'TextAttributeExtractorRegistry':
        """
        
        
        : 
        -  → CaptionModelTextAttributeExtractor
        -  → 
        
        Args:
            caption_extractor: Caption Model
        
        Returns:
            
        """
        registry = cls()
        
        if not caption_extractor:
            logger.warning("TạoTextAttributeExtractorRegistrynhưng không cung cấp bất kỳextractor")
            return registry
        
        # Backend logic
        registry.register_default(caption_extractor)
        
        # Backend logic
        registry.register_types(list(cls.TEXT_TYPES), caption_extractor)
        registry.register_types(list(cls.TABLE_TEXT_TYPES), caption_extractor)
        
        logger.info(f"Tạo mặc địnhTextAttributeExtractorRegistry: "
                   f"Bộ trích xuất mặc định->{caption_extractor.__class__.__name__}")
        
        return registry