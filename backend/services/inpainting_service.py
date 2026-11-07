"""
Inpainting 
 provider 
 provider:
- volcengine:  Inpainting
- gemini: Google Gemini 2.5 Flash Image Preview
"""
import logging
from typing import List, Tuple, Union, Optional
from PIL import Image

from services.ai_providers.image.volcengine_inpainting_provider import VolcengineInpaintingProvider
from services.ai_providers.image.gemini_inpainting_provider import GeminiInpaintingProvider
from utils.mask_utils import (
    create_mask_from_bboxes,
    create_inverse_mask_from_bboxes,
    create_mask_from_image_and_bboxes,
    merge_overlapping_bboxes,
    visualize_mask_overlay
)
from config import get_config

logger = logging.getLogger(__name__)


class InpaintingService:
    """
    Inpainting 
    
    : 
    1.  bbox 
    2.  inpainting provider 
    3. 
    
     provider:
    - volcengine:  Inpainting
    - gemini: Google Gemini 2.5 Flash Image Preview
    """
    
    def __init__(self, provider=None, provider_type: str = "volcengine"):
        """
         Inpainting 
        
        Args:
            provider: Inpainting ,  None 
            provider_type: Provider loại ('volcengine' hoặc 'gemini')
        """
        if provider is None:
            config = get_config()
            
            if provider_type == "gemini":
                # Backend logic
                api_key = config.GOOGLE_API_KEY
                api_base = config.GOOGLE_API_BASE
                timeout = config.GENAI_TIMEOUT
                
                if not api_key:
                    raise ValueError("Google API Key chưa cấu hình")
                
                self.provider = GeminiInpaintingProvider(
                    api_key=api_key,
                    api_base=api_base,
                    timeout=timeout
                )
                self.provider_type = "gemini"
            else:
                # Backend logic
                access_key = config.VOLCENGINE_ACCESS_KEY
                secret_key = config.VOLCENGINE_SECRET_KEY
                timeout = config.VOLCENGINE_INPAINTING_TIMEOUT
                
                if not access_key or not secret_key:
                    raise ValueError("Volcengine Access Key và Secret Key chưa cấu hình")
                
                self.provider = VolcengineInpaintingProvider(
                    access_key=access_key,
                    secret_key=secret_key,
                    timeout=timeout
                )
                self.provider_type = "volcengine"
        else:
            self.provider = provider
            self.provider_type = provider_type
        
        self.config = get_config()
    
    def remove_regions_by_bboxes(
        self,
        image: Image.Image,
        bboxes: List[Union[Tuple[int, int, int, int], dict]],
        expand_pixels: int = 5,
        merge_bboxes: bool = False,
        merge_threshold: int = 10,
        save_mask_path: Optional[str] = None,
        full_page_image: Optional[Image.Image] = None,
        crop_box: Optional[tuple] = None
    ) -> Optional[Image.Image]:
        """
        
        
        Args:
            image:  (PIL Image) 
            bboxes: , : 
                    - (x1, y1, x2, y2) 
                    - {"x1": x1, "y1": y1, "x2": x2, "y2": y2} dictionary
                    - {"x": x, "y": y, "width": w, "height": h} dictionary
            expand_pixels: ,  (5) 
            merge_bboxes:  (False) 
            merge_threshold: ,  (10) 
            save_mask_path: Mask  () 
            full_page_image:  PPT  ( Gemini provider) 
            crop_box:  (x0, y0, x1, y1),  ( Gemini provider) 
            
        Returns:
            ,  None
        """
        try:
            logger.info(f"Bắt đầu xử lý xóa vùng ảnh, Gốc bbox số lượng: {len(bboxes)}")
            
            # Backend logic
            if merge_bboxes and len(bboxes) > 1:
                # Backend logic
                normalized_bboxes = []
                for bbox in bboxes:
                    if isinstance(bbox, dict):
                        if 'x1' in bbox:
                            normalized_bboxes.append((bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']))
                        elif 'x' in bbox:
                            normalized_bboxes.append((bbox['x'], bbox['y'], 
                                                    bbox['x'] + bbox['width'], 
                                                    bbox['y'] + bbox['height']))
                    else:
                        normalized_bboxes.append(tuple(bbox))
                
                bboxes = merge_overlapping_bboxes(normalized_bboxes, merge_threshold)
                logger.info(f"Sau khi gộp bbox số lượng: {len(bboxes)}")
            
            # Backend logic
            mask = create_mask_from_image_and_bboxes(
                image,
                bboxes,
                expand_pixels=expand_pixels
            )
            
            logger.info(f"Đã tạo ảnh mặt nạ, kích thước: {mask.size}")
            
            # Backend logic
            if save_mask_path:
                try:
                    mask.save(save_mask_path)
                    logger.info(f"📷 MaskĐã lưu ảnh: {save_mask_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Lưumaskhình ảnh thất bại: {e}")
            
            # Backend logic
            result = self.provider.inpaint_image(
                original_image=image,
                mask_image=mask,
                full_page_image=full_page_image,
                crop_box=crop_box
            )
            
            if result is not None:
                logger.info(f"Xóa vùng ảnh thành công, kích thước kết quả: {result.size}")
            else:
                logger.error("Xóa vùng ảnh thất bại")
            
            return result
            
        except Exception as e:
            logger.error(f"Xóa vùng thất bại: {str(e)}", exc_info=True)
            return None
    
    def regenerate_background(
        self,
        image: Image.Image,
        foreground_bboxes: List[Union[Tuple[int, int, int, int], dict]],
        expand_pixels: int = 5
    ) -> Optional[Image.Image]:
        """
         (, ) 
        
        :  bbox , 
        
        Args:
            image: 
            foreground_bboxes:  () 
            expand_pixels:  () , 
            
        Returns:
            ,  None
        """
        try:
            logger.info(f"Bắt đầu tạo lại ảnh nền, Số lượng đối tượng tiền cảnh: {len(foreground_bboxes)}")
            
            # Backend logic
            mask = create_inverse_mask_from_bboxes(
                image.size,
                foreground_bboxes,
                expand_pixels=expand_pixels
            )
            
            logger.info(f"Đã tạo mặt nạ đảo ngược, kích thước: {mask.size}")
            
            # Backend logic
            result = self.provider.inpaint_image(
                original_image=image,
                mask_image=mask
            )
            
            if result is not None:
                logger.info(f"Tạo lại nền thành công, kích thước kết quả: {result.size}")
            else:
                logger.error("Tạo lại nền thất bại")
            
            return result
            
        except Exception as e:
            logger.error(f"Tạo lại nền thất bại: {str(e)}", exc_info=True)
            return None
    
    def create_mask_preview(
        self,
        image: Image.Image,
        bboxes: List[Union[Tuple[int, int, int, int], dict]],
        expand_pixels: int = 0,
        alpha: float = 0.5
    ) -> Image.Image:
        """
         () 
        
        Args:
            image: 
            bboxes: 
            expand_pixels: 
            alpha: 
            
        Returns:
            
        """
        mask = create_mask_from_image_and_bboxes(image, bboxes, expand_pixels)
        return visualize_mask_overlay(image, mask, alpha)
    
    @staticmethod
    def create_mask_image(
        image_size: Tuple[int, int],
        bboxes: List[Union[Tuple[int, int, int, int], dict]],
        expand_pixels: int = 0
    ) -> Image.Image:
        """
        :  () 
        
        Args:
            image_size:  (width, height)
            bboxes: 
            expand_pixels: 
            
        Returns:
            
        """
        return create_mask_from_bboxes(image_size, bboxes, expand_pixels)


# Backend logic

_inpainting_service_instances = {}


def get_inpainting_service(provider_type: str = None) -> InpaintingService:
    """
     InpaintingService  (,  provider ) 
    
    Args:
        provider_type: Provider loại ('volcengine', 'gemini'), 
                       None 
    
    Returns:
        InpaintingService 
    """
    # Backend logic
    if provider_type is None:
        config = get_config()
        provider_type = getattr(config, 'INPAINTING_PROVIDER', 'gemini')  # Backend logic
    
    # Backend logic
    if provider_type not in _inpainting_service_instances:
        _inpainting_service_instances[provider_type] = InpaintingService(
            provider_type=provider_type
        )
    
    return _inpainting_service_instances[provider_type]


def remove_regions(
    image: Image.Image,
    bboxes: List[Union[Tuple[int, int, int, int], dict]],
    **kwargs
) -> Optional[Image.Image]:
    """
    : 
    
    Args:
        image: 
        bboxes: 
        **kwargs:  InpaintingService.remove_regions_by_bboxes
        
    Returns:
        
    """
    service = get_inpainting_service()
    return service.remove_regions_by_bboxes(image, bboxes, **kwargs)


def regenerate_background(
    image: Image.Image,
    foreground_bboxes: List[Union[Tuple[int, int, int, int], dict]],
    **kwargs
) -> Optional[Image.Image]:
    """
    : 
    
    Args:
        image: 
        foreground_bboxes: 
        **kwargs:  InpaintingService.regenerate_background
        
    Returns:
        
    """
    service = get_inpainting_service()
    return service.regenerate_background(image, foreground_bboxes, **kwargs)