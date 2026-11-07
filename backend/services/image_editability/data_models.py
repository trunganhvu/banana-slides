"""
 - 
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class BBox:
    """ Backend docstring """
    x0: float
    y0: float
    x1: float
    y1: float
    
    @property
    def width(self) -> float:
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        return self.y1 - self.y0
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """ Backend docstring """
        return (self.x0, self.y0, self.x1, self.y1)
    
    def to_dict(self) -> Dict[str, float]:
        """ Backend docstring """
        return {
            'x0': self.x0,
            'y0': self.y0,
            'x1': self.x1,
            'y1': self.y1
        }
    
    def scale(self, scale_x: float, scale_y: float) -> 'BBox':
        """ Backend docstring """
        return BBox(
            x0=self.x0 * scale_x,
            y0=self.y0 * scale_y,
            x1=self.x1 * scale_x,
            y1=self.y1 * scale_y
        )
    
    def translate(self, offset_x: float, offset_y: float) -> 'BBox':
        """ Backend docstring """
        return BBox(
            x0=self.x0 + offset_x,
            y0=self.y0 + offset_y,
            x1=self.x1 + offset_x,
            y1=self.y1 + offset_y
        )

    def expand(self, px: float, max_w: float, max_h: float) -> 'BBox':
        """ Backend docstring """
        return BBox(
            x0=max(0.0, self.x0 - px),
            y0=max(0.0, self.y0 - px),
            x1=min(float(max_w), self.x1 + px),
            y1=min(float(max_h), self.y1 + px),
        )


@dataclass
class EditableElement:
    """ Backend docstring """
    element_id: str  # Backend logic
    element_type: str  # Backend logic
    bbox: BBox  # Backend logic
    bbox_global: BBox  # Backend logic
    content: Optional[str] = None  # Backend logic
    image_path: Optional[str] = None  # Backend logic

    # Backend logic
    # Backend logic
    is_icon: Optional[bool] = None
    
    # Backend logic
    children: List['EditableElement'] = field(default_factory=list)
    
    # Backend logic
    inpainted_background_path: Optional[str] = None
    
    # Backend logic
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """ Backend docstring """
        result = {
            'element_id': self.element_id,
            'element_type': self.element_type,
            'bbox': self.bbox.to_dict(),
            'bbox_global': self.bbox_global.to_dict(),
            'content': self.content,
            'image_path': self.image_path,
            'inpainted_background_path': self.inpainted_background_path,
            'is_icon': self.is_icon,
            'metadata': self.metadata,
            'children': [child.to_dict() for child in self.children]
        }
        return result


@dataclass
class EditableImage:
    """ Backend docstring """
    image_id: str  # Backend logic
    image_path: str  # Backend logic
    width: int  # Backend logic
    height: int  # Backend logic
    
    # Backend logic
    elements: List[EditableElement] = field(default_factory=list)
    
    # Backend logic
    clean_background: Optional[str] = None
    
    # Backend logic
    depth: int = 0
    
    # Backend logic
    parent_id: Optional[str] = None
    
    # Backend logic
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """ Backend docstring """
        return {
            'image_id': self.image_id,
            'image_path': self.image_path,
            'width': self.width,
            'height': self.height,
            'elements': [elem.to_dict() for elem in self.elements],
            'clean_background': self.clean_background,
            'depth': self.depth,
            'parent_id': self.parent_id,
            'metadata': self.metadata
        }
