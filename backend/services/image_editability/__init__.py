"""


: 
-  - , 
-  - 
-  - , 

: 
-  (BBox, EditableElement, EditableImage) 
-  (ElementExtractor) 
- Inpaint (InpaintProvider) 
-  (ServiceConfig) 
-  (ImageEditabilityService) 

Example:
    >>> from services.image_editability import ServiceConfig, ImageEditabilityService
    >>> 
    >>> # Backend logic
    >>> config = ServiceConfig.from_defaults(mineru_token="your_token")
    >>> 
    >>> # Backend logic
    >>> service = ImageEditabilityService(config)
    >>> 
    >>> # Backend logic
    >>> result = service.make_image_editable("image.png")
    >>> 
    >>> # Backend logic
    >>> from concurrent.futures import ThreadPoolExecutor, as_completed
    >>> 
    >>> images = ["img1.png", "img2.png", "img3.png"]
    >>> with ThreadPoolExecutor(max_workers=4) as executor:
    ...     futures = {executor.submit(service.make_image_editable, img): img 
    ...                for img in images}
    ...     results = {images[i]: future.result() 
    ...                for i, future in enumerate(as_completed(futures))}
"""

# Backend logic
from .data_models import BBox, EditableElement, EditableImage

# Backend logic
from .coordinate_mapper import CoordinateMapper

# Backend logic
from .extractors import (
    ElementExtractor,
    MinerUElementExtractor,
    BaiduOCRElementExtractor,
    BaiduAccurateOCRElementExtractor,
    ExtractorRegistry
)

# Backend logic
from .hybrid_extractor import (
    HybridElementExtractor,
    BBoxUtils,
    create_hybrid_extractor
)

# Backend logic
from .inpaint_providers import (
    InpaintProvider,
    DefaultInpaintProvider,
    GenerativeEditInpaintProvider,
    BaiduInpaintProvider,
    HybridInpaintProvider,
    InpaintProviderRegistry
)

# Backend logic
from .text_attribute_extractors import (
    TextStyleResult,
    TextAttributeExtractor,
    CaptionModelTextAttributeExtractor,
    TextAttributeExtractorRegistry
)

# Backend logic
from .factories import (
    ExtractorFactory,
    InpaintProviderFactory,
    TextAttributeExtractorFactory,
    ServiceConfig
)

# Backend logic
from .service import ImageEditabilityService

__all__ = [
    # Backend logic
    'BBox',
    'EditableElement',
    'EditableImage',
    # Backend logic
    'CoordinateMapper',
    # Backend logic
    'ElementExtractor',
    'MinerUElementExtractor',
    'BaiduOCRElementExtractor',
    'BaiduAccurateOCRElementExtractor',
    'ExtractorRegistry',
    # Backend logic
    'HybridElementExtractor',
    'BBoxUtils',
    'create_hybrid_extractor',
    # Backend logic
    'InpaintProvider',
    'DefaultInpaintProvider',
    'GenerativeEditInpaintProvider',
    'BaiduInpaintProvider',
    'HybridInpaintProvider',
    'InpaintProviderRegistry',
    # Backend logic
    'TextStyleResult',
    'TextAttributeExtractor',
    'CaptionModelTextAttributeExtractor',
    'TextAttributeExtractorRegistry',
    # Backend logic
    'ExtractorFactory',
    'InpaintProviderFactory',
    'TextAttributeExtractorFactory',
    'ServiceConfig',
    # Backend logic
    'ImageEditabilityService',
]