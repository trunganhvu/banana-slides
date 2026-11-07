"""
Gemini Inpainting 
 Gemini 2.5 Flash Image Preview  mask 
"""
import logging
from typing import Optional
from PIL import Image, ImageDraw
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from .genai_provider import GenAIImageProvider
from config import get_config

logger = logging.getLogger(__name__)


class GeminiInpaintingProvider:
    """ Backend docstring """
    
    # DEFAULT_MODEL = "gemini-2.5-flash-image"
    DEFAULT_MODEL = "gemini-3-pro-image-preview"
    DEFAULT_PROMPT = """\
, . 
: 
1. 
2. , , . 

, , , , . , , . 

. 

"""
    
    def __init__(
        self, 
        api_key: str, 
        api_base: str = None,
        model: str = None,
        timeout: int = 60
    ):
        """
         Gemini Inpainting 
        
        Args:
            api_key: Google API key
            api_base: API base URL (for proxies like aihubmix)
            model: Model name to use (default: gemini-2.5-flash-image)
            timeout: API  () 
        """
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        
        # Backend logic
        self.genai_provider = GenAIImageProvider(
            api_key=api_key,
            api_base=api_base,
            model=self.model
        )
        
        logger.info(f"✅ Gemini Inpainting Provider Khởi tạo (model={self.model})")
    
    @staticmethod
    def create_marked_image(original_image: Image.Image, mask_image: Image.Image) -> Image.Image:
        """
        
        
        Args:
            original_image: 
            mask_image:  (=) 
            
        Returns:
             ( + ) 
        """
        # Backend logic
        if mask_image.size != original_image.size:
            mask_image = mask_image.resize(original_image.size, Image.LANCZOS)
        
        # Backend logic
        if original_image.mode != 'RGB':
            original_image = original_image.convert('RGB')
        if mask_image.mode != 'RGB':
            mask_image = mask_image.convert('RGB')
        
        # Backend logic
        marked_image = original_image.copy()
        
        # Backend logic
        mask_array = np.array(mask_image)
        marked_array = np.array(marked_image)
        
        # Backend logic
        # Backend logic
        white_threshold = 200
        mask_regions = np.all(mask_array > white_threshold, axis=2)
        
        # Backend logic
        black_overlay = np.array([0, 0, 0], dtype=np.uint8)
        marked_array[mask_regions] = black_overlay
        
        # Backend logic
        marked_image = Image.fromarray(marked_array)
        
        logger.debug(f"✅ Đã tạo ảnh đánh dấu, đã phủ màu đen đặc lên {np.sum(mask_regions)} điểm ảnh")
        
        return marked_image
    
    @retry(
        stop=stop_after_attempt(3),  # Backend logic
        wait=wait_exponential(multiplier=1, min=2, max=10),  # Backend logic
        reraise=True
    )
    def inpaint_image(
        self,
        original_image: Image.Image,
        mask_image: Image.Image,
        inpaint_mode: str = "remove",
        custom_prompt: Optional[str] = None,
        full_page_image: Optional[Image.Image] = None,
        crop_box: Optional[tuple] = None
    ) -> Optional[Image.Image]:
        """
         Gemini 
        
        Args:
            original_image: 
            mask_image:  (=, =) 
            inpaint_mode:  (, ) 
            custom_prompt:  prompt ( None ) 
            full_page_image:  PPT  (16:9) , 
            crop_box:  (x0, y0, x1, y1), 
            
        Returns:
            ,  None
        """
        try:
            logger.info("🚀 Bắt đầu gọi Gemini inpainting (Chế độ đánh dấu) ")
            
            working_image = full_page_image
            
            # Backend logic
            result_crop_box = crop_box  # Backend logic
            
            # Backend logic
            final_image = working_image
            
            # Backend logic
            # Backend logic
            full_mask = Image.new('RGB', final_image.size, (0, 0, 0))
            # Backend logic
            x0, y0, x1, y1 = crop_box
            # Backend logic
            mask_resized = mask_image.resize((x1 - x0, y1 - y0), Image.LANCZOS)
            full_mask.paste(mask_resized, (x0, y0))
            final_mask = full_mask
            logger.info(f"📷 Chế độ toàn trang: Trang={final_image.size}, maskmở rộng tới={final_mask.size}, vị trí dán={crop_box}")

            # Backend logic
            logger.info("🎨 Tạo ảnh đánh dấu (khung màu đen đặc đánh dấu vùng cần xóa) ...")
            marked_image = self.create_marked_image(final_image, final_mask)
            logger.info(f"✅ Hoàn tất tạo ảnh đánh dấu: {marked_image.size}")
            
            # Backend logic
            prompt = custom_prompt or self.DEFAULT_PROMPT
            logger.info(f"📝 Prompt: {prompt[:100]}...")
            
            # Backend logic
            logger.info("🌐 gọi GenAI Provider thực hiện inpainting (chỉ truyền ảnh đánh dấu) ...")
            
            result_image = self.genai_provider.generate_image(
                prompt=prompt,
                ref_images=[full_page_image, marked_image],  
                aspect_ratio="16:9",
                resolution="1K"
            )
            
            if result_image is None:
                logger.error("❌ Gemini Inpainting thất bại: không trả về hình ảnh")
                return None
            
            # Backend logic
            # Backend logic
            if hasattr(result_image, '_pil_image'):
                logger.debug("🔄 chuyển đổi GenAI Image là PIL Image")
                result_image = result_image._pil_image
            
            logger.info(f"✅ Gemini Inpainting thành công! APIkích thước trả về: {result_image.size}, {result_image.mode}")
            
            # Backend logic
            if result_image.size != final_image.size:
                logger.info(f"🔄 Resize từ {result_image.size} đến {final_image.size}")
                result_image = result_image.resize(final_image.size, Image.LANCZOS)
            
            # Backend logic
            logger.info("🎨 Ghép ảnh: sẽ inpaintKết quả và ảnh gốc theomaskgộp...")
            
            # Backend logic
            if result_image.mode != 'RGB':
                result_image = result_image.convert('RGB')
            if final_image.mode != 'RGB':
                final_image = final_image.convert('RGB')
            
            # Backend logic
            mask_for_composite = final_mask.convert('L')
            
            # Backend logic
            # Backend logic
            composited_image = Image.composite(result_image, final_image, mask_for_composite)
            logger.info(f"✅ Hoàn tất ghép ảnh! kích thước: {composited_image.size}")
            
            # Backend logic
            cropped_result = composited_image.crop(result_crop_box)
            logger.info(f"✂️ Cắt từ trang đầy đủ: {composited_image.size} -> {cropped_result.size}")
            return cropped_result
            
        except Exception as e:
            logger.error(f"❌ Gemini Inpainting thất bại: {e}", exc_info=True)
            raise