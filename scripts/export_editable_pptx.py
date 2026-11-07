#!/usr/bin/env python3
"""
 PPTX 

 PPTX 


:
    # Config
    python scripts/export_editable_pptx.py path/to/image.png
    
    # Config
    python scripts/export_editable_pptx.py img1.png img2.png img3.png
    
    # Config
    python scripts/export_editable_pptx.py path/to/images/
    
    # Config
    python scripts/export_editable_pptx.py image.png -o output.pptx
    
    # Config
    python scripts/export_editable_pptx.py image.png --extractor mineru
    python scripts/export_editable_pptx.py image.png --extractor hybrid
    
    # Config
    python scripts/export_editable_pptx.py image.png --inpaint baidu
    python scripts/export_editable_pptx.py image.png --inpaint generative
    python scripts/export_editable_pptx.py image.png --inpaint hybrid

:
     .env 
    - MINERU_TOKEN: MinerU API token
    - BAIDU_API_KEY, BAIDU_SECRET_KEY:  API  baidu/hybrid 
    - GEMINI_API_KEY  OPENAI_API_KEY:  generative/hybrid 

:
    - 'generative'  'hybrid'  API
    - 'baidu'  API
    - 'mineru'  'hybrid'  MinerU API
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Config
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

# Config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_flask_app():
    """ Flask """
    from dotenv import load_dotenv
    
    # Config
    env_path = PROJECT_ROOT / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f": {env_path}")
    
    # Config
    from app import create_app
    app = create_app()
    return app


def collect_image_paths(paths: List[str]) -> List[str]:
    """"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
    result = []
    
    for path_str in paths:
        path = Path(path_str)
        
        if path.is_file():
            if path.suffix.lower() in image_extensions:
                result.append(str(path.resolve()))
            else:
                logger.warning(f": {path}")
        elif path.is_dir():
            for file in sorted(path.iterdir()):
                if file.suffix.lower() in image_extensions:
                    result.append(str(file.resolve()))
        else:
            logger.warning(f": {path}")
    
    return result


def create_service_config(
    extractor_method: str = 'hybrid',
    inpaint_method: str = 'hybrid'
):
    """
    
    
    Args:
        extractor_method:  ('mineru'  'hybrid')
        inpaint_method:  ('generative', 'baidu', 'hybrid')
    """
    from services.image_editability import ServiceConfig
    
    # Config
    use_hybrid_extractor = (extractor_method == 'hybrid')
    use_hybrid_inpaint = (inpaint_method == 'hybrid')
    
    logger.info(f": ={extractor_method}, ={inpaint_method}")
    
    config = ServiceConfig.from_defaults(
        use_hybrid_extractor=use_hybrid_extractor,
        use_hybrid_inpaint=use_hybrid_inpaint,
        max_depth=1  # 
    )
    
    # Config
    if inpaint_method != 'hybrid':
        from services.image_editability import (
            InpaintProviderFactory,
            InpaintProviderRegistry
        )
        
        inpaint_registry = InpaintProviderRegistry()
        
        if inpaint_method == 'generative':
            provider = InpaintProviderFactory.create_generative_edit_provider()
            inpaint_registry.register_default(provider)
            logger.info(" API")
        elif inpaint_method == 'baidu':
            provider = InpaintProviderFactory.create_baidu_inpaint_provider()
            if provider:
                inpaint_registry.register_default(provider)
                logger.info("")
            else:
                logger.warning("")
                provider = InpaintProviderFactory.create_generative_edit_provider()
                inpaint_registry.register_default(provider)
        
        config.inpaint_registry = inpaint_registry
    
    return config


def export_editable_pptx(
    image_paths: List[str],
    output_file: str,
    extractor_method: str = 'hybrid',
    inpaint_method: str = 'hybrid',
    extract_text_styles: bool = True
):
    """
     PPTX
    
    Args:
        image_paths: 
        output_file: 
        extractor_method: 
        inpaint_method: 
        extract_text_styles: 
    """
    from services.image_editability import ImageEditabilityService
    from services.export_service import ExportService
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    logger.info(f" {len(image_paths)} ...")
    
    # Config
    config = create_service_config(extractor_method, inpaint_method)
    service = ImageEditabilityService(config)
    
    # Config
    logger.info(" 1/3: ...")
    editable_images = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(service.make_image_editable, path): idx
            for idx, path in enumerate(image_paths)
        }
        
        results = [None] * len(image_paths)
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
                logger.info(f"  : {image_paths[idx]}")
            except Exception as e:
                logger.error(f"  : {image_paths[idx]} - {e}")
                raise
        
        editable_images = results
    
    # Config
    text_attribute_extractor = None
    if extract_text_styles:
        logger.info(" 2/3: ...")
        try:
            from services.image_editability import TextAttributeExtractorFactory
            text_attribute_extractor = TextAttributeExtractorFactory.create_caption_model_extractor()
            logger.info("   API")
        except Exception as e:
            logger.warning(f"  : {e}")
    else:
        logger.info(" 2/3: ")
    
    # Config
    logger.info(" 3/3:  PPTX...")
    
    def progress_callback(step, message, percent):
        logger.info(f"  [{percent}%] {step}: {message}")
    
    # Config
    if os.path.exists(output_file):
        output_file = output_file.rsplit('.', 1)[0] + '_1.pptx'
        logger.warning(f": {output_file}")
    
    # Config
    # Config
    if editable_images:
        # Config
        ASPECT_RATIO_16_9 = 16 / 9  # ≈ 1.7778
        ASPECT_RATIO_TOLERANCE = 0.02  # 2%
        
        # Config
        min_width = float('inf')
        min_height = float('inf')
        
        for idx, img in enumerate(editable_images):
            aspect_ratio = img.width / img.height
            ratio_diff = abs(aspect_ratio - ASPECT_RATIO_16_9) / ASPECT_RATIO_16_9
            
            if ratio_diff > ASPECT_RATIO_TOLERANCE:
                logger.error(f" {idx + 1} ({image_paths[idx]}) 16:9: "
                           f"{img.width}x{img.height} ( {aspect_ratio:.4f},  {ASPECT_RATIO_16_9:.4f})")
                raise ValueError(f"16:9 {idx + 1}  ({img.width}x{img.height}) ")
            
            min_width = min(min_width, img.width)
            min_height = min(min_height, img.height)
            logger.info(f" {idx + 1}: {img.width}x{img.height} ( {aspect_ratio:.4f})")
        
        slide_width_pixels = int(min_width)
        slide_height_pixels = int(min_height)
        logger.info(f": {slide_width_pixels}x{slide_height_pixels}")
        
        # Config
        if any(img.width != slide_width_pixels or img.height != slide_height_pixels for img in editable_images):
            logger.warning(f" {slide_width_pixels}x{slide_height_pixels}")
    else:
        # Config
        slide_width_pixels = 1920
        slide_height_pixels = 1080
        logger.warning(": 1920x1080")
    
    ExportService.create_editable_pptx_with_recursive_analysis(
        editable_images=editable_images,
        output_file=output_file,
        slide_width_pixels=slide_width_pixels,
        slide_height_pixels=slide_height_pixels,
        text_attribute_extractor=text_attribute_extractor,
        progress_callback=progress_callback
    )
    
    logger.info(f"✓ : {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description=' PPTX ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
:
  %(prog)s slide1.png slide2.png -o presentation.pptx
  %(prog)s ./slides/ --extractor hybrid --inpaint baidu
  %(prog)s image.png --no-text-styles

:
  - 'generative'  'hybrid'  API
  - '--no-text-styles'  API 
        """
    )
    
    parser.add_argument(
        'images',
        nargs='+',
        help=''
    )
    
    parser.add_argument(
        '-o', '--output',
        default='output_editable.pptx',
        help=' PPTX : output_editable.pptx'
    )
    
    parser.add_argument(
        '--extractor',
        choices=['mineru', 'hybrid'],
        default='hybrid',
        help=': hybrid'
    )
    
    parser.add_argument(
        '--inpaint',
        choices=['generative', 'baidu', 'hybrid'],
        default='hybrid',
        help=': hybridgenerative/hybrid '
    )
    
    parser.add_argument(
        '--no-text-styles',
        action='store_true',
        help=' API '
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help=''
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Config
    image_paths = collect_image_paths(args.images)
    
    if not image_paths:
        logger.error("")
        sys.exit(1)
    
    logger.info(f" {len(image_paths)} :")
    for path in image_paths:
        logger.info(f"  - {path}")
    
    # Config
    app = setup_flask_app()
    
    with app.app_context():
        try:
            export_editable_pptx(
                image_paths=image_paths,
                output_file=args.output,
                extractor_method=args.extractor,
                inpaint_method=args.inpaint,
                extract_text_styles=not args.no_text_styles
            )
        except Exception as e:
            logger.error(f": {e}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    main()
