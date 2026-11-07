"""
 - MinerUOCR

: 
1. MinerUOCR () 
2. : 
   - bboxOCR bbox → OCR bbox
   - bboxOCR bbox → OCR bbox, MinerUbbox
   - bboxOCR bbox → OCR, MinerU bbox
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

from .extractors import (
    ElementExtractor, 
    ExtractionResult, 
    ExtractionContext,
    MinerUElementExtractor,
    BaiduAccurateOCRElementExtractor
)

logger = logging.getLogger(__name__)


class BBoxUtils:
    """ Backend docstring """
    
    @staticmethod
    def is_contained(inner_bbox: List[float], outer_bbox: List[float], threshold: float = 0.8) -> bool:
        """
        inner_bboxouter_bbox
        
        Args:
            inner_bbox: bbox [x0, y0, x1, y1]
            outer_bbox: bbox [x0, y0, x1, y1]
            threshold: , inner_bboxouter_bbox, 0.8
        
        Returns:
            
        """
        if not inner_bbox or not outer_bbox:
            return False
        
        ix0, iy0, ix1, iy1 = inner_bbox
        ox0, oy0, ox1, oy1 = outer_bbox
        
        # Backend logic
        inter_x0 = max(ix0, ox0)
        inter_y0 = max(iy0, oy0)
        inter_x1 = min(ix1, ox1)
        inter_y1 = min(iy1, oy1)
        
        if inter_x1 <= inter_x0 or inter_y1 <= inter_y0:
            return False
        
        # Backend logic
        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
        
        # Backend logic
        inner_area = (ix1 - ix0) * (iy1 - iy0)
        
        if inner_area <= 0:
            return False
        
        # Backend logic
        return (inter_area / inner_area) >= threshold
    
    @staticmethod
    def has_intersection(bbox1: List[float], bbox2: List[float], min_overlap_ratio: float = 0.1) -> bool:
        """
        bbox
        
        Args:
            bbox1: bbox [x0, y0, x1, y1]
            bbox2: bbox [x0, y0, x1, y1]
            min_overlap_ratio:  (bbox) , 0.1
        
        Returns:
            
        """
        if not bbox1 or not bbox2:
            return False
        
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2
        
        # Backend logic
        inter_x0 = max(x0_1, x0_2)
        inter_y0 = max(y0_1, y0_2)
        inter_x1 = min(x1_1, x1_2)
        inter_y1 = min(y1_1, y1_2)
        
        if inter_x1 <= inter_x0 or inter_y1 <= inter_y0:
            return False
        
        # Backend logic
        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
        
        # Backend logic
        area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
        area2 = (x1_2 - x0_2) * (y1_2 - y0_2)
        
        # Backend logic
        min_area = min(area1, area2)
        
        if min_area <= 0:
            return False
        
        # Backend logic
        return (inter_area / min_area) >= min_overlap_ratio
    
    @staticmethod
    def get_intersection_ratio(bbox1: List[float], bbox2: List[float]) -> Tuple[float, float]:
        """
        bbox
        
        Args:
            bbox1: bbox
            bbox2: bbox
        
        Returns:
            (bbox1, bbox2)
        """
        if not bbox1 or not bbox2:
            return (0.0, 0.0)
        
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2
        
        # Backend logic
        inter_x0 = max(x0_1, x0_2)
        inter_y0 = max(y0_1, y0_2)
        inter_x1 = min(x1_1, x1_2)
        inter_y1 = min(y1_1, y1_2)
        
        if inter_x1 <= inter_x0 or inter_y1 <= inter_y0:
            return (0.0, 0.0)
        
        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
        area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
        area2 = (x1_2 - x0_2) * (y1_2 - y0_2)
        
        ratio1 = inter_area / area1 if area1 > 0 else 0.0
        ratio2 = inter_area / area2 if area2 > 0 else 0.0
        
        return (ratio1, ratio2)


class HybridElementExtractor(ElementExtractor):
    """
    
    
    MinerUOCR, : 
    - MinerU
    - OCR
    
    : 
    1. bboxOCR bbox →  () 
    2. bboxOCR bbox → OCR, MinerUbbox
    3.  () OCR bbox → OCR, MinerU bbox
    """
    
    # Backend logic
    IMAGE_TYPES = {'image', 'figure', 'chart', 'diagram'}
    TABLE_TYPES = {'table', 'table_cell'}
    TEXT_TYPES = {'text', 'title', 'paragraph', 'header', 'footer', 'list'}
    
    def __init__(
        self,
        mineru_extractor: MinerUElementExtractor,
        baidu_ocr_extractor: BaiduAccurateOCRElementExtractor,
        contain_threshold: float = 0.8,
        intersection_threshold: float = 0.3
    ):
        """
        
        
        Args:
            mineru_extractor: MinerU
            baidu_ocr_extractor: OCR
            contain_threshold: , 0.8 (80%) 
            intersection_threshold: , 0.3 (30%) 
        """
        self._mineru_extractor = mineru_extractor
        self._baidu_ocr_extractor = baidu_ocr_extractor
        self._contain_threshold = contain_threshold
        self._intersection_threshold = intersection_threshold
    
    def supports_type(self, element_type: Optional[str]) -> bool:
        """ Backend docstring """
        return True
    
    def extract(
        self,
        image_path: str,
        element_type: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
         () 
        
        : 
        1. MinerU
        2. OCR
        3. 
        
        Args:
            image_path: 
            element_type:  () 
            **kwargs: 
                - depth: 
                - language_type: OCR
        
        Returns:
            ExtractionResult
        """
        depth = kwargs.get('depth', 0)
        indent = '  ' * depth
        
        logger.info(f"{indent}🔀 Bắt đầu trích xuất kết hợp: {image_path}")
        
        # Backend logic
        logger.info(f"{indent}📄🔤 Step 1: MinerU + BaiduOCR nhận diện song song...")
        
        mineru_result = None
        baidu_result = None
        mineru_error = None
        baidu_error = None

        def run_mineru():
            return self._mineru_extractor.extract(image_path, element_type, **kwargs)

        def run_baidu_ocr():
            return self._baidu_ocr_extractor.extract(image_path, element_type, **kwargs)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_mineru = executor.submit(run_mineru)
            future_baidu = executor.submit(run_baidu_ocr)

            # Backend logic
            for future in as_completed([future_mineru, future_baidu]):
                try:
                    if future == future_mineru:
                        mineru_result = future.result()
                        # Backend logic
                        if mineru_result.has_error:
                            mineru_error = mineru_result.error
                            logger.error(f"{indent} ❌ MinerUlỗi trích xuất: {mineru_error}")
                        else:
                            logger.info(f"{indent} ✅ MinerUnhận diện được {len(mineru_result.elements)} phần tử")
                    else:
                        baidu_result = future.result()
                        if baidu_result.has_error:
                            baidu_error = baidu_result.error
                            logger.error(f"{indent} ❌ BaiduOCRlỗi trích xuất: {baidu_error}")
                        else:
                            logger.info(f"{indent} ✅ BaiduOCRnhận diện được {len(baidu_result.elements)} phần tử")
                except Exception as e:
                    if future == future_mineru:
                        mineru_error = str(e)
                        logger.error(f"{indent} ❌ MinerUtrích xuất thất bại: {e}")
                    else:
                        baidu_error = str(e)
                        logger.error(f"{indent} ❌ BaiduOCRtrích xuất thất bại: {e}")

        # Backend logic
        if mineru_result is None:
            mineru_result = ExtractionResult(elements=[], error=mineru_error)
        if baidu_result is None:
            baidu_result = ExtractionResult(elements=[], error=baidu_error)
        
        mineru_elements = mineru_result.elements
        baidu_elements = baidu_result.elements

        # Backend logic
        logger.info(f"{indent}🔧 Step 2: Gộp kết quả...")
        merged_elements = self._merge_results(mineru_elements, baidu_elements, depth)
        logger.info(f"{indent} Sau khi gộp có tổng cộng {len(merged_elements)} phần tử")

        # Backend logic
        errors = []
        if mineru_result.has_error:
            errors.append(f"MinerU: {mineru_result.error}")
        if baidu_result.has_error:
            errors.append(f"BaiduOCR: {baidu_result.error}")
        combined_error = "; ".join(errors) if errors else None

        # Backend logic
        context = ExtractionContext(
            result_dir=mineru_result.context.result_dir,
            metadata={
                'source': 'hybrid',
                'mineru_count': len(mineru_elements),
                'baidu_count': len(baidu_elements),
                'merged_count': len(merged_elements),
                'mineru_error': mineru_result.error,
                'baidu_error': baidu_result.error,
                **mineru_result.context.metadata
            }
        )

        return ExtractionResult(elements=merged_elements, context=context, error=combined_error)
    
    def _merge_results(
        self,
        mineru_elements: List[Dict[str, Any]],
        baidu_elements: List[Dict[str, Any]],
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        MinerUOCR
        
        : 
        1. bboxOCR bbox → OCR bbox
        2. bboxOCR bbox → OCR bbox, MinerUbbox
        3. OCR bbox → OCR, MinerU bbox
        
        Args:
            mineru_elements: MinerU
            baidu_elements: OCR
            depth:  () 
        
        Returns:
            
        """
        indent = '  ' * depth
        
        # Backend logic
        image_elements = []
        table_elements = []
        other_elements = []
        
        for elem in mineru_elements:
            elem_type = elem.get('type', '')
            if elem_type in self.IMAGE_TYPES:
                image_elements.append(elem)
            elif elem_type in self.TABLE_TYPES:
                table_elements.append(elem)
            else:
                other_elements.append(elem)
        
        logger.info(f"{indent} MinerUphân loại: hình ảnh={len(image_elements)}, Bảng={len(table_elements)}, khác={len(other_elements)}")
        
        # Backend logic
        baidu_to_keep = set(range(len(baidu_elements)))  # Backend logic
        baidu_in_table = set()  # Backend logic
        
        # Backend logic
        for img_elem in image_elements:
            img_bbox = img_elem.get('bbox', [])
            for idx, baidu_elem in enumerate(baidu_elements):
                baidu_bbox = baidu_elem.get('bbox', [])
                if BBoxUtils.is_contained(baidu_bbox, img_bbox, self._contain_threshold):
                    baidu_to_keep.discard(idx)
                    logger.debug(f"{indent} BaiduOCR[{idx}]nằm trong vùng ảnh, Xóa")
        
        # Backend logic
        tables_to_remove = set()
        for table_idx, table_elem in enumerate(table_elements):
            table_bbox = table_elem.get('bbox', [])
            has_contained_text = False
            for idx, baidu_elem in enumerate(baidu_elements):
                baidu_bbox = baidu_elem.get('bbox', [])
                if BBoxUtils.is_contained(baidu_bbox, table_bbox, self._contain_threshold):
                    baidu_in_table.add(idx)
                    has_contained_text = True
                    logger.debug(f"{indent} BaiduOCR[{idx}]nằm trong vùng ảnh, Xóa")
            
            if has_contained_text:
                tables_to_remove.add(table_idx)
                logger.debug(f"{indent} Bảng[{table_idx}]có văn bản, Xóa bảngbbox")
        
        # Backend logic
        other_to_remove = set()
        for other_idx, other_elem in enumerate(other_elements):
            other_bbox = other_elem.get('bbox', [])
            for idx, baidu_elem in enumerate(baidu_elements):
                if idx not in baidu_to_keep:
                    continue
                baidu_bbox = baidu_elem.get('bbox', [])
                if BBoxUtils.has_intersection(other_bbox, baidu_bbox, self._intersection_threshold):
                    other_to_remove.add(other_idx)
                    logger.debug(f"{indent} MinerUkhác[{other_idx}]và BaiduOCR[{idx}]có giao nhau, sử dụng BaiduOCR")
                    break
        
        # Backend logic
        merged = []
        
        # Backend logic
        for elem in image_elements:
            elem_copy = elem.copy()
            elem_copy['metadata'] = elem_copy.get('metadata', {}).copy()
            elem_copy['metadata']['source'] = 'mineru'
            merged.append(elem_copy)
        
        # Backend logic
        for idx, elem in enumerate(table_elements):
            if idx not in tables_to_remove:
                elem_copy = elem.copy()
                elem_copy['metadata'] = elem_copy.get('metadata', {}).copy()
                elem_copy['metadata']['source'] = 'mineru'
                merged.append(elem_copy)
        
        # Backend logic
        for idx, elem in enumerate(other_elements):
            if idx not in other_to_remove:
                elem_copy = elem.copy()
                elem_copy['metadata'] = elem_copy.get('metadata', {}).copy()
                elem_copy['metadata']['source'] = 'mineru'
                merged.append(elem_copy)
        
        # Backend logic
        for idx in baidu_to_keep:
            elem = baidu_elements[idx]
            elem_copy = elem.copy()
            elem_copy['metadata'] = elem_copy.get('metadata', {}).copy()
            elem_copy['metadata']['source'] = 'baidu_ocr'
            if idx in baidu_in_table:
                elem_copy['metadata']['in_table'] = True
            merged.append(elem_copy)
        
        logger.info(f"{indent} Gộp kết quả: Giữ lại ảnh={len(image_elements)}, "
                   f"Giữ lại bảng={len(table_elements) - len(tables_to_remove)}, "
                   f"giữ lạiMinerUkhác={len(other_elements) - len(other_to_remove)}, "
                   f"Giữ lại BaiduOCR={len(baidu_to_keep)}")
        
        return merged


def create_hybrid_extractor(
    mineru_extractor: Optional[MinerUElementExtractor] = None,
    baidu_ocr_extractor: Optional[BaiduAccurateOCRElementExtractor] = None,
    parser_service: Optional[Any] = None,
    upload_folder: Optional[Any] = None,
    contain_threshold: float = 0.8,
    intersection_threshold: float = 0.3
) -> Optional[HybridElementExtractor]:
    """
    
    
    Args:
        mineru_extractor: MinerU (, ) 
        baidu_ocr_extractor: OCR (, ) 
        parser_service: FileParserService (MinerU) 
        upload_folder:  (MinerU) 
        contain_threshold: 
        intersection_threshold: 
    
    Returns:
        HybridElementExtractor, None
    """
    from pathlib import Path
    
    # Backend logic
    if mineru_extractor is None:
        if parser_service is None or upload_folder is None:
            logger.error("Tạo bộ trích xuất kết hợp cần cung cấp parser_service và upload_folder, hoặc cung cấp trực tiếp mineru_extractor")
            return None
        
        if isinstance(upload_folder, str):
            upload_folder = Path(upload_folder)
        
        mineru_extractor = MinerUElementExtractor(parser_service, upload_folder)
        logger.info("✅ MinerUĐã tạo bộ trích xuất")
    
    # Backend logic
    if baidu_ocr_extractor is None:
        try:
            from services.ai_providers.ocr import create_baidu_accurate_ocr_provider
            baidu_provider = create_baidu_accurate_ocr_provider()
            if baidu_provider is None:
                logger.warning("Không thể tạo Baidu độ chính xác caoOCR Provider")
                return None
            baidu_ocr_extractor = BaiduAccurateOCRElementExtractor(baidu_provider)
            logger.info("✅ Baidu độ chính xác caoOCRĐã tạo bộ trích xuất")
        except Exception as e:
            logger.error(f"Tạo Baidu độ chính xác caoOCRbộ trích xuất thất bại: {e}")
            return None
    
    return HybridElementExtractor(
        mineru_extractor=mineru_extractor,
        baidu_ocr_extractor=baidu_ocr_extractor,
        contain_threshold=contain_threshold,
        intersection_threshold=intersection_threshold
    )