"""
 Provider
AI, 

API: https://ai.baidu.com/ai-doc/IMAGEPROCESS/Mk4i6o3w3
"""
import logging
import base64
import requests
import json
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import io
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaiduInpaintingProvider:
    """
     Provider
    
    , , . 
    
    : 
    - 
    - 
    - , 
    """

    def __init__(self, api_key: str):
        """
         Provider

        Args:
            api_key: API Key (BCEv3: bce-v3/ALTAK-...) Access Token
        """
        self.api_key = api_key
        self.api_url = "https://aip.baidubce.com/rest/2.0/image-process/v1/inpainting"

        if api_key.startswith('bce-v3/'):
            logger.info("✅ Khởi tạo phục hồi ảnh Baidu Provider (Sử dụngBCEv3 API Key)")
        else:
            logger.info("✅ Khởi tạo phục hồi ảnh Baidu Provider (Sử dụngAccess Token)")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=1, max=5),
        retry=retry_if_exception_type((requests.exceptions.RequestException, Exception)),
        reraise=True
    )
    def inpaint(
        self,
        image: Image.Image,
        rectangles: List[Dict[str, int]]
    ) -> Optional[Image.Image]:
        """
        
        
        Args:
            image: PIL Image
            rectangles: , :
                - left: x
                - top: y
                - width: 
                - height: 
        
        Returns:
            PIL Image, None
        """
        if not rectangles:
            logger.warning("Không cung cấp vùng hình chữ nhật, trả về ảnh gốc")
            return image.copy()
        
        logger.info(f"🔧 Bắt đầu phục hồi ảnh Baidu, Tổng {len(rectangles)} vùng")
        
        try:
            # Backend logic
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            original_width, original_height = image.size
            logger.info(f"📏 Kích thước ảnh: {original_width}x{original_height}")
            
            # Backend logic
            max_size = 5000
            scale = 1.0
            if original_width > max_size or original_height > max_size:
                scale = min(max_size / original_width, max_size / original_height)
                new_size = (int(original_width * scale), int(original_height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"✂️ Nén ảnh: {image.size}")
                
                # Backend logic
                rectangles = [
                    {
                        'left': int(r['left'] * scale),
                        'top': int(r['top'] * scale),
                        'width': int(r['width'] * scale),
                        'height': int(r['height'] * scale)
                    }
                    for r in rectangles
                ]
            
            # Backend logic
            valid_rectangles = [
                r for r in rectangles 
                if r['width'] > 0 and r['height'] > 0
            ]
            
            if not valid_rectangles:
                logger.warning("Không có vùng hình chữ nhật hợp lệ sau khi lọc, trả về ảnh gốc")
                return image.copy()
            
            # Backend logic
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=95)
            image_bytes = buffer.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            logger.info(f"📦 Hoàn tất mã hóa ảnh: {len(image_base64)} bytes, {len(valid_rectangles)} vùng hình chữ nhật")
            
            # Backend logic
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            
            # Backend logic
            if self.api_key.startswith('bce-v3/'):
                headers['Authorization'] = f'Bearer {self.api_key}'
                url = self.api_url
                logger.info("🔐 Sử dụngBCEv3xác thực chữ ký")
            else:
                url = f"{self.api_url}?access_token={self.api_key}"
                logger.info("🔐 Sử dụngAccess Tokenxác thực")
            
            # Backend logic
            request_body = {
                'image': image_base64,
                'rectangle': valid_rectangles
            }
            
            logger.info("🌐 Gửi yêu cầu tới API phục hồi ảnh BaiduAPI...")
            response = requests.post(
                url, 
                headers=headers, 
                json=request_body, 
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Backend logic
            if 'error_code' in result:
                error_msg = result.get('error_msg', 'Unknown error')
                error_code = result.get('error_code')
                logger.error(f"❌ BaiduAPILỗi: [{error_code}] {error_msg}")
                raise Exception(f"Baidu API error [{error_code}]: {error_msg}")
            
            # Backend logic
            result_image_base64 = result.get('image')
            if not result_image_base64:
                logger.error("❌ BaiduAPIKhông có hình ảnh trong kết quả trả về")
                return None
            
            # Backend logic
            result_image_bytes = base64.b64decode(result_image_base64)
            result_image = Image.open(io.BytesIO(result_image_bytes))
            
            # Backend logic
            if scale < 1.0:
                result_image = result_image.resize(
                    (original_width, original_height), 
                    Image.Resampling.LANCZOS
                )
                logger.info(f"📐 Khôi phục kích thước ảnh: {result_image.size}")
            
            logger.info(f"✅ Hoàn tất phục hồi ảnh Baidu!")
            return result_image
            
        except Exception as e:
            logger.error(f"❌ Phục hồi ảnh Baidu thất bại: {str(e)}")
            raise
    
    def inpaint_bboxes(
        self,
        image: Image.Image,
        bboxes: List[Tuple[float, float, float, float]],
        expand_pixels: int = 2
    ) -> Optional[Image.Image]:
        """
        bbox
        
        Args:
            image: PIL Image
            bboxes: bbox, bbox (x0, y0, x1, y1)
            expand_pixels: , 2
        
        Returns:
            PIL Image
        """
        # Backend logic
        rectangles = []
        for bbox in bboxes:
            x0, y0, x1, y1 = bbox
            # Backend logic
            x0 = max(1, x0 - expand_pixels)
            y0 = max(1, y0 - expand_pixels)
            x1 = min(image.width - 1, x1 + expand_pixels)
            y1 = min(image.height - 1, y1 + expand_pixels)
            
            rectangles.append({
                'left': int(x0),
                'top': int(y0),
                'width': int(x1 - x0),
                'height': int(y1 - y0)
            })
        
        return self.inpaint(image, rectangles)


def create_baidu_inpainting_provider(
    api_key: Optional[str] = None
) -> Optional[BaiduInpaintingProvider]:
    """
     Provider 

    Args:
        api_key: API Key, Flask config

    Returns:
        BaiduInpaintingProvider, api_keyNone
    """
    import os
    from config import Config

    if not api_key:
        # Backend logic
        try:
            from flask import current_app
            api_key = current_app.config.get('BAIDU_API_KEY')
        except RuntimeError:
            pass  # Backend logic
        if not api_key:
            api_key = Config.BAIDU_API_KEY
        if not api_key:
            api_key = os.getenv('BAIDU_API_KEY')

    if not api_key:
        logger.warning("⚠️ Chưa cấu hình BaiduAPI Key (BAIDU_API_KEY), bỏ qua phục hồi ảnh Baidu")
        return None

    return BaiduInpaintingProvider(api_key)