"""
 - 

: 
- ElementExtractor: 
- MinerUElementExtractor: MinerU
- BaiduOCRElementExtractor: OCR
- BaiduAccurateOCRElementExtractor: OCR () 
- ExtractorRegistry: 
"""
import os
import json
import logging
import tempfile
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Type
from pathlib import Path
from PIL import Image

from utils.latex_utils import latex_to_text

logger = logging.getLogger(__name__)


class ExtractionContext:
    """ Backend docstring """
    
    def __init__(
        self,
        result_dir: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            result_dir:  (MinerU) 
            metadata: 
        """
        self.result_dir = result_dir
        self.metadata = metadata or {}


class ExtractionResult:
    """ Backend docstring """

    def __init__(
        self,
        elements: List[Dict[str, Any]],
        context: Optional[ExtractionContext] = None,
        error: Optional[str] = None
    ):
        """
        Args:
            elements: 
            context:  () 
            error:  () 
        """
        self.elements = elements
        self.context = context or ExtractionContext()
        self.error = error

    @property
    def has_error(self) -> bool:
        """ Backend docstring """
        return self.error is not None


class ElementExtractor(ABC):
    """
    
    
    , : 
    - MinerU () 
    - OCR () 
    - PaddleOCR
    - Tesseract OCR
    - 
    """
    
    @abstractmethod
    def extract(
        self,
        image_path: str,
        element_type: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        
        
        Args:
            image_path: 
            element_type: Gợi ý loại phần tử ( như 'table', 'text', 'image' v.v.) , tùy chọn
            **kwargs: 
        
        Returns:
            ExtractionResult, : 
            - elements: , : 
                - bbox: List[float] -  [x0, y0, x1, y1]
                - type: str - Loại phần tử ('text', 'image', 'table', 'title' v.v.) 
                - content: Optional[str] - 
                - image_path: Optional[str] - 
                - metadata: Dict[str, Any] - 
            - context:  () 
        """
        pass
    
    @abstractmethod
    def supports_type(self, element_type: Optional[str]) -> bool:
        """
        
        
        Args:
            element_type: Loại phần tử ( như 'table', 'image' v.v.) , Nonebiểu thị chung
        
        Returns:
            
        """
        pass


class MinerUElementExtractor(ElementExtractor):
    """
    MinerU () 
    
    MinerU, , 
    : PDF, MinerU, 
    """
    
    def __init__(self, parser_service, upload_folder: Path):
        """
        MinerU
        
        Args:
            parser_service: FileParserService
            upload_folder: 
        """
        self._parser_service = parser_service
        self._upload_folder = upload_folder
    
    def supports_type(self, element_type: Optional[str]) -> bool:
        """ Backend docstring """
        return element_type != 'table_cell'
    
    def extract(
        self,
        image_path: str,
        element_type: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
         (PDFMinerU) 

        kwargs:
        - depth: int,  () 
        """
        depth = kwargs.get('depth', 0)

        # Backend logic
        img = Image.open(image_path)
        image_size = img.size  # (width, height)

        # Backend logic
        cached_dir = self._find_cache(image_path)
        if cached_dir:
            logger.info(f"{' ' * depth}Sử dụngMinerUbộ nhớ đệm")
            mineru_result_dir = cached_dir
            parse_error = None
        else:
            # Backend logic
            mineru_result_dir, parse_error = self._parse_image(image_path, depth)
            if not mineru_result_dir:
                return ExtractionResult(elements=[], error=parse_error)

        # Backend logic
        elements = self._extract_from_result(
            mineru_result_dir=mineru_result_dir,
            target_image_size=image_size,
            depth=depth
        )

        # Backend logic
        context = ExtractionContext(
            result_dir=mineru_result_dir,
            metadata={'source': 'mineru', 'image_size': image_size}
        )

        return ExtractionResult(elements=elements, context=context)
    
    def _find_cache(self, image_path: str) -> Optional[str]:
        """ Backend docstring """
        try:
            import hashlib
            import time
            
            img_path = Path(image_path)
            if not img_path.exists():
                return None
            
            mineru_files_dir = self._upload_folder / 'mineru_files'
            if not mineru_files_dir.exists():
                return None
            
            # Backend logic
            return None
            
        except Exception as e:
            logger.debug(f"Tìm bộ nhớ đệm thất bại: {e}")
            return None
    
    def _parse_image(self, image_path: str, depth: int) -> Tuple[Optional[str], Optional[str]]:
        """, MinerU

        Returns:
            Tuple of (result_dir, error_message)
        """
        from services.export_service import ExportService

        # Backend logic
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            pdf_path = tmp_pdf.name

        try:
            ExportService.create_pdf_from_images([image_path], output_file=pdf_path)

            # Backend logic
            image_id = str(uuid.uuid4())[:8]
            batch_id, markdown_content, extract_id, error_message, failed_image_count = \
                self._parser_service.parse_file(pdf_path, f"image_{image_id}.pdf")

            if error_message or not extract_id:
                logger.error(f"{' ' * depth}MinerUphân tích thất bại: {error_message}")
                return None, error_message or "MinerUphân tích thất bại, chưa trả vềextract_id"

            mineru_result_dir = (self._upload_folder / 'mineru_files' / extract_id).resolve()
            if not mineru_result_dir.exists():
                err = f"MinerUThư mục kết quả không tồn tại: {mineru_result_dir}"
                logger.error(f"{'  ' * depth}{err}")
                return None, err

            return str(mineru_result_dir), None

        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    
    def _extract_from_result(
        self,
        mineru_result_dir: str,
        target_image_size: Tuple[int, int],
        depth: int
    ) -> List[Dict[str, Any]]:
        """ Backend docstring """
        elements = []
        
        try:
            mineru_dir = Path(mineru_result_dir)
            
            # Backend logic
            layout_file = mineru_dir / 'layout.json'
            content_list_files = list(mineru_dir.glob("*_content_list.json"))
            
            if not layout_file.exists() or not content_list_files:
                logger.warning(f"layout.json hoặc content_list.jsonkhông tồn tại")
                return []
            
            with open(layout_file, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
            
            with open(content_list_files[0], 'r', encoding='utf-8') as f:
                content_list = json.load(f)
            
            # Backend logic
            if 'pdf_info' not in layout_data or not layout_data['pdf_info']:
                return []
            
            page_info = layout_data['pdf_info'][0]
            source_page_size = page_info.get('page_size', target_image_size)
            
            # Backend logic
            scale_x = target_image_size[0] / source_page_size[0]
            scale_y = target_image_size[1] / source_page_size[1]
            
            # Backend logic
            def process_block(block):
                bbox = block.get('bbox')
                block_type = block.get('type', 'text')
                equation_types = {'equation', 'interline_equation', 'inline_equation'}
                is_equation_source_block = block_type in equation_types
                
                if not bbox or len(bbox) != 4:
                    return None
                
                # Backend logic
                if block_type in ['header', 'footer']:
                    if block.get('lines'):
                        # Backend logic
                        all_text = []
                        for line in block['lines']:
                            for span in line.get('spans', []):
                                if span.get('type') == 'text' and span.get('content'):
                                    all_text.append(span['content'])
                        # Backend logic
                        combined_text = ''.join(all_text).strip()
                        if combined_text == '#':
                            return None
                
                # Backend logic
                scaled_bbox = [
                    bbox[0] * scale_x,
                    bbox[1] * scale_y,
                    bbox[2] * scale_x,
                    bbox[3] * scale_y
                ]
                
                # Backend logic
                actual_content_type = 'text' if is_equation_source_block else block_type
                if block_type in ['header', 'footer']:
                    # Backend logic
                    has_image = False
                    if block.get('blocks'):
                        for sub_block in block['blocks']:
                            if sub_block.get('type') == 'image_body':
                                has_image = True
                                break
                    
                    # Backend logic
                    has_text = False
                    if block.get('lines'):
                        for line in block['lines']:
                            for span in line.get('spans', []):
                                if span.get('type') in ['text', 'inline_equation'] and span.get('content', '').strip():
                                    has_text = True
                                    break
                            if has_text:
                                break
                    
                    # Backend logic
                    if has_image and not has_text:
                        actual_content_type = 'image'
                    elif has_text:
                        actual_content_type = 'text'  # Backend logic
                    else:
                        # Backend logic
                        actual_content_type = 'text'
                
                # Backend logic
                def extract_text_from_lines(lines, preserve_equations=False):
                    """ Backend docstring """
                    line_texts = []
                    for line in lines:
                        span_texts = []
                        for span in line.get('spans', []):
                            span_type = span.get('type', '')
                            span_content = span.get('content', '')
                            
                            if span_type == 'text' and span_content:
                                span_texts.append(span_content)
                            elif span_type in equation_types and span_content:
                                if preserve_equations:
                                    span_texts.append(span_content)
                                else:
                                    converted = latex_to_text(span_content)
                                    span_texts.append(converted)
                        
                        if span_texts:
                            line_text = ''.join(span_texts)
                            line_texts.append(line_text)
                    return line_texts
                
                # Backend logic
                content = None
                if actual_content_type in ['text', 'title', 'table_caption', 'image_caption']:
                    if block.get('lines'):
                        line_texts = extract_text_from_lines(
                            block['lines'],
                            preserve_equations=is_equation_source_block
                        )
                        if line_texts:
                            content = '\n'.join(line_texts).strip()

                elif actual_content_type == 'list':
                    # Backend logic
                    if block.get('blocks'):
                        all_line_texts = []
                        for sub_block in block['blocks']:
                            if sub_block.get('lines'):
                                sub_texts = extract_text_from_lines(sub_block['lines'])
                                all_line_texts.extend(sub_texts)
                        if all_line_texts:
                            content = '\n'.join(all_line_texts).strip()
                
                # Backend logic
                img_path = None
                if actual_content_type in ['image', 'table']:
                    if block.get('blocks'):
                        for sub_block in block['blocks']:
                            for line in sub_block.get('lines', []):
                                for span in line.get('spans', []):
                                    if span.get('image_path'):
                                        relative_path = span['image_path']
                                        if not relative_path.startswith('images/'):
                                            relative_path = 'images/' + relative_path
                                        # Backend logic
                                        abs_path = mineru_dir / relative_path
                                        if abs_path.exists():
                                            img_path = str(abs_path)
                                        break
                                if img_path:
                                    break
                            if img_path:
                                break
                
                return {
                    'bbox': scaled_bbox,
                    'type': actual_content_type,  # Backend logic
                    'content': content,
                    'image_path': img_path,  # Backend logic
                    'metadata': {
                        **block,
                        'original_type': block_type  # Backend logic
                    }
                }
            
            # Backend logic
            for block in page_info.get('para_blocks', []):
                element = process_block(block)
                if element:
                    elements.append(element)
                # Backend logic
                # Backend logic
                block_type = block.get('type', '')
                if block_type != 'list':
                    for sub_block in block.get('blocks', []):
                        sub_elem = process_block(sub_block)
                        if sub_elem:
                            elements.append(sub_elem)
            
            # Backend logic
            for block in page_info.get('discarded_blocks', []):
                element = process_block(block)
                if element:
                    elements.append(element)
                # Backend logic
                # Backend logic
                block_type = block.get('type', '')
                if block_type != 'list':
                    for sub_block in block.get('blocks', []):
                        sub_elem = process_block(sub_block)
                        if sub_elem:
                            elements.append(sub_elem)
            
            logger.info(f"MinerUđã trích xuất {len(elements)} phần tử")
        
        except Exception as e:
            logger.error(f"MinerUTrích xuất phần tử thất bại: {e}", exc_info=True)
        
        return elements


class BaiduOCRElementExtractor(ElementExtractor):
    """
    OCR
    
    , 
    : OCR
    """
    
    def __init__(self, baidu_table_ocr_provider):
        """
        OCR
        
        Args:
            baidu_table_ocr_provider: OCR Provider
        """
        self._ocr_provider = baidu_table_ocr_provider
    
    def supports_type(self, element_type: Optional[str]) -> bool:
        """ Backend docstring """
        return element_type in ['table', 'table_cell', None]
    
    def extract(
        self,
        image_path: str,
        element_type: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        
        
        kwargs:
        - depth: int,  () 
        - shrink_cells: bool, , True
        """
        depth = kwargs.get('depth', 0)
        shrink_cells = kwargs.get('shrink_cells', True)
        
        elements = []
        
        try:
            # Backend logic
            ocr_result = self._ocr_provider.recognize_table(
                image_path,
                cell_contents=True
            )
            
            table_cells = ocr_result.get('cells', [])
            # Backend logic
            table_img_size = ocr_result.get('image_size')
            if not table_img_size:
                img = Image.open(image_path)
                table_img_size = img.size
            
            logger.info(f"{' ' * depth}BaiduOCRnhận diện được {len(table_cells)} ô bảng")
            
            # Backend logic
            body_cells = [cell for cell in table_cells if cell.get('section') == 'body']
            valid_cells = [cell for cell in body_cells if cell.get('text', '').strip()]
            
            if not valid_cells:
                logger.warning(f"{' ' * depth}Không có ô hợp lệ")
                return ExtractionResult(elements=elements)
            
            # Backend logic
            cell_bboxes = []
            if shrink_cells:
                cell_bboxes = self._shrink_cells_to_avoid_overlap(valid_cells, depth)
            else:
                cell_bboxes = [cell.get('bbox', [0, 0, 0, 0]) for cell in valid_cells]
            
            # Backend logic
            for idx, (cell, bbox) in enumerate(zip(valid_cells, cell_bboxes)):
                elements.append({
                    'bbox': bbox,
                    'type': 'table_cell',
                    'content': cell.get('text', ''),
                    'image_path': None,
                    'metadata': {
                        'row_start': cell.get('row_start'),
                        'row_end': cell.get('row_end'),
                        'col_start': cell.get('col_start'),
                        'col_end': cell.get('col_end'),
                        'table_idx': cell.get('table_idx', 0)
                    }
                })
            
            logger.info(f"{' ' * depth}BaiduOCRđã trích xuất {len(elements)} phần tử ô bảng")

        except Exception as e:
            error_msg = f"BaiduOCRnhận diện thất bại: {e}"
            logger.error(f"{'  ' * depth}{error_msg}", exc_info=True)
            return ExtractionResult(elements=elements, error=error_msg)

        # Backend logic
        return ExtractionResult(elements=elements)
    
    def _shrink_cells_to_avoid_overlap(
        self,
        valid_cells: List[Dict],
        depth: int
    ) -> List[List[float]]:
        """ Backend docstring """
        TARGET_MIN_GAP = 6
        SHRINK_STEP = 0.02
        MIN_SIZE_RATIO = 0.4
        MAX_ITERATIONS = 20
        
        cell_data = []
        for cell in valid_cells:
            bbox = cell.get('bbox', [0, 0, 0, 0])
            x0, y0, x1, y1 = bbox
            cell_data.append({
                'cell': cell,
                'original_bbox': bbox,
                'current_bbox': [float(x0), float(y0), float(x1), float(y1)],
                'original_width': x1 - x0,
                'original_height': y1 - y0
            })
        
        def calculate_min_gap(cell_data):
            if len(cell_data) <= 1:
                return float('inf')
            
            min_gap = float('inf')
            for i, data1 in enumerate(cell_data):
                x0_1, y0_1, x1_1, y1_1 = data1['current_bbox']
                for j, data2 in enumerate(cell_data):
                    if i >= j:
                        continue
                    x0_2, y0_2, x1_2, y1_2 = data2['current_bbox']
                    
                    x_overlap = not (x1_1 <= x0_2 or x1_2 <= x0_1)
                    y_overlap = not (y1_1 <= y0_2 or y1_2 <= y0_1)
                    
                    if x_overlap and y_overlap:
                        overlap_x = min(x1_1, x1_2) - max(x0_1, x0_2)
                        overlap_y = min(y1_1, y1_2) - max(y0_1, y0_2)
                        min_gap = min(min_gap, -min(overlap_x, overlap_y))
                    elif x_overlap:
                        gap = y0_2 - y1_1 if y1_1 <= y0_2 else y0_1 - y1_2
                        min_gap = min(min_gap, gap)
                    elif y_overlap:
                        gap = x0_2 - x1_1 if x1_1 <= x0_2 else x0_1 - x1_2
                        min_gap = min(min_gap, gap)
            
            return min_gap
        
        iteration = 0
        total_shrink_ratio = 0
        
        while iteration < MAX_ITERATIONS:
            current_min_gap = calculate_min_gap(cell_data)
            
            if current_min_gap >= TARGET_MIN_GAP:
                if iteration == 0:
                    logger.info(f"{' ' * depth}Khoảng cách giữa các ô đã đạt yêu cầu (tối thiểu={current_min_gap:.1f}px) , không cần thu hẹp")
                else:
                    logger.info(f"{' ' * depth}Hoàn tất thu hẹp: {iteration}vòng lặp, khoảng cách tối thiểu={current_min_gap:.1f}px")
                break
            
            all_cells_can_shrink = True
            for data in cell_data:
                x0, y0, x1, y1 = data['current_bbox']
                current_width = x1 - x0
                current_height = y1 - y0
                
                min_width = data['original_width'] * MIN_SIZE_RATIO
                min_height = data['original_height'] * MIN_SIZE_RATIO
                
                if current_width <= min_width or current_height <= min_height:
                    all_cells_can_shrink = False
                    break
                
                shrink_x = max(0.5, current_width * SHRINK_STEP)
                shrink_y = max(0.5, current_height * SHRINK_STEP)
                
                new_x0 = x0 + shrink_x
                new_y0 = y0 + shrink_y
                new_x1 = x1 - shrink_x
                new_y1 = y1 - shrink_y
                
                if (new_x1 - new_x0) < min_width:
                    new_x0 = x0 + (current_width - min_width) / 2
                    new_x1 = x1 - (current_width - min_width) / 2
                if (new_y1 - new_y0) < min_height:
                    new_y0 = y0 + (current_height - min_height) / 2
                    new_y1 = y1 - (current_height - min_height) / 2
                
                data['current_bbox'] = [new_x0, new_y0, new_x1, new_y1]
            
            if not all_cells_can_shrink:
                logger.warning(f"{' ' * depth}Đã chạm giới hạn kích thước tối thiểu, khoảng cách tối thiểu hiện tại={current_min_gap:.1f}px")
                break
            
            total_shrink_ratio += SHRINK_STEP
            iteration += 1
        
        if iteration >= MAX_ITERATIONS:
            current_min_gap = calculate_min_gap(cell_data)
            logger.warning(f"{' ' * depth}Đã đạt số vòng lặp tối đa, khoảng cách tối thiểu hiện tại={current_min_gap:.1f}px")
        
        return [data['current_bbox'] for data in cell_data]


class BaiduAccurateOCRElementExtractor(ElementExtractor):
    """
    OCR
    
    , 
    , , 
    """
    
    def __init__(self, baidu_accurate_ocr_provider):
        """
        OCR
        
        Args:
            baidu_accurate_ocr_provider: OCR Provider
        """
        self._ocr_provider = baidu_accurate_ocr_provider
    
    def supports_type(self, element_type: Optional[str]) -> bool:
        """ Backend docstring """
        return element_type in ['text', 'title', 'paragraph', None]
    
    def extract(
        self,
        image_path: str,
        element_type: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        
        
        kwargs:
        - depth: int,  () 
        - language_type: str, Loại ngôn ngữ nhận diện, mặc định'CHN_ENG'
        - recognize_granularity: str, Có định vị trí từng ký tự đơn hay không, 'big' hoặc 'small'
        - detect_direction: bool, 
        - paragraph: bool, 
        """
        depth = kwargs.get('depth', 0)
        language_type = kwargs.get('language_type', 'CHN_ENG')
        recognize_granularity = kwargs.get('recognize_granularity', 'big')
        detect_direction = kwargs.get('detect_direction', False)
        paragraph = kwargs.get('paragraph', False)
        
        elements = []
        
        try:
            # Backend logic
            ocr_result = self._ocr_provider.recognize(
                image_path,
                language_type=language_type,
                recognize_granularity=recognize_granularity,
                detect_direction=detect_direction,
                paragraph=paragraph,
                probability=True,  # Backend logic
            )
            
            text_lines = ocr_result.get('text_lines', [])
            image_size = ocr_result.get('image_size', (0, 0))
            direction = ocr_result.get('direction', None)
            
            logger.info(f"{' ' * depth}Baidu độ chính xác caoOCRnhận diện được {len(text_lines)} dòng văn bản")
            
            # Backend logic
            valid_lines = [line for line in text_lines if line.get('text', '').strip()]
            
            if not valid_lines:
                logger.warning(f"{' ' * depth}Không nhận diện được văn bản hợp lệ")
                return ExtractionResult(elements=elements)
            
            # Backend logic
            for idx, line in enumerate(valid_lines):
                bbox = line.get('bbox', [0, 0, 0, 0])
                text = line.get('text', '')
                
                element = {
                    'bbox': bbox,
                    'type': 'text',
                    'content': text,
                    'image_path': None,
                    'metadata': {
                        'line_idx': idx,
                        'source': 'baidu_accurate_ocr',
                    }
                }
                
                # Backend logic
                if 'probability' in line:
                    element['metadata']['probability'] = line['probability']
                
                # Backend logic
                if 'chars' in line:
                    element['metadata']['chars'] = line['chars']
                
                # Backend logic
                if 'vertexes_location' in line:
                    element['metadata']['vertexes_location'] = line['vertexes_location']
                
                elements.append(element)
            
            logger.info(f"{' ' * depth}Baidu độ chính xác caoOCRđã trích xuất {len(elements)} phần tử văn bản")
            
            # Backend logic
            context = ExtractionContext(
                metadata={
                    'source': 'baidu_accurate_ocr',
                    'image_size': image_size,
                    'direction': direction,
                }
            )
            
            return ExtractionResult(elements=elements, context=context)

        except Exception as e:
            error_msg = f"Baidu độ chính xác caoOCRnhận diện thất bại: {e}"
            logger.error(f"{'  ' * depth}{error_msg}", exc_info=True)
            return ExtractionResult(elements=elements, error=error_msg)


class ExtractorRegistry:
    """
    
    
    : 
    - / → MinerU 
    -  → OCR
    -  → 
    
    : 
        >>> registry = ExtractorRegistry()
        >>> registry.register('table', baidu_ocr_extractor)
        >>> registry.register('image', mineru_extractor)
        >>> registry.register_default(mineru_extractor)
        >>> 
        >>> extractor = registry.get_extractor('table')  # Backend logic
        >>> extractor = registry.get_extractor('chart')  # Backend logic
    """
    
    # Backend logic
    TABLE_TYPES = {'table', 'table_cell'}
    IMAGE_TYPES = {'image', 'figure', 'chart', 'diagram'}
    TEXT_TYPES = {'text', 'title', 'paragraph', 'header', 'footer', 'list'}
    
    def __init__(self):
        """ Backend docstring """
        self._type_mapping: Dict[str, ElementExtractor] = {}
        self._default_extractor: Optional[ElementExtractor] = None
    
    def register(self, element_type: str, extractor: ElementExtractor) -> 'ExtractorRegistry':
        """
        
        
        Args:
            element_type: Loại phần tử ( như 'table', 'image' v.v.) 
            extractor: 
        
        Returns:
            self, 
        """
        self._type_mapping[element_type] = extractor
        logger.debug(f"Đăng ký bộ trích xuất: {element_type} -> {extractor.__class__.__name__}")
        return self
    
    def register_types(self, element_types: List[str], extractor: ElementExtractor) -> 'ExtractorRegistry':
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
    
    def register_default(self, extractor: ElementExtractor) -> 'ExtractorRegistry':
        """
         () 
        
        Args:
            extractor: 
        
        Returns:
            self, 
        """
        self._default_extractor = extractor
        logger.debug(f"Đăng ký bộ trích xuất mặc định: {extractor.__class__.__name__}")
        return self
    
    def get_extractor(self, element_type: Optional[str]) -> Optional[ElementExtractor]:
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
    
    def get_all_extractors(self) -> List[ElementExtractor]:
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
        mineru_extractor: ElementExtractor,
        baidu_ocr_extractor: Optional[ElementExtractor] = None,
        baidu_accurate_ocr_extractor: Optional[ElementExtractor] = None
    ) -> 'ExtractorRegistry':
        """
        
        
        : 
        -  → OCR () 
        -  → OCR () , MinerU
        -  → MinerU
        -  → MinerU () 
        
        Args:
            mineru_extractor: MinerU
            baidu_ocr_extractor: OCR () 
            baidu_accurate_ocr_extractor: OCR () 
        
        Returns:
            
        """
        registry = cls()
        
        # Backend logic
        registry.register_default(mineru_extractor)
        
        # Backend logic
        registry.register_types(list(cls.IMAGE_TYPES), mineru_extractor)
        
        # Backend logic
        table_extractor = baidu_ocr_extractor if baidu_ocr_extractor else mineru_extractor
        registry.register_types(list(cls.TABLE_TYPES), table_extractor)
        
        # Backend logic
        text_extractor = baidu_accurate_ocr_extractor if baidu_accurate_ocr_extractor else mineru_extractor
        registry.register_types(list(cls.TEXT_TYPES), text_extractor)
        
        logger.info(f"Tạo mặc địnhExtractorRegistry: "
                   f"Bảng->{table_extractor.__class__.__name__}, "
                   f"văn bản->{text_extractor.__class__.__name__}, "
                   f"hình ảnh->{mineru_extractor.__class__.__name__}")
        
        return registry