"""
 Inpainting 
HTTP, SDK
"""
import logging
import base64
import json
import requests
from datetime import datetime
from io import BytesIO
from typing import Optional
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class VolcengineInpaintingProvider:
    """ Backend docstring """
    
    API_URL = "https://visual.volcengineapi.com"
    SERVICE = "cv"
    REGION = "cn-north-1"
    
    def __init__(self, access_key: str, secret_key: str, timeout: int = 60):
        """
         Inpainting 
        
        Args:
            access_key:  Access Key  
            secret_key:  Secret Key
            timeout: API  () 
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.timeout = timeout
        logger.info("Volcengine Inpainting Provider Khởi tạo (trực tiếpHTTPchế độ) ")
        
    def _encode_image_to_base64(self, image: Image.Image, is_mask: bool = False) -> str:
        """
         PIL Image  base64 
        
        Args:
            image: PIL Image
            is_mask: mask (mask) 
        """
        buffered = BytesIO()
        
        if is_mask:
            # Backend logic
            # Backend logic
            if image.mode != 'L':
                image = image.convert('L')
            # Backend logic
            image.save(buffered, format="PNG", optimize=True)
        else:
            # Backend logic
            if image.mode in ('RGBA', 'LA', 'P'):
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert('RGB')
            # Backend logic
            image.save(buffered, format="JPEG", quality=85)
        
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    @retry(
        stop=stop_after_attempt(3),  # Backend logic
        wait=wait_exponential(multiplier=1, min=2, max=10),  # Backend logic
        retry=retry_if_exception_type((requests.exceptions.RequestException, Exception)),
        reraise=True
    )
    def inpaint_image(
        self,
        original_image: Image.Image,
        mask_image: Image.Image,
        inpaint_mode: str = "remove",
        full_page_image: Optional[Image.Image] = None,
        crop_box: Optional[tuple] = None
    ) -> Optional[Image.Image]:
        """
         () 
        
        Args:
            original_image: 
            mask_image:  (=, =) 
            inpaint_mode: 
            
        Returns:
            ,  None
        """
        try:
            logger.info("🚀 Bắt đầu gọi Volcengine inpainting (trực tiếpHTTP) ")
            
            # Backend logic
            max_dimension = 2048
            if max(original_image.size) > max_dimension:
                ratio = max_dimension / max(original_image.size)
                new_size = tuple(int(dim * ratio) for dim in original_image.size)
                original_image = original_image.resize(new_size, Image.LANCZOS)
                mask_image = mask_image.resize(new_size, Image.LANCZOS)
                logger.info(f"✂️ Nén ảnh: {original_image.size}")
            
            # Backend logic
            logger.info("📦 Mã hóa ảnh sangbase64...")
            original_base64 = self._encode_image_to_base64(original_image, is_mask=False)
            mask_base64 = self._encode_image_to_base64(mask_image, is_mask=True)
            logger.info(f"✅ Hoàn tất mã hóa: ảnh gốc={len(original_base64)} bytes, mask={len(mask_base64)} bytes")
            
            # Backend logic
            # Backend logic
            # Backend logic
            request_body = {
                "req_key": "i2i_inpainting",
                "binary_data_base64": [original_base64, mask_base64],
                "dilate_size": 10,  # Backend logic
                "quality": "H",  # Backend logic
                "steps": 50,  # Backend logic
                "strength": 0.85  # Backend logic
            }
            
            # Backend logic
            url = f"{self.API_URL}/?Action=CVProcess&Version=2022-08-31"
            
            # Backend logic
            headers = {
                "Content-Type": "application/json",
                "X-Date": datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            }
            
            logger.info(f"🌐 Gửi yêu cầu tới: {url}")
            logger.debug(f"Kích thước nội dung yêu cầu: {len(json.dumps(request_body))} bytes")
            
            # Backend logic
            from volcengine.visual.VisualService import VisualService
            service = VisualService()
            service.set_ak(self.access_key)
            service.set_sk(self.secret_key)
            
            # Backend logic
            logger.info("Sử dụngSDKGửi yêu cầu (có chữ ký hợp lệ) ")
            
            try:
                # Backend logic
                response = service.json(
                    "CVProcess",
                    {},  # query params
                    json.dumps(request_body)  # body
                )
                
                # Backend logic
                if isinstance(response, str):
                    response = json.loads(response)
                    
            except Exception as e:
                error_str = str(e)
                logger.error(f"SDKlỗi khi gọi: {error_str}")
                
                # Backend logic
                if error_str.startswith("b'") and error_str.endswith("'"):
                    try:
                        response_text = error_str[2:-1]  # Backend logic
                        response = json.loads(response_text)
                    except Exception:
                        logger.error("Không thể phân tích phản hồi lỗi")
                        return None
                else:
                    return None
            
            # Backend logic
            logger.debug(f"APIphản hồi: {json.dumps(response, ensure_ascii=False)[:300]}")
            
            if response.get("code") == 10000 or response.get("status") == 10000:
                data = response.get("data", {})
                
                # Backend logic
                result_base64 = None
                if "binary_data_base64" in data and data["binary_data_base64"]:
                    result_base64 = data["binary_data_base64"][0]
                elif "image_base64" in data:
                    result_base64 = data["image_base64"]
                elif "result_image" in data:
                    result_base64 = data["result_image"]
                
                if result_base64:
                    image_data = base64.b64decode(result_base64)
                    inpainted_image = Image.open(BytesIO(image_data))
                    logger.info(f"✅ Inpaintingthành công! kết quả: {inpainted_image.size}, {inpainted_image.mode}")
                    
                    # Backend logic
                    # Backend logic
                    if inpainted_image.size != original_image.size:
                        logger.warning(f"kích thước không khớp, điều chỉnhinpaintingkết quả: {inpainted_image.size} -> {original_image.size}")
                        inpainted_image = inpainted_image.resize(original_image.size, Image.LANCZOS)
                    
                    # Backend logic
                    if mask_image.size != original_image.size:
                        mask_image = mask_image.resize(original_image.size, Image.LANCZOS)
                    
                    # Backend logic
                    if inpainted_image.mode != 'RGB':
                        inpainted_image = inpainted_image.convert('RGB')
                    if original_image.mode != 'RGB':
                        original_image = original_image.convert('RGB')
                    
                    # Backend logic
                    mask_for_composite = mask_image.convert('L')
                    
                    # Backend logic
                    # Backend logic
                    # Backend logic
                    # Backend logic
                    result_image = Image.composite(inpainted_image, original_image, mask_for_composite)
                    
                    logger.info(f"✅ Hoàn tất ghép ảnh! kích thước cuối cùng: {result_image.size}, {result_image.mode}")
                    return result_image
                else:
                    logger.error(f"❌ Không có dữ liệu ảnh trong phản hồi, keys: {list(data.keys())}")
                    return None
            else:
                code = response.get("code") or response.get("status")
                message = response.get("message", "Lỗi không xác định")
                logger.error(f"❌ APILỗi: code={code}, message={message}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Inpaintingthất bại: {str(e)}", exc_info=True)
            return None
    