"""
 () OCR Provider
, , , 

API: https://ai.baidu.com/ai-doc/OCR/1k3h7y3db
"""
import logging
import base64
import requests
import urllib.parse
from typing import Dict, List, Any, Optional, Literal
from PIL import Image
import io
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


# Backend logic
LanguageType = Literal[
    'auto_detect',  # Backend logic
    'CHN_ENG',      # Backend logic
    'ENG',          # Backend logic
    'JAP',          # Backend logic
    'KOR',          # Backend logic
    'FRE',          # Backend logic
    'SPA',          # Backend logic
    'POR',          # Backend logic
    'GER',          # Backend logic
    'ITA',          # Backend logic
    'RUS',          # Backend logic
    'DAN',          # Backend logic
    'DUT',          # Backend logic
    'MAL',          # Backend logic
    'SWE',          # Backend logic
    'IND',          # Backend logic
    'POL',          # Backend logic
    'ROM',          # Backend logic
    'TUR',          # Backend logic
    'GRE',          # Backend logic
    'HUN',          # Backend logic
    'THA',          # Backend logic
    'VIE',          # Backend logic
    'ARA',          # Backend logic
    'HIN',          # Backend logic
]


class BaiduAccurateOCRProvider:
    """
    OCR Provider -  () 
    
    :
    - 
    - 25
    -  () 
    - 
    - 
    """

    def __init__(self, api_key: str):
        """
        OCR Provider

        Args:
            api_key: API Key (BCEv3: bce-v3/ALTAK-...) Access Token
        """
        self.api_key = api_key
        self.api_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate"

        if api_key.startswith('bce-v3/'):
            logger.info("✅ Khởi tạo Baidu độ chính xác caoOCR Provider (Sử dụngBCEv3 API Key)")
        else:
            logger.info("✅ Khởi tạo Baidu độ chính xác caoOCR Provider (Sử dụngAccess Token)")
    
    @retry(
        stop=stop_after_attempt(3),  # Backend logic
        wait=wait_exponential(multiplier=0.5, min=1, max=5),  # Backend logic
        retry=retry_if_exception_type((requests.exceptions.RequestException, Exception)),
        reraise=True
    )
    def recognize(
        self,
        image_path: str,
        language_type: LanguageType = 'CHN_ENG',
        recognize_granularity: Literal['big', 'small'] = 'big',
        detect_direction: bool = False,
        vertexes_location: bool = False,
        paragraph: bool = False,
        probability: bool = False,
        char_probability: bool = False,
        multidirectional_recognize: bool = False,
        eng_granularity: Optional[Literal['word', 'letter']] = None,
    ) -> Dict[str, Any]:
        """
         () 
        
        Args:
            image_path: 
            language_type: , 
            recognize_granularity: , big=, small=
            detect_direction: 
            vertexes_location: 
            paragraph: 
            probability: 
            char_probability:  (recognize_granularity=small) 
            multidirectional_recognize: 
            eng_granularity:  (word/letter) , recognize_granularity=small
            
        Returns:
            , :
            - log_id: ID
            - words_result_num: 
            - words_result: 
                - words: 
                - location:  {left, top, width, height}
                - chars:  (recognize_granularity=small) 
                - probability:  (probability=true) 
                - vertexes_location:  (vertexes_location=true) 
            - direction:  (detect_direction=true) 
            - paragraphs_result:  (paragraph=true) 
            - image_size: 
        """
        logger.info(f"🔍 Bắt đầu độ chính xác caoOCRnhận diện: {image_path}")
        
        try:
            # Backend logic
            original_width, original_height = 0, 0
            with Image.open(image_path) as img:
                # Backend logic
                original_width, original_height = img.size
                logger.info(f"📏 Kích thước ảnh: {original_width}x{original_height}")
                
                # Backend logic
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Backend logic
                max_size = 8192
                min_size = 15
                width, height = img.size
                
                if width < min_size or height < min_size:
                    logger.warning(f"⚠️ Ảnh quá nhỏ: {width}x{height}, cạnh ngắn nhất cần tối thiểu{min_size}px")
                
                if width > max_size or height > max_size:
                    ratio = min(max_size / width, max_size / height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logger.info(f"✂️ Nén ảnh: {img.size}")
                
                # Backend logic
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=95)
                image_bytes = buffer.getvalue()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                # URL encode
                image_encoded = urllib.parse.quote(image_base64)
                logger.info(f"📦 Hoàn tất mã hóa ảnh: base64={len(image_base64)} bytes")
            
            # Backend logic
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            }
            
            # Backend logic
            if self.api_key.startswith('bce-v3/'):
                # Backend logic
                headers['Authorization'] = f'Bearer {self.api_key}'
                url = self.api_url
                logger.info("🔐 Sử dụngBCEv3xác thực chữ ký")
            else:
                # Backend logic
                url = f"{self.api_url}?access_token={self.api_key}"
                logger.info("🔐 Sử dụngAccess Tokenxác thực")
            
            # Backend logic
            form_data = {
                'image': image_encoded,
                'language_type': language_type,
                'recognize_granularity': recognize_granularity,
                'detect_direction': 'true' if detect_direction else 'false',
                'vertexes_location': 'true' if vertexes_location else 'false',
                'paragraph': 'true' if paragraph else 'false',
                'probability': 'true' if probability else 'false',
                'multidirectional_recognize': 'true' if multidirectional_recognize else 'false',
            }
            
            if recognize_granularity == 'small' and char_probability:
                form_data['char_probability'] = 'true'
            
            if recognize_granularity == 'small' and eng_granularity:
                form_data['eng_granularity'] = eng_granularity
            
            # Backend logic
            data = '&'.join([f"{k}={v}" for k, v in form_data.items()])
            
            logger.info("🌐 Gửi yêu cầu tới Baidu độ chính xác caoOCR API...")
            response = requests.post(url, headers=headers, data=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Backend logic
            if 'error_code' in result:
                error_msg = result.get('error_msg', 'Unknown error')
                error_code = result.get('error_code')
                logger.error(f"❌ BaiduAPILỗi: [{error_code}] {error_msg}")
                raise Exception(f"Baidu API error [{error_code}]: {error_msg}")
            
            # Backend logic
            log_id = result.get('log_id', '')
            words_result_num = result.get('words_result_num', 0)
            words_result = result.get('words_result', [])
            direction = result.get('direction', None)
            paragraphs_result_num = result.get('paragraphs_result_num', 0)
            paragraphs_result = result.get('paragraphs_result', [])
            
            logger.info(f"✅ độ chính xác caoOCRnhận diện thành công! log_id={log_id}, nhận diện được {words_result_num} dòng văn bản")
            
            # Backend logic
            text_lines = []
            for line in words_result:
                line_info = {
                    'text': line.get('words', ''),
                    'location': line.get('location', {}),
                    'bbox': self._location_to_bbox(line.get('location', {})),
                }
                
                # Backend logic
                if 'chars' in line:
                    line_info['chars'] = []
                    for char in line['chars']:
                        char_info = {
                            'char': char.get('char', ''),
                            'location': char.get('location', {}),
                            'bbox': self._location_to_bbox(char.get('location', {})),
                        }
                        if 'char_prob' in char:
                            char_info['probability'] = char['char_prob']
                        line_info['chars'].append(char_info)
                
                # Backend logic
                if 'probability' in line:
                    line_info['probability'] = line['probability']
                
                # Backend logic
                if 'vertexes_location' in line:
                    line_info['vertexes_location'] = line['vertexes_location']
                
                if 'finegrained_vertexes_location' in line:
                    line_info['finegrained_vertexes_location'] = line['finegrained_vertexes_location']
                
                if 'min_finegrained_vertexes_location' in line:
                    line_info['min_finegrained_vertexes_location'] = line['min_finegrained_vertexes_location']
                
                text_lines.append(line_info)
            
            # Backend logic
            paragraphs = []
            if paragraphs_result:
                for para in paragraphs_result:
                    para_info = {
                        'words_result_idx': para.get('words_result_idx', []),
                    }
                    if 'finegrained_vertexes_location' in para:
                        para_info['finegrained_vertexes_location'] = para['finegrained_vertexes_location']
                    if 'min_finegrained_vertexes_location' in para:
                        para_info['min_finegrained_vertexes_location'] = para['min_finegrained_vertexes_location']
                    paragraphs.append(para_info)
            
            return {
                'log_id': log_id,
                'words_result_num': words_result_num,
                'words_result': words_result,  # Backend logic
                'text_lines': text_lines,  # Backend logic
                'direction': direction,
                'paragraphs_result_num': paragraphs_result_num,
                'paragraphs_result': paragraphs_result,  # Backend logic
                'paragraphs': paragraphs,  # Backend logic
                'image_size': (original_width, original_height),
            }
            
        except Exception as e:
            logger.error(f"❌ độ chính xác caoOCRnhận diện thất bại: {str(e)}")
            raise
    
    def _location_to_bbox(self, location: Dict[str, int]) -> List[int]:
        """
        locationbbox [x0, y0, x1, y1]
        
        Args:
            location: {left, top, width, height}
            
        Returns:
            bbox [x0, y0, x1, y1]
        """
        if not location:
            return [0, 0, 0, 0]
        
        left = location.get('left', 0)
        top = location.get('top', 0)
        width = location.get('width', 0)
        height = location.get('height', 0)
        
        return [left, top, left + width, top + height]
    
    def get_full_text(self, result: Dict[str, Any], separator: str = '\n') -> str:
        """
        
        
        Args:
            result: recognize()
            separator: , 
            
        Returns:
            
        """
        text_lines = result.get('text_lines', [])
        return separator.join([line.get('text', '') for line in text_lines])
    
    def get_text_with_positions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        
        
        Args:
            result: recognize()
            
        Returns:
            ,  text  bbox
        """
        text_lines = result.get('text_lines', [])
        return [
            {
                'text': line.get('text', ''),
                'bbox': line.get('bbox', [0, 0, 0, 0]),
            }
            for line in text_lines
        ]


def create_baidu_accurate_ocr_provider(
    api_key: Optional[str] = None
) -> Optional[BaiduAccurateOCRProvider]:
    """
    OCR Provider

    Args:
        api_key: API Key (BCEv3Access Token) , Flask config

    Returns:
        BaiduAccurateOCRProvider, api_keyNone
    """
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
        logger.warning("⚠️ Chưa cấu hình BaiduAPI Key, bỏ qua Baidu độ chính xác caoOCR")
        return None

    return BaiduAccurateOCRProvider(api_key)