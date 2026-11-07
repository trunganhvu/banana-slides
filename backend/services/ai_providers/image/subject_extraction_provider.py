""" Backend docstring """
from typing import Optional, Protocol, runtime_checkable

from PIL import Image


@runtime_checkable
class SubjectExtractionProvider(Protocol):
    """ provider . 

     extract_subject  provider, 
     RMBG ONNX  BRIA  API . 
    """

    def extract_subject(self, image: Image.Image) -> Optional[Image.Image]:
        """ Backend docstring """
        ...