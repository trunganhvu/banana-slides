"""
 - 

: 
1.  - , 
2.  - 
3.  - 
4.  - 
"""
import logging
import math
import uuid
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from .data_models import BBox, EditableElement, EditableImage
from .coordinate_mapper import CoordinateMapper
from .extractors import ElementExtractor, ExtractionResult
from .inpaint_providers import InpaintProvider
from .factories import ServiceConfig
from .helpers import (
    collect_bboxes_from_elements,
    should_recurse_into_element,
    crop_element_from_image,
    should_extract_subject,
)

logger = logging.getLogger(__name__)


class ImageEditabilityService:
    """
    
    
    ,  make_image_editable()
    , 
    
    Example:
        >>> config = ServiceConfig.from_defaults(mineru_token="xxx")
        >>> service = ImageEditabilityService(config)
        >>> 
        >>> # Backend logic
        >>> result = service.make_image_editable("image.png")
        >>> 
        >>> # Backend logic
        >>> from concurrent.futures import ThreadPoolExecutor
        >>> with ThreadPoolExecutor() as executor:
        ...     futures = [executor.submit(service.make_image_editable, img) 
        ...                for img in image_paths]
        ...     results = [f.result() for f in futures]
    """
    
    def __init__(self, config: ServiceConfig):
        """
        
        
        Args:
            config: ServiceConfig, 
        """
        # Backend logic
        self._upload_folder = config.upload_folder
        self._extractor_registry = config.extractor_registry
        self._inpaint_registry = config.inpaint_registry
        self._max_depth = config.max_depth
        self._min_image_size = config.min_image_size
        self._min_image_area = config.min_image_area
        self._max_child_coverage_ratio = 0.85
        self._segmentation_provider = config.segmentation_provider
        self._enable_icon_subject_extraction = config.enable_icon_subject_extraction
        
        extractors = self._extractor_registry.get_all_extractors()
        inpaint_providers = self._inpaint_registry.get_all_providers()
        logger.info(
            f"ImageEditabilityService: {len(extractors)} extractors, "
            f"{len(inpaint_providers)} inpaint providers, "
            f"max_depth={self._max_depth}"
        )
    
    def make_image_editable(
        self,
        image_path: str,
        depth: int = 0,
        parent_id: Optional[str] = None,
        parent_bbox: Optional[BBox] = None,
        root_image_size: Optional[Tuple[int, int]] = None,
        element_type: Optional[str] = None,
        root_image_path: Optional[str] = None
    ) -> EditableImage:
        """
         () 
        
        : 
        
        Args:
            image_path: 
            depth:  () 
            parent_id: ID () 
            parent_bbox: bbox () 
            root_image_size:  () 
            element_type: ,  () 
            root_image_path:  () 
        
        Returns:
            EditableImage
        
        Raises:
            FileNotFoundError: 
            ValueError: 
        """
        image_id = str(uuid.uuid4())[:8]
        logger.info(f"{' ' * depth}[{image_id}] Bắt đầu xử lý")
        
        # Backend logic
        try:
            img = Image.open(image_path)
            width, height = img.size
        except Exception as e:
            logger.error(f"Không thể tải hình ảnh {image_path}: {e}")
            raise
        
        # Backend logic
        if root_image_size is None:
            root_image_size = (width, height)
        if root_image_path is None:
            root_image_path = image_path
        
        # Backend logic
        extraction_result = self._extract_elements(
            image_path=image_path,
            element_type=element_type,
            depth=depth
        )

        # Backend logic
        if extraction_result.has_error and depth == 0:
            raise RuntimeError(f"Phân tích bố cục thất bại: {extraction_result.error}")

        # Backend logic
        extracted_image_size = extraction_result.context.metadata.get('image_size', (width, height))
        
        elements = self._convert_to_editable_elements(
            element_dicts=extraction_result.elements,
            image_id=image_id,
            parent_bbox=parent_bbox,
            image_size=extracted_image_size,
            root_image_size=root_image_size,
            source_image_path=image_path  # Backend logic
        )

        logger.info(f"{' ' * depth}Trích xuất được {len(elements)} phần tử")

        # Backend logic
        if self._enable_icon_subject_extraction and self._segmentation_provider is not None:
            self._enhance_icon_elements_with_subject_extraction(
                elements=elements,
                image_id=image_id,
                depth=depth,
            )
        
        # Backend logic
        clean_background = None
        if self._inpaint_registry and elements:
            clean_background = self._generate_clean_background(
                image_path=image_path,
                elements=elements,
                image_id=image_id,
                depth=depth,
                parent_bbox=parent_bbox,
                root_image_path=root_image_path,
                image_size=(width, height),
                element_type=element_type  # Backend logic
            )
        
        # Backend logic
        # Backend logic
        if depth + 1 < self._max_depth:
            self._process_children(
                elements=elements,
                current_image_path=image_path,
                depth=depth,
                image_id=image_id,
                root_image_size=root_image_size,
                current_image_size=(width, height),
                root_image_path=root_image_path
            )
        
        # Backend logic
        editable_image = EditableImage(
            image_id=image_id,
            image_path=image_path,
            width=width,
            height=height,
            elements=elements,
            clean_background=clean_background,
            depth=depth,
            parent_id=parent_id
        )
        
        logger.info(f"{' ' * depth}[{image_id}] Xử lý hoàn tất")
        return editable_image
    
    def _extract_elements(
        self,
        image_path: str,
        element_type: Optional[str],
        depth: int
    ) -> ExtractionResult:
        """ Backend docstring """
        logger.info(f"{' ' * depth}Trích xuất phần tử...")
        
        # Backend logic
        extractor = self._select_extractor(element_type)
        
        # Backend logic
        return extractor.extract(
            image_path=image_path,
            element_type=element_type,
            depth=depth
        )
    
    def _select_extractor(self, element_type: Optional[str]) -> ElementExtractor:
        """ Backend docstring """
        extractor = self._extractor_registry.get_extractor(element_type)
        if extractor is None:
            raise ValueError(f"Không tìm thấy loại phần tử '{element_type}' bộ trích xuất tương ứng")
        return extractor
    
    def _convert_to_editable_elements(
        self,
        element_dicts: List[dict],
        image_id: str,
        parent_bbox: Optional[BBox],
        image_size: Tuple[int, int],
        root_image_size: Tuple[int, int],
        source_image_path: Optional[str] = None
    ) -> List[EditableElement]:
        """
        EditableElement
        
         bbox ,  MinerU . 
         ()  image_path, . 
        """
        elements = []

        # Backend logic
        output_dir = None
        source_img = None
        source_bgr = None
        if source_image_path:
            output_dir = self._upload_folder / 'editable_images' / image_id / 'elements'
            output_dir.mkdir(parents=True, exist_ok=True)
            try:
                source_img = Image.open(source_image_path)
                # Backend logic
                source_bgr = cv2.cvtColor(
                    np.asarray(source_img.convert('RGB')), cv2.COLOR_RGB2BGR
                )
            except Exception as e:
                logger.warning(f"Không thể tải ảnh gốc để cắt: {e}")

        for idx, elem_dict in enumerate(element_dicts):
            bbox_list = elem_dict['bbox']
            local_bbox = BBox(
                x0=bbox_list[0],
                y0=bbox_list[1],
                x1=bbox_list[2],
                y1=bbox_list[3]
            )
            elem_type = elem_dict['type']

            # Backend logic
            # Backend logic
            is_icon: Optional[bool] = None
            if source_bgr is not None and elem_type in ('image', 'figure'):
                is_icon = should_extract_subject(source_bgr, local_bbox)
                if is_icon is True and source_img is not None:
                    pad = max(4, math.ceil(0.02 * min(local_bbox.width, local_bbox.height)))
                    local_bbox = local_bbox.expand(pad, source_img.width, source_img.height)

            # Backend logic
            if parent_bbox is None:
                global_bbox = local_bbox
            else:
                global_bbox = CoordinateMapper.local_to_global(
                    local_bbox=local_bbox,
                    parent_bbox=parent_bbox,
                    local_image_size=image_size,
                    parent_image_size=root_image_size
                )
            
            # Backend logic
            element_image_path = None
            if source_img and output_dir:
                try:
                    # Backend logic
                    crop_box = (
                        max(0, int(local_bbox.x0)),
                        max(0, int(local_bbox.y0)),
                        min(source_img.width, int(local_bbox.x1)),
                        min(source_img.height, int(local_bbox.y1))
                    )
                    
                    # Backend logic
                    if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                        cropped = source_img.crop(crop_box)
                        element_image_path = str(output_dir / f"{idx}_{elem_type}.png")
                        cropped.save(element_image_path)
                except Exception as e:
                    logger.warning(f"Cắt phần tử {idx} thất bại: {e}")
            
            element = EditableElement(
                element_id=f"{image_id}_{idx}",
                element_type=elem_type,
                bbox=local_bbox,
                bbox_global=global_bbox,
                content=elem_dict.get('content'),
                image_path=element_image_path,  # Backend logic
                is_icon=is_icon,
                metadata=elem_dict.get('metadata', {})
            )
            
            elements.append(element)
        
        # Backend logic
        if source_img:
            source_img.close()
        
        return elements
    
    def _enhance_icon_elements_with_subject_extraction(
        self,
        elements: List[EditableElement],
        image_id: str,
        depth: int,
    ) -> None:
        """
         image/figure ,  image_path  PNG. 

         _convert_to_editable_elements  (elem.is_icon) , , 
         (,  None)  crop, . 
        """
        icons = [
            elem for elem in elements
            if elem.image_path
            and elem.element_type in ('image', 'figure')
            and elem.is_icon is True
        ]
        if not icons:
            return

        output_dir = self._upload_folder / 'editable_images' / image_id / 'icon_cutouts'
        output_dir.mkdir(parents=True, exist_ok=True)

        success = 0
        for elem in icons:
            try:
                with Image.open(elem.image_path) as src:
                    cutout = self._segmentation_provider.extract_subject(src)
            except Exception as e:
                logger.warning(f"{' ' * depth} ✗ biểu tượng {elem.element_id} Lỗi tách nền chủ thể: {e}")
                continue
            if cutout is None:
                continue
            cutout_path = output_dir / f"{elem.element_id}.png"
            cutout.save(str(cutout_path))
            elem.image_path = str(cutout_path)
            elem.metadata['subject_extracted'] = True
            success += 1

        logger.info(f"{' ' * depth}🎨 Tách nền chủ thể: {success}/{len(icons)} thành công")

    def _generate_clean_background(
        self,
        image_path: str,
        elements: List[EditableElement],
        image_id: str,
        depth: int,
        parent_bbox: Optional[BBox],
        root_image_path: str,
        image_size: Tuple[int, int],
        element_type: Optional[str] = None
    ) -> Optional[str]:
        """
        clean background
        
        : 
        - element_type, 
        - 
        """
        logger.info(f"{' ' * depth}Tạoclean background (element_type={element_type})...")
        
        # Backend logic
        inpaint_provider = self._inpaint_registry.get_provider(element_type)
        if inpaint_provider is None:
            logger.warning(f"{' ' * depth}Không tìm thấy phương thức vẽ lại, bỏ qua")
            return None
        
        try:
            bboxes = collect_bboxes_from_elements(elements)
            img = Image.open(image_path)
            img_width, img_height = img.size
            element_types = [elem.element_type for elem in elements]
            
            # Backend logic
            if depth == 0:
                crop_box = (0, 0, img_width, img_height)
            elif parent_bbox:
                crop_box = (
                    int(parent_bbox.x0),
                    int(parent_bbox.y0),
                    int(parent_bbox.x1),
                    int(parent_bbox.y1)
                )
            else:
                crop_box = None
            
            # Backend logic
            full_page_img = None
            if root_image_path != image_path:
                full_page_img = Image.open(root_image_path)
            
            # Backend logic
            filtered_bboxes = []
            filtered_types = []
            for bbox, elem_type in zip(bboxes, element_types):
                if isinstance(bbox, (tuple, list)) and len(bbox) == 4:
                    x0, y0, x1, y1 = bbox
                    coverage = ((x1 - x0) * (y1 - y0)) / (img_width * img_height)
                    if coverage > 0.95:
                        continue
                filtered_bboxes.append(bbox)
                filtered_types.append(elem_type)
            
            if not filtered_bboxes:
                return None
            
            # Backend logic
            output_dir = self._upload_folder / 'editable_images' / image_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Backend logic
            logger.info(f"{' ' * depth}Sử dụng {inpaint_provider.__class__.__name__} để vẽ lại")
            result_img = inpaint_provider.inpaint_regions(
                image=img,
                bboxes=filtered_bboxes,
                types=filtered_types,
                expand_pixels=10,
                save_mask_path=str(output_dir / 'mask.png'),
                full_page_image=full_page_img,
                crop_box=crop_box
            )
            
            if result_img is None:
                return None
            
            # Backend logic
            output_path = output_dir / 'clean_background.png'
            result_img.save(str(output_path))
            return str(output_path)
        
        except Exception as e:
            logger.error(f"Tạoclean backgroundthất bại: {e}", exc_info=True)
            return None
    
    def _process_children(
        self,
        elements: List[EditableElement],
        current_image_path: str,
        depth: int,
        image_id: str,
        root_image_size: Tuple[int, int],
        current_image_size: Tuple[int, int],
        root_image_path: str
    ):
        """ Backend docstring """
        logger.info(f"{' ' * depth}Xử lý đệ quy các phần tử con...")
        
        # Backend logic
        elements_to_process = []
        for element in elements:
            if should_recurse_into_element(
                element=element,
                parent_image_size=current_image_size,
                min_image_size=self._min_image_size,
                min_image_area=self._min_image_area,
                max_child_coverage_ratio=self._max_child_coverage_ratio
            ):
                elements_to_process.append(element)
        
        if not elements_to_process:
            return
        
        # Backend logic
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_single_element(element):
            """ Backend docstring """
            try:
                # Backend logic
                child_image_path = crop_element_from_image(
                    source_image_path=current_image_path,
                    bbox=element.bbox
                )
                
                child_editable = self.make_image_editable(
                    image_path=child_image_path,
                    depth=depth + 1,
                    parent_id=image_id,
                    parent_bbox=element.bbox_global,
                    root_image_size=root_image_size,
                    element_type=element.element_type,
                    root_image_path=root_image_path
                )
                
                return element, child_editable, None
            
            except Exception as e:
                return element, None, e
        
        logger.info(f"{' ' * depth} Xử lý song song {len(elements_to_process)} phần tử con...")
        
        # Backend logic
        max_workers = min(8, len(elements_to_process))  # Backend logic
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_element, elem): elem for elem in elements_to_process}
            
            for future in as_completed(futures):
                element, child_editable, error = future.result()
                
                if error:
                    logger.error(f"{' ' * depth} ✗ {element.element_id} thất bại: {error}")
                else:
                    element.children = child_editable.elements
                    element.inpainted_background_path = child_editable.clean_background
                    logger.info(f"{' ' * depth} ✓ {element.element_id} Hoàn tất: {len(child_editable.elements)} phần tử con")