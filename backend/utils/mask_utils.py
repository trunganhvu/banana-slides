"""

 (bbox) 
"""
import logging
from typing import List, Tuple, Union, Callable
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


# Backend logic

def normalize_bbox(bbox: Union[Tuple, List, dict]) -> Tuple[int, int, int, int]:
    """
    bbox (x1, y1, x2, y2) 
    
    : 
    - /: (x1, y1, x2, y2)
    - dictionary: {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    - dictionary: {"x": x, "y": y, "width": w, "height": h}
    """
    if isinstance(bbox, dict):
        if 'x1' in bbox:
            return (bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2'])
        elif 'x' in bbox:
            return (bbox['x'], bbox['y'], 
                   bbox['x'] + bbox['width'], 
                   bbox['y'] + bbox['height'])
        else:
            raise ValueError(f"Không nhận diện đượcbboxĐịnh dạng dictionary: {bbox}")
    elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
        return tuple(bbox)
    else:
            raise ValueError(f"Không nhận diện đượcbboxĐịnh dạng dictionary: {bbox}")


def normalize_bboxes(bboxes: List[Union[Tuple, List, dict]]) -> List[Tuple[int, int, int, int]]:
    """ Backend docstring """
    result = []
    for bbox in bboxes:
        try:
            result.append(normalize_bbox(bbox))
        except ValueError as e:
            logger.warning(str(e))
    return result


def merge_two_boxes(box1: Tuple, box2: Tuple) -> Tuple[int, int, int, int]:
    """ Backend docstring """
    return (
        min(box1[0], box2[0]),
        min(box1[1], box2[1]),
        max(box1[2], box2[2]),
        max(box1[3], box2[3])
    )


def _iterative_merge(
    bboxes: List[Tuple[int, int, int, int]],
    should_merge_fn: Callable[[Tuple, Tuple], bool]
) -> List[Tuple[int, int, int, int]]:
    """
    
    
    Args:
        bboxes: bbox
        should_merge_fn: bbox
    
    Returns:
        bbox
    """
    if not bboxes:
        return []
    if len(bboxes) == 1:
        return list(bboxes)
    
    normalized = list(bboxes)
    merged = True
    
    while merged:
        merged = False
        new_boxes = []
        used = set()
        
        for i, box1 in enumerate(normalized):
            if i in used:
                continue
            
            current_box = box1
            
            for j, box2 in enumerate(normalized):
                if j <= i or j in used:
                    continue
                
                if should_merge_fn(current_box, box2):
                    current_box = merge_two_boxes(current_box, box2)
                    used.add(j)
                    merged = True
            
            new_boxes.append(current_box)
            used.add(i)
        
        normalized = new_boxes
    
    return normalized


def create_mask_from_bboxes(
    image_size: Tuple[int, int],
    bboxes: List[Union[Tuple[int, int, int, int], dict]],
    mask_color: Tuple[int, int, int] = (255, 255, 255),
    background_color: Tuple[int, int, int] = (0, 0, 0),
    expand_pixels: int = 0
) -> Image.Image:
    """
    
    
    Args:
        image_size:  (width, height)
        bboxes: , : 
                - : (x1, y1, x2, y2)  (x1,y1) , (x2,y2) 
    - dictionary: {"x": x, "y": y, "width": w, "height": h}
    - dictionary: {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        mask_color:  () , 
        background_color:  () , 
        expand_pixels: ,  () 
        
    Returns:
        PIL Image , RGB 
    """
    try:
        # Backend logic
        mask = Image.new('RGB', image_size, background_color)
        draw = ImageDraw.Draw(mask)
        
        logger.info(f"Tạo ảnh mặt nạ, kích thước: {image_size}, bboxsố lượng: {len(bboxes)}")
        
        # Backend logic
        bbox_list = []  # Backend logic
        for i, bbox in enumerate(bboxes):
            # Backend logic
            if isinstance(bbox, dict):
                if 'x1' in bbox and 'y1' in bbox and 'x2' in bbox and 'y2' in bbox:
                    # Backend logic
                    x1 = bbox['x1']
                    y1 = bbox['y1']
                    x2 = bbox['x2']
                    y2 = bbox['y2']
                elif 'x' in bbox and 'y' in bbox and 'width' in bbox and 'height' in bbox:
                    # Backend logic
                    x1 = bbox['x']
                    y1 = bbox['y']
                    x2 = x1 + bbox['width']
                    y2 = y1 + bbox['height']
                else:
                    logger.warning(f"Không nhận diện được bbox Định dạng dictionary: {bbox}")
                    continue
            elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
                # Backend logic
                x1, y1, x2, y2 = bbox
            else:
                logger.warning(f"Không nhận diện được định dạng bbox: {bbox}")
                continue
            
            # Backend logic
            x1_orig, y1_orig, x2_orig, y2_orig = x1, y1, x2, y2
            
            # Backend logic
            if expand_pixels > 0:
                # Backend logic
                x1 = max(0, x1 - expand_pixels)
                y1 = max(0, y1 - expand_pixels)
                x2 = min(image_size[0], x2 + expand_pixels)
                y2 = min(image_size[1], y2 + expand_pixels)
            elif expand_pixels < 0:
                # Backend logic
                shrink = abs(expand_pixels)
                x1 = x1 + shrink
                y1 = y1 + shrink
                x2 = x2 - shrink
                y2 = y2 - shrink
                # Backend logic
                if x2 <= x1 or y2 <= y1:
                    logger.warning(f"bbox {i+1} không hợp lệ sau khi thu hẹp: ({x1}, {y1}, {x2}, {y2}), bỏ qua")
                    continue
            
            # Backend logic
            x1 = max(0, min(x1, image_size[0]))
            y1 = max(0, min(y1, image_size[1]))
            x2 = max(0, min(x2, image_size[0]))
            y2 = max(0, min(y2, image_size[1]))
            
            # Backend logic
            if x2 <= x1 or y2 <= y1:
                logger.warning(f"bbox {i+1} tọa độ cuối cùng không hợp lệ: ({x1}, {y1}, {x2}, {y2}), bỏ qua")
                continue
            
            # Backend logic
            draw.rectangle([x1, y1, x2, y2], fill=mask_color)
            width = x2 - x1
            height = y2 - y1
            if expand_pixels > 0:
                bbox_list.append(f" [{i+1}] Gốc: ({x1_orig}, {y1_orig}, {x2_orig}, {y2_orig}) -> Sau khi mở rộng: ({x1}, {y1}, {x2}, {y2}) kích thước: {width}x{height}")
            elif expand_pixels < 0:
                bbox_list.append(f" [{i+1}] Gốc: ({x1_orig}, {y1_orig}, {x2_orig}, {y2_orig}) -> Sau khi mở rộng: ({x1}, {y1}, {x2}, {y2}) kích thước: {width}x{height}")
            else:
                bbox_list.append(f" [{i+1}] ({x1}, {y1}, {x2}, {y2}) kích thước: {width}x{height}")
            logger.debug(f"bbox {i+1}: ({x1}, {y1}, {x2}, {y2}) kích thước: {width}x{height}")
        
        # Backend logic
        if bbox_list:
            logger.info(f"Đã thêm {len(bbox_list)} bbox mask:")
            for bbox_info in bbox_list:
                logger.info(bbox_info)
        
        logger.info(f"Hoàn tất tạo ảnh mặt nạ")
        return mask
        
    except Exception as e:
        logger.error(f"Tạo ảnh mặt nạ thất bại: {str(e)}", exc_info=True)
        raise


def create_inverse_mask_from_bboxes(
    image_size: Tuple[int, int],
    bboxes: List[Union[Tuple[int, int, int, int], dict]],
    expand_pixels: int = 0
) -> Image.Image:
    """
     ( bbox , ) 
    
    Args:
        image_size:  (width, height)
        bboxes: 
        expand_pixels: 
        
    Returns:
        PIL Image , 
    """
    # Backend logic
    return create_mask_from_bboxes(
        image_size,
        bboxes,
        mask_color=(0, 0, 0),  # Backend logic
        background_color=(255, 255, 255),  # Backend logic
        expand_pixels=expand_pixels
    )


def create_mask_from_image_and_bboxes(
    image: Image.Image,
    bboxes: List[Union[Tuple[int, int, int, int], dict]],
    expand_pixels: int = 0
) -> Image.Image:
    """
     () 
    
    Args:
        image: 
        bboxes: 
        expand_pixels: 
        
    Returns:
        
    """
    return create_mask_from_bboxes(
        image.size,
        bboxes,
        expand_pixels=expand_pixels
    )


def visualize_mask_overlay(
    original_image: Image.Image,
    mask_image: Image.Image,
    alpha: float = 0.5
) -> Image.Image:
    """
    
    
    Args:
        original_image: 
        mask_image: 
        alpha:  (0.0-1.0)
        
    Returns:
        
    """
    try:
        # Backend logic
        if original_image.size != mask_image.size:
            logger.warning(f"Kích thước ảnh không khớp, Điều chỉnh kích thước mặt nạ: {mask_image.size} -> {original_image.size}")
            mask_image = mask_image.resize(original_image.size, Image.LANCZOS)
        
        # Backend logic
        if original_image.mode != 'RGBA':
            original_rgba = original_image.convert('RGBA')
        else:
            original_rgba = original_image.copy()
        
        # Backend logic
        mask_rgba = Image.new('RGBA', original_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask_rgba)
        
        # Backend logic
        mask_array = mask_image.load()
        mask_rgba_array = mask_rgba.load()
        
        for y in range(mask_image.size[1]):
            for x in range(mask_image.size[0]):
                pixel = mask_array[x, y]
                # Backend logic
                if isinstance(pixel, tuple):
                    brightness = sum(pixel) / len(pixel)
                else:
                    brightness = pixel
                
                if brightness > 200:  # Backend logic
                    mask_rgba_array[x, y] = (0, 0, 0, int(128 * alpha))
        
        # Backend logic
        result = Image.alpha_composite(original_rgba, mask_rgba)
        return result.convert('RGB')
        
    except Exception as e:
        logger.error(f"Tạo ảnh mặt nạ thất bại: {str(e)}", exc_info=True)
        return original_image


def merge_vertical_nearby_bboxes(
    bboxes: List[Tuple[int, int, int, int]],
    vertical_gap_ratio: float = 0.8,
    horizontal_overlap_ratio: float = 0.3
) -> List[Tuple[int, int, int, int]]:
    """
     () 
    
     (bbox, ) : 
    - y, bbox
    -  vertical_gap_ratio 
    -  horizontal_overlap_ratio 
    - , 
    
    Args:
        bboxes:  [(x1, y1, x2, y2), ...]
        vertical_gap_ratio: , , 0.8
        horizontal_overlap_ratio: , 0.3
        
    Returns:
        
    """
    if not bboxes or len(bboxes) <= 1:
        return list(bboxes) if bboxes else []
    
    normalized = normalize_bboxes(bboxes)
    if not normalized:
        return []
    
    # Backend logic
    normalized.sort(key=lambda b: b[1])
    
    # Backend logic
    avg_height = sum(b[3] - b[1] for b in normalized) / len(normalized)
    max_vertical_gap = avg_height * vertical_gap_ratio
    
    def get_horizontal_overlap(box1, box2):
        """ Backend docstring """
        overlap_start = max(box1[0], box2[0])
        overlap_end = min(box1[2], box2[2])
        overlap = max(0, overlap_end - overlap_start)
        min_width = min(box1[2] - box1[0], box2[2] - box2[0])
        return overlap / min_width if min_width > 0 else 0
    
    def should_merge_adjacent(box1, box2):
        """ Backend docstring """
        # Backend logic
        v_gap = box2[1] - box1[3]
        
        # Backend logic
        if v_gap > max_vertical_gap:
            return False
        
        # Backend logic
        h_overlap = get_horizontal_overlap(box1, box2)
        if h_overlap >= horizontal_overlap_ratio:
            return True
        
        # Backend logic
        if h_overlap <= 0:
            h_gap = max(0, max(box2[0] - box1[2], box1[0] - box2[2]))
            if h_gap < avg_height:
                return True
        
        return False
    
    # Backend logic
    merge_with_next = []
    for i in range(len(normalized) - 1):
        merge_with_next.append(should_merge_adjacent(normalized[i], normalized[i + 1]))
    
    # Backend logic
    result = []
    current_box = normalized[0]
    
    for i in range(len(merge_with_next)):
        if merge_with_next[i]:
            # Backend logic
            current_box = merge_two_boxes(current_box, normalized[i + 1])
        else:
            # Backend logic
            result.append(current_box)
            current_box = normalized[i + 1]
    
    # Backend logic
    result.append(current_box)
    
    logger.info(f"Gộp các dòng văn bản liền kềbbox: {len(bboxes)} -> {len(result)}")
    return result


def merge_overlapping_bboxes(
    bboxes: List[Tuple[int, int, int, int]],
    merge_threshold: int = 10
) -> List[Tuple[int, int, int, int]]:
    """
    
    
    Args:
        bboxes:  [(x1, y1, x2, y2), ...]
        merge_threshold:  () , 
        
    Returns:
        
    """
    if not bboxes:
        return []
    
    normalized = normalize_bboxes(bboxes)
    if not normalized:
        return []
    
    def should_merge(box1, box2):
        x1, y1, x2, y2 = box1
        bx1, by1, bx2, by2 = box2
        return (x1 - merge_threshold <= bx2 and bx1 <= x2 + merge_threshold and
                y1 - merge_threshold <= by2 and by1 <= y2 + merge_threshold)
    
    result = _iterative_merge(normalized, should_merge)
    logger.info(f"Gộp khung giới hạn: {len(bboxes)} -> {len(result)}")
    return result