"""
Inpaint - inpaint

: 
1. DefaultInpaintProvider - mask (Volcengine Inpainting) 
2. GenerativeEditInpaintProvider -  (Gemini) 
3. BaiduInpaintProvider - API
4. HybridInpaintProvider - : , 

: 
- InpaintProviderRegistry - 
"""
import logging
import tempfile
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from PIL import Image

from utils.mask_utils import create_mask_from_bboxes

logger = logging.getLogger(__name__)


class InpaintProvider(ABC):
    """
    Inpaint
    
    inpaint, : 
    - InpaintingService () 
    - Gemini API
    - SD/SDXL
    - API
    """
    
    @abstractmethod
    def inpaint_regions(
        self,
        image: Image.Image,
        bboxes: List[tuple],
        types: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Image.Image]:
        """
        inpaint
        
        Args:
            image: PIL
            bboxes: , bbox (x0, y0, x1, y1)
            types: Danh sách loại phần tử tùy chọn, và bboxestương ứng một-một ( như 'text', 'image', 'table' v.v.) 
            **kwargs: 
        
        Returns:
            PIL, None
        """
        pass


class DefaultInpaintProvider(InpaintProvider):
    """
    InpaintingServiceInpaint
    
    , InpaintingService
    """
    
    def __init__(self, inpainting_service):
        """
        Inpaint
        
        Args:
            inpainting_service: InpaintingService
        """
        self.inpainting_service = inpainting_service
    
    def inpaint_regions(
        self,
        image: Image.Image,
        bboxes: List[tuple],
        types: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Image.Image]:
        """
        InpaintingServiceinpaint
        
        kwargs: 
        - expand_pixels: int, , 10
        - merge_bboxes: bool, bbox, False
        - merge_threshold: int, , 20
        - save_mask_path: str, mask, 
        - full_page_image: Image.Image,  (Gemini) , 
        - crop_box: tuple,  (x0, y0, x1, y1), 
        """
        expand_pixels = kwargs.get('expand_pixels', 10)
        merge_bboxes = kwargs.get('merge_bboxes', False)
        merge_threshold = kwargs.get('merge_threshold', 20)
        save_mask_path = kwargs.get('save_mask_path')
        full_page_image = kwargs.get('full_page_image')
        crop_box = kwargs.get('crop_box')
        
        try:
            result_img = self.inpainting_service.remove_regions_by_bboxes(
                image=image,
                bboxes=bboxes,
                expand_pixels=expand_pixels,
                merge_bboxes=merge_bboxes,
                merge_threshold=merge_threshold,
                save_mask_path=save_mask_path,
                full_page_image=full_page_image,
                crop_box=crop_box
            )
            return result_img
        except Exception as e:
            logger.error(f"DefaultInpaintProviderXử lý thất bại: {e}", exc_info=True)
            return None


class GenerativeEditInpaintProvider(InpaintProvider):
    """
    Inpaint
    
     (Gemini) , . 
    
    DefaultInpaintProvider: 
    - DefaultInpaintProvider: mask (bbox) 
    - GenerativeEditInpaintProvider:  (prompt) 
    
    :  mask,  bbox 
    : , , token
    
    : 
    - bbox
    - 
    - mask-based
    """
    
    def __init__(self, ai_service, aspect_ratio: str = "16:9", resolution: str = "2K"):
        """
        Inpaint
        
        Args:
            ai_service: AIService (edit_image) 
            aspect_ratio: 
            resolution: 
        """
        self.ai_service = ai_service
        self.aspect_ratio = aspect_ratio
        self.resolution = resolution

    @staticmethod
    def _build_normalized_removal_regions(
        image_size: tuple[int, int],
        bboxes: List[tuple],
        types: Optional[List[str]] = None,
    ) -> List[Dict]:
        """ Backend docstring """
        image_width, image_height = image_size
        if image_width <= 0 or image_height <= 0:
            return []

        def clamp_01(value: float) -> float:
            return max(0.0, min(1.0, value))

        removal_regions = []
        for index, bbox in enumerate(bboxes):
            if not isinstance(bbox, (tuple, list)) or len(bbox) != 4:
                continue

            raw_x0, raw_y0, raw_x1, raw_y1 = [float(v) for v in bbox]
            x0, x1 = sorted((raw_x0, raw_x1))
            y0, y1 = sorted((raw_y0, raw_y1))

            nx0 = round(clamp_01(x0 / image_width), 6)
            ny0 = round(clamp_01(y0 / image_height), 6)
            nx1 = round(clamp_01(x1 / image_width), 6)
            ny1 = round(clamp_01(y1 / image_height), 6)

            removal_regions.append({
                'region_id': index + 1,
                'element_type': types[index] if types and index < len(types) else 'unknown',
                'bbox': {
                    'x0': nx0,
                    'y0': ny0,
                    'x1': nx1,
                    'y1': ny1,
                    'width': round(nx1 - nx0, 6),
                    'height': round(ny1 - ny0, 6),
                }
            })

        return removal_regions
    
    def inpaint_regions(
        self,
        image: Image.Image,
        bboxes: List[tuple],
        types: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Image.Image]:
        """
        
        
        :  bbox  mask,  bbox  0-1  JSON  prompt, 
        
        kwargs: 
        - aspect_ratio: str, , 
        - resolution: str, , 
        """
        aspect_ratio = kwargs.get('aspect_ratio', self.aspect_ratio)
        resolution = kwargs.get('resolution', self.resolution)
        
        try:
            from services.prompts import get_clean_background_prompt

            normalized_regions = self._build_normalized_removal_regions(
                image.size,
                bboxes,
                types,
            )

            # Backend logic
            edit_instruction = get_clean_background_prompt(normalized_regions)
            
            # Backend logic
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                image.save(tmp_path)
            
            logger.info("GenerativeEditInpaintProvider: Bắt đầu vẽ lại bằng chỉnh sửa tạo sinh...")
            
            # Backend logic
            clean_bg_image = self.ai_service.edit_image(
                prompt=edit_instruction,
                current_image_path=tmp_path,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                original_description=None,
                additional_ref_images=None
            )
            
            if not clean_bg_image:
                logger.error("GenerativeEditInpaintProvider: Chỉnh sửa tạo sinh trả về kết quả rỗng")
                return None
            
            # Backend logic
            if not isinstance(clean_bg_image, Image.Image):
                # Backend logic
                if hasattr(clean_bg_image, '_pil_image'):
                    clean_bg_image = clean_bg_image._pil_image
                else:
                    logger.error(f"GenerativeEditInpaintProvider: Loại hình ảnh không xác định: {type(clean_bg_image)}")
                    return None
            
            logger.info("GenerativeEditInpaintProvider: Hoàn tất vẽ lại")
            return clean_bg_image
        
        except Exception as e:
            logger.error(f"GenerativeEditInpaintProviderXử lý thất bại: {e}", exc_info=True)
            return None


class BaiduInpaintProvider(InpaintProvider):
    """
    APIInpaint
    
    AI. 
    
    : 
    - bbox
    - , 
    - , 
    
    : , 
    """
    
    def __init__(self, baidu_inpainting_provider):
        """
        
        
        Args:
            baidu_inpainting_provider: BaiduInpaintingProvider (ai_providers.image) 
        """
        self._provider = baidu_inpainting_provider
    
    def inpaint_regions(
        self,
        image: Image.Image,
        bboxes: List[tuple],
        types: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Image.Image]:
        """
        API
        
        kwargs: 
        - expand_pixels: int, , 2
        """
        expand_pixels = kwargs.get('expand_pixels', 2)
        
        try:
            logger.info(f"BaiduInpaintProvider: Bắt đầu phục hồi {len(bboxes)} vùng...")
            
            result_image = self._provider.inpaint_bboxes(
                image=image,
                bboxes=bboxes,
                expand_pixels=expand_pixels
            )
            
            if result_image:
                logger.info("BaiduInpaintProvider: Hoàn tất phục hồi")
            else:
                logger.warning("BaiduInpaintProvider: Phục hồi trả về kết quả rỗng")
                return None
            
            # Backend logic
            mask = create_mask_from_bboxes(image.size, bboxes, expand_pixels=0)
            return Image.composite(result_image, image, mask.convert('L'))
        
        except Exception as e:
            logger.error(f"BaiduInpaintProviderXử lý thất bại: {e}", exc_info=True)
            return None


class HybridInpaintProvider(InpaintProvider):
    """
    Inpaint -  + 
    
    : 
    1. API (, ) 
    2.  (Gemini) , 
    
    : 
    - , 
    - , 
    
    : 
    - 
    - 
    """
    
    def __init__(
        self,
        baidu_provider: BaiduInpaintProvider,
        generative_provider: 'GenerativeEditInpaintProvider',
        enhance_quality: bool = True
    ):
        """
        Inpaint
        
        Args:
            baidu_provider: 
            generative_provider:  () 
            enhance_quality: , True
        """
        self._baidu_provider = baidu_provider
        self._generative_provider = generative_provider
        self._enhance_quality = enhance_quality
    
    def inpaint_regions(
        self,
        image: Image.Image,
        bboxes: List[tuple],
        types: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Image.Image]:
        """
        : , 
        
        kwargs: 
        - expand_pixels: int, , 2
        - enhance_quality: bool, , 
        - aspect_ratio: str, 
        - resolution: str, 
        """
        expand_pixels = kwargs.get('expand_pixels', 2)
        enhance_quality = kwargs.get('enhance_quality', self._enhance_quality)
        
        try:
            # Backend logic
            logger.info(f"HybridInpaintProvider Step 1: Baidu phục hồi {len(bboxes)} vùng...")
            
            repaired_image = self._baidu_provider.inpaint_regions(
                image=image,
                bboxes=bboxes,
                types=types,
                expand_pixels=expand_pixels
            )
            
            if repaired_image is None:
                logger.error("HybridInpaintProvider: Phục hồi Baidu thất bại")
                return None
            
            logger.info("HybridInpaintProvider: Hoàn tất phục hồi Baidu")
            
            # Backend logic
            if enhance_quality and self._generative_provider:
                logger.info("HybridInpaintProvider Step 2: Nâng cấp chất lượng ảnh tạo sinh...")
                
                # Backend logic
                enhanced_image = self._enhance_image_quality(
                    repaired_image,
                    inpainted_bboxes=bboxes,  # Backend logic
                    aspect_ratio=kwargs.get('aspect_ratio'),
                    resolution=kwargs.get('resolution')
                )
                
                if enhanced_image:
                    logger.info("HybridInpaintProvider: Hoàn tất nâng cấp chất lượng ảnh")
                    return enhanced_image
                else:
                    logger.warning("HybridInpaintProvider: Nâng cấp chất lượng ảnh thất bại, trả về kết quả phục hồi Baidu")
                    return repaired_image
            else:
                logger.info("HybridInpaintProvider: Bỏ qua nâng cấp chất lượng ảnh")
                return repaired_image
        
        except Exception as e:
            logger.error(f"HybridInpaintProviderXử lý thất bại: {e}", exc_info=True)
            return None
    
    def _enhance_image_quality(
        self,
        image: Image.Image,
        inpainted_bboxes: Optional[List[tuple]] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> Optional[Image.Image]:
        """
        
        
        Args:
            image: 
            inpainted_bboxes: bbox,  [(x0, y0, x1, y1), ...]
            aspect_ratio:  () 
            resolution:  () 
        
        Returns:
            
        """
        try:
            # Backend logic
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                image.save(tmp_path)
            
            # Backend logic
            regions = None
            if inpainted_bboxes:
                # Backend logic
                from utils.mask_utils import merge_vertical_nearby_bboxes
                original_count = len(inpainted_bboxes)
                merged_bboxes = merge_vertical_nearby_bboxes(inpainted_bboxes)
                if len(merged_bboxes) < original_count:
                    logger.info(f"Sau khi gộp các dòng văn bản liền kề: {original_count} -> {len(merged_bboxes)} vùng")
                
                img_width, img_height = image.size
                regions = []
                for bbox in merged_bboxes:
                    x0, y0, x1, y1 = bbox
                    # Backend logic
                    regions.append({
                        'left': round(x0 / img_width * 100, 1),
                        'top': round(y0 / img_height * 100, 1),
                        'right': round(x1 / img_width * 100, 1),
                        'bottom': round(y1 / img_height * 100, 1),
                        'width_percent': round((x1 - x0) / img_width * 100, 1),
                        'height_percent': round((y1 - y0) / img_height * 100, 1)
                    })
                logger.info(f"truyền {len(regions)} vùng đã phục hồi cho mô hình tạo sinh (tọa độ phần trăm) ")
            
            # Backend logic
            from services.prompts import get_quality_enhancement_prompt
            enhance_prompt = get_quality_enhancement_prompt(inpainted_regions=regions)
            
            # Backend logic
            ar = aspect_ratio or self._generative_provider.aspect_ratio
            res = resolution or self._generative_provider.resolution
            
            # Backend logic
            enhanced_image = self._generative_provider.ai_service.edit_image(
                prompt=enhance_prompt,
                current_image_path=tmp_path,
                aspect_ratio=ar,
                resolution=res,
                original_description=None,
                additional_ref_images=None
            )
            
            if not enhanced_image:
                return None
            
            # Backend logic
            if not isinstance(enhanced_image, Image.Image):
                if hasattr(enhanced_image, '_pil_image'):
                    enhanced_image = enhanced_image._pil_image
                else:
                    logger.error(f"Loại hình ảnh không xác định: {type(enhanced_image)}")
                    return None
            
            return enhanced_image
        
        except Exception as e:
            logger.error(f"Nâng cấp chất lượng ảnh thất bại: {e}", exc_info=True)
            return None


class InpaintProviderRegistry:
    """
    
    
    : 
    -  → DefaultInpaintProvider (mask-based) 
    -  → DefaultInpaintProvider () 
    - / → GenerativeEditInpaintProvider () 
    -  → 
    
    : 
        >>> registry = InpaintProviderRegistry()
        >>> registry.register('text', mask_provider)
        >>> registry.register('image', generative_provider)
        >>> registry.register_default(mask_provider)
        >>> 
        >>> provider = registry.get_provider('text')  # Backend logic
        >>> provider = registry.get_provider('chart')  # Backend logic
    """
    
    # Backend logic
    TEXT_TYPES = {'text', 'title', 'paragraph', 'header', 'footer', 'list'}
    TABLE_TYPES = {'table', 'table_cell'}
    IMAGE_TYPES = {'image', 'figure', 'chart', 'diagram'}
    
    def __init__(self):
        """ Backend docstring """
        self._type_mapping: Dict[str, InpaintProvider] = {}
        self._default_provider: Optional[InpaintProvider] = None
    
    def register(self, element_type: str, provider: InpaintProvider) -> 'InpaintProviderRegistry':
        """
        
        
        Args:
            element_type: Loại phần tử ( như 'text', 'image' v.v.) 
            provider: 
        
        Returns:
            self, 
        """
        self._type_mapping[element_type] = provider
        logger.debug(f"Đăng ký nhà cung cấp vẽ lại: {element_type} -> {provider.__class__.__name__}")
        return self
    
    def register_types(self, element_types: List[str], provider: InpaintProvider) -> 'InpaintProviderRegistry':
        """
        
        
        Args:
            element_types: 
            provider: 
        
        Returns:
            self, 
        """
        for t in element_types:
            self.register(t, provider)
        return self
    
    def register_default(self, provider: InpaintProvider) -> 'InpaintProviderRegistry':
        """
         () 
        
        Args:
            provider: 
        
        Returns:
            self, 
        """
        self._default_provider = provider
        logger.debug(f"Đăng ký nhà cung cấp vẽ lại mặc định: {provider.__class__.__name__}")
        return self
    
    def get_provider(self, element_type: Optional[str]) -> Optional[InpaintProvider]:
        """
        
        
        Args:
            element_type: , None
        
        Returns:
            , 
        """
        if element_type is None:
            return self._default_provider
        
        # Backend logic
        if element_type in self._type_mapping:
            return self._type_mapping[element_type]
        
        # Backend logic
        return self._default_provider
    
    def get_all_providers(self) -> List[InpaintProvider]:
        """
         () 
        
        Returns:
            
        """
        providers = list(set(self._type_mapping.values()))
        if self._default_provider and self._default_provider not in providers:
            providers.append(self._default_provider)
        return providers
    
    @classmethod
    def create_default(
        cls,
        mask_provider: Optional[InpaintProvider] = None,
        generative_provider: Optional[InpaintProvider] = None
    ) -> 'InpaintProviderRegistry':
        """
        
        
        : 
        -  → mask-based () 
        -  → mask-based (, ) 
        - / → generative (, ) 
        -  → mask-based () 
        
        Args:
            mask_provider: mask (DefaultInpaintProvider) 
            generative_provider:  (GenerativeEditInpaintProvider) 
        
        Returns:
            
        """
        registry = cls()
        
        # Backend logic
        if not mask_provider and not generative_provider:
            logger.warning("TạoInpaintProviderRegistrynhưng không cung cấp bất kỳprovider")
            return registry
        
        # Backend logic
        default_provider = mask_provider or generative_provider
        registry.register_default(default_provider)
        
        # Backend logic
        if mask_provider:
            registry.register_types(list(cls.TEXT_TYPES), mask_provider)
            registry.register_types(list(cls.TABLE_TYPES), mask_provider)
        
        # Backend logic
        image_provider = generative_provider or mask_provider
        if image_provider:
            registry.register_types(list(cls.IMAGE_TYPES), image_provider)
        
        logger.info(f"Tạo mặc địnhInpaintProviderRegistry: "
                   f"văn bản/Bảng->{mask_provider.__class__.__name__ if mask_provider else 'None'}, "
                   f"hình ảnh->{image_provider.__class__.__name__ if image_provider else 'None'}")
        
        return registry