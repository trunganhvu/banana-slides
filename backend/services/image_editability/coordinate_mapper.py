"""
 - 
"""
from typing import Tuple
from .data_models import BBox


class CoordinateMapper:
    """ Backend docstring """
    
    @staticmethod
    def local_to_global(
        local_bbox: BBox,
        parent_bbox: BBox,
        local_image_size: Tuple[int, int],
        parent_image_size: Tuple[int, int]
    ) -> BBox:
        """
         () 
        
        Args:
            local_bbox: bbox
            parent_bbox: 
            local_image_size:  (width, height)
            parent_image_size:  (width, height)
        
        Returns:
            bbox
        """
        # Backend logic
        scale_x = parent_bbox.width / local_image_size[0]
        scale_y = parent_bbox.height / local_image_size[1]
        
        # Backend logic
        scaled_bbox = local_bbox.scale(scale_x, scale_y)
        
        # Backend logic
        global_bbox = scaled_bbox.translate(parent_bbox.x0, parent_bbox.y0)
        
        return global_bbox
    
    @staticmethod
    def global_to_local(
        global_bbox: BBox,
        parent_bbox: BBox,
        local_image_size: Tuple[int, int],
        parent_image_size: Tuple[int, int]
    ) -> BBox:
        """
         () 
        
        Args:
            global_bbox: bbox
            parent_bbox: 
            local_image_size:  (width, height)
            parent_image_size:  (width, height)
        
        Returns:
            bbox
        """
        # Backend logic
        translated_bbox = global_bbox.translate(-parent_bbox.x0, -parent_bbox.y0)
        
        # Backend logic
        scale_x = local_image_size[0] / parent_bbox.width
        scale_y = local_image_size[1] / parent_bbox.height
        
        local_bbox = translated_bbox.scale(scale_x, scale_y)
        
        return local_bbox