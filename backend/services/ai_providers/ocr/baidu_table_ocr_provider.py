"""
OCR Provider
AI,

API: https://ai.baidu.com/ai-doc/OCR/1k3h7y3db
"""
import logging
import base64
import requests
import urllib.parse
from typing import Dict, List, Any, Optional
from PIL import Image
import io
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaiduTableOCRProvider:
    """ Backend docstring """

    def __init__(self, api_key: str):
        """
        OCR Provider

        Args:
            api_key: API Key (BCEv3: bce-v3/ALTAK-...) Access Token
        """
        self.api_key = api_key
        self.api_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/table"

        if api_key.startswith('bce-v3/'):
            logger.info("✅ Khởi tạo bảng BaiduOCR Provider (Sử dụngBCEv3 API Key)")
        else:
            logger.info("✅ Khởi tạo bảng BaiduOCR Provider (Sử dụngAccess Token)")
    
    @retry(
        stop=stop_after_attempt(3),  # Backend logic
        wait=wait_exponential(multiplier=0.5, min=1, max=5),  # Backend logic
        retry=retry_if_exception_type((requests.exceptions.RequestException, Exception)),
        reraise=True
    )
    def recognize_table(
        self,
        image_path: str,
        cell_contents: bool = True,  # Backend logic
        return_excel: bool = False
    ) -> Dict[str, Any]:
        """
         () 
        
        Args:
            image_path: 
            cell_contents: , True
            return_excel: Excel, False
            
        Returns:
            ,:
            - log_id: ID
            - table_num: 
            - tables_result: 
            - cells: ()
            - image_size: 
        """
        logger.info(f"🔍 Bắt đầu nhận diện ảnh bảng: {image_path}")
        
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
                logger.info(f"📦 Hoàn tất mã hóa ảnh: base64={len(image_base64)} bytes, urlencode={len(image_encoded)} bytes")
            
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
                logger.info(f"🔐 Sử dụngBCEv3xác thực chữ ký")
            else:
                # Backend logic
                url = f"{self.api_url}?access_token={self.api_key}"
                logger.info(f"🔐 Sử dụngAccess Tokenxác thực")
            
            # Backend logic
            data = f"image={image_encoded}&cell_contents={'true' if cell_contents else 'false'}&return_excel={'true' if return_excel else 'false'}"
            
            logger.info(f"🌐 Gửi yêu cầu tới bảng BaiduOCR API...")
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
            table_num = result.get('table_num', 0)
            tables_result = result.get('tables_result', [])
            excel_file = result.get('excel_file', None)
            
            logger.info(f"✅ Nhận diện bảng thành công! log_id={log_id}, nhận diện được {table_num} bảng")
            
            # Backend logic
            cells = []
            for table_idx, table in enumerate(tables_result):
                table_location = table.get('table_location', [])
                header = table.get('header', [])
                body = table.get('body', [])
                footer = table.get('footer', [])
                
                logger.info(f" Bảng {table_idx + 1}: header={len(header)}, body={len(body)}, footer={len(footer)}")
                
                # Backend logic
                for idx, header_cell in enumerate(header):
                    cell_info = {
                        'table_idx': table_idx,
                        'section': 'header',
                        'section_idx': idx,
                        'text': header_cell.get('words', ''),
                        'bbox': self._location_to_bbox(header_cell.get('location', [])),
                    }
                    cells.append(cell_info)
                
                # Backend logic
                for cell in body:
                    cell_info = {
                        'table_idx': table_idx,
                        'section': 'body',
                        'row_start': cell.get('row_start', 0),
                        'row_end': cell.get('row_end', 0),
                        'col_start': cell.get('col_start', 0),
                        'col_end': cell.get('col_end', 0),
                        'text': cell.get('words', ''),
                        'bbox': self._location_to_bbox(cell.get('cell_location', [])),
                        'contents': cell.get('contents', []),  # Backend logic
                    }
                    cells.append(cell_info)
                
                # Backend logic
                for idx, footer_cell in enumerate(footer):
                    cell_info = {
                        'table_idx': table_idx,
                        'section': 'footer',
                        'section_idx': idx,
                        'text': footer_cell.get('words', ''),
                        'bbox': self._location_to_bbox(footer_cell.get('location', [])),
                    }
                    cells.append(cell_info)
            
            return {
                'log_id': log_id,
                'table_num': table_num,
                'tables_result': tables_result,
                'cells': cells,
                'image_size': (original_width, original_height),
                'excel_file': excel_file,
            }
            
        except Exception as e:
            logger.error(f"❌ Nhận diện bảng thất bại: {str(e)}")
            raise
    
    def _location_to_bbox(self, location: List[Dict[str, int]]) -> List[int]:
        """
        bbox [x0, y0, x1, y1]
        
        Args:
            location:  [{x, y}, {x, y}, {x, y}, {x, y}]
            
        Returns:
            bbox [x0, y0, x1, y1]
        """
        if not location or len(location) < 2:
            return [0, 0, 0, 0]
        
        xs = [p['x'] for p in location]
        ys = [p['y'] for p in location]
        
        return [min(xs), min(ys), max(xs), max(ys)]
    
    def get_table_structure(self, cells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        
        
        Args:
            cells: 
            
        Returns:
            :
            - rows: 
            - cols: 
            - cells_by_position: {(row, col): cell_info}
        """
        if not cells:
            return {'rows': 0, 'cols': 0, 'cells_by_position': {}}
        
        max_row = max(cell['row_end'] for cell in cells)
        max_col = max(cell['col_end'] for cell in cells)
        
        cells_by_position = {}
        for cell in cells:
            # Backend logic
            key = (cell['row_start'], cell['col_start'])
            cells_by_position[key] = cell
        
        return {
            'rows': max_row,
            'cols': max_col,
            'cells_by_position': cells_by_position,
        }


def create_baidu_table_ocr_provider(
    api_key: Optional[str] = None
) -> Optional[BaiduTableOCRProvider]:
    """
    OCR Provider

    Args:
        api_key: API Key (BCEv3Access Token) , Flask config

    Returns:
        BaiduTableOCRProvider, api_keyNone
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
        logger.warning("⚠️ Chưa cấu hình BaiduAPI Key, bỏ qua nhận diện bảng Baidu")
        return None

    return BaiduTableOCRProvider(api_key)