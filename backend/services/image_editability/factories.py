"""
 - Inpaint
"""
import logging
from typing import List, Optional, Any
from pathlib import Path

from .extractors import ElementExtractor, MinerUElementExtractor, BaiduOCRElementExtractor, BaiduAccurateOCRElementExtractor, ExtractorRegistry
from .hybrid_extractor import HybridElementExtractor, create_hybrid_extractor
from .inpaint_providers import (
    InpaintProvider, 
    DefaultInpaintProvider, 
    GenerativeEditInpaintProvider, 
    BaiduInpaintProvider,
    HybridInpaintProvider,
    InpaintProviderRegistry
)
from .text_attribute_extractors import (
    TextAttributeExtractor,
    CaptionModelTextAttributeExtractor,
    TextAttributeExtractorRegistry,
    TextStyleResult
)

logger = logging.getLogger(__name__)


class ExtractorFactory:
    """ Backend docstring """
    
    @staticmethod
    def create_default_extractors(
        parser_service: Any,
        upload_folder: Path,
        baidu_table_ocr_provider: Optional[Any] = None
    ) -> List[ElementExtractor]:
        """
        
        
        Args:
            parser_service: MinerU
            upload_folder: 
            baidu_table_ocr_provider: OCR Provider () 
        
        Returns:
             () 
        
        Note:
             create_extractor_registry() , 
        """
        extractors: List[ElementExtractor] = []
        
        # Backend logic
        if baidu_table_ocr_provider is None:
            try:
                from services.ai_providers.ocr import create_baidu_table_ocr_provider
                baidu_provider = create_baidu_table_ocr_provider()
                if baidu_provider:
                    extractors.append(BaiduOCRElementExtractor(baidu_provider))
                    logger.info("✅ bảng BaiduOCRĐã bật bộ trích xuất")
            except Exception as e:
                logger.warning(f"Không thể khởi tạo bảng BaiduOCR: {e}")
        else:
            extractors.append(BaiduOCRElementExtractor(baidu_table_ocr_provider))
            logger.info("✅ Đã bật bộ trích xuất bảng Baidu OCR")
        
        # Backend logic
        mineru_extractor = MinerUElementExtractor(parser_service, upload_folder)
        extractors.append(mineru_extractor)
        logger.info("✅ MinerUĐã bật bộ trích xuất")
        
        return extractors
    
    @staticmethod
    def create_extractor_registry(
        parser_service: Any,
        upload_folder: Path,
        baidu_table_ocr_provider: Optional[Any] = None
    ) -> ExtractorRegistry:
        """
        
        
        : 
        -  (table, table_cell) → OCR () , MinerU
        -  (image, figure, chart) → MinerU
        -  → MinerU () 
        
        Args:
            parser_service: MinerU
            upload_folder: 
            baidu_table_ocr_provider: OCR Provider () 
        
        Returns:
            ExtractorRegistry
        """
        # Backend logic
        mineru_extractor = MinerUElementExtractor(parser_service, upload_folder)
        logger.info("✅ MinerUĐã bật bộ trích xuất")
        
        # Backend logic
        baidu_ocr_extractor = None
        if baidu_table_ocr_provider is None:
            try:
                from services.ai_providers.ocr import create_baidu_table_ocr_provider
                baidu_provider = create_baidu_table_ocr_provider()
                if baidu_provider:
                    baidu_ocr_extractor = BaiduOCRElementExtractor(baidu_provider)
                    logger.info("✅ Đã tạo bộ trích xuất bảng Baidu OCR")
            except Exception as e:
                logger.warning(f"Không thể khởi tạo bảng Baidu OCR: {e}")
        else:
            baidu_ocr_extractor = BaiduOCRElementExtractor(baidu_table_ocr_provider)
            logger.info("✅ Đã tạo bộ trích xuất bảng Baidu OCR")
        
        # Backend logic
        baidu_accurate_ocr_extractor = None
        try:
            from services.ai_providers.ocr import create_baidu_accurate_ocr_provider
            baidu_accurate_provider = create_baidu_accurate_ocr_provider()
            if baidu_accurate_provider:
                baidu_accurate_ocr_extractor = BaiduAccurateOCRElementExtractor(baidu_accurate_provider)
                logger.info("✅ Đã tạo bộ trích xuất Baidu OCR độ chính xác cao")
        except Exception as e:
            logger.warning(f"Không thể khởi tạo Baidu OCR độ chính xác cao: {e}")
        
        # Backend logic
        return ExtractorRegistry.create_default(
            mineru_extractor=mineru_extractor,
            baidu_ocr_extractor=baidu_ocr_extractor,
            baidu_accurate_ocr_extractor=baidu_accurate_ocr_extractor
        )
    
    @staticmethod
    def create_baidu_accurate_ocr_extractor(
        baidu_accurate_ocr_provider: Optional[Any] = None
    ) -> Optional[BaiduAccurateOCRElementExtractor]:
        """
        OCR
        
        Args:
            baidu_accurate_ocr_provider: OCR Provider (, ) 
        
        Returns:
            BaiduAccurateOCRElementExtractor, None
        """
        if baidu_accurate_ocr_provider is None:
            try:
                from services.ai_providers.ocr import create_baidu_accurate_ocr_provider
                baidu_accurate_ocr_provider = create_baidu_accurate_ocr_provider()
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Baidu độ chính xác caoOCR Provider: {e}")
                return None
        
        if baidu_accurate_ocr_provider is None:
            return None
        
        return BaiduAccurateOCRElementExtractor(baidu_accurate_ocr_provider)
    
    @staticmethod
    def create_hybrid_extractor(
        parser_service: Any,
        upload_folder: Path,
        baidu_accurate_ocr_provider: Optional[Any] = None,
        contain_threshold: float = 0.8,
        intersection_threshold: float = 0.3
    ) -> Optional[HybridElementExtractor]:
        """
        
        
        MinerUOCR: 
        - MinerU
        - OCR
        
        : 
        1. bboxOCR bbox →  () 
        2. bboxOCR bbox → OCR, MinerUbbox
        3.  () OCR bbox → OCR, MinerU bbox
        
        Args:
            parser_service: MinerU
            upload_folder: 
            baidu_accurate_ocr_provider: OCR Provider (, ) 
            contain_threshold: , 0.8 (80%) 
            intersection_threshold: , 0.3 (30%) 
        
        Returns:
            HybridElementExtractor, None
        """
        # Backend logic
        mineru_extractor = MinerUElementExtractor(parser_service, upload_folder)
        logger.info("✅ MinerU () ")
        
        # Backend logic
        baidu_ocr_extractor = ExtractorFactory.create_baidu_accurate_ocr_extractor(
            baidu_accurate_ocr_provider
        )
        
        if baidu_ocr_extractor is None:
            logger.warning("Không thể tạo Baidu độ chính xác caoOCRbộ trích xuất, Tạo bộ trích xuất kết hợp thất bại")
            return None
        
        logger.info("✅ OCR () ")
        
        return HybridElementExtractor(
            mineru_extractor=mineru_extractor,
            baidu_ocr_extractor=baidu_ocr_extractor,
            contain_threshold=contain_threshold,
            intersection_threshold=intersection_threshold
        )
    
    @staticmethod
    def create_hybrid_extractor_registry(
        parser_service: Any,
        upload_folder: Path,
        baidu_table_ocr_provider: Optional[Any] = None,
        baidu_accurate_ocr_provider: Optional[Any] = None,
        contain_threshold: float = 0.8,
        intersection_threshold: float = 0.3
    ) -> ExtractorRegistry:
        """
        
        
        : 
        -  →  () 
        - MinerU () 
        
        Args:
            parser_service: MinerU
            upload_folder: 
            baidu_table_ocr_provider: OCR Provider () 
            baidu_accurate_ocr_provider: OCR Provider () 
            contain_threshold: 
            intersection_threshold: 
        
        Returns:
            ExtractorRegistry
        """
        # Backend logic
        mineru_extractor = MinerUElementExtractor(parser_service, upload_folder)
        logger.info("✅ MinerUĐã tạo bộ trích xuất")
        
        # Backend logic
        hybrid_extractor = ExtractorFactory.create_hybrid_extractor(
            parser_service=parser_service,
            upload_folder=upload_folder,
            baidu_accurate_ocr_provider=baidu_accurate_ocr_provider,
            contain_threshold=contain_threshold,
            intersection_threshold=intersection_threshold
        )
        
        # Backend logic
        baidu_table_ocr_extractor = None
        if baidu_table_ocr_provider is None:
            try:
                from services.ai_providers.ocr import create_baidu_table_ocr_provider
                baidu_provider = create_baidu_table_ocr_provider()
                if baidu_provider:
                    from .extractors import BaiduOCRElementExtractor
                    baidu_table_ocr_extractor = BaiduOCRElementExtractor(baidu_provider)
                    logger.info("✅ Đã tạo bộ trích xuất bảng Baidu OCR")
            except Exception as e:
                logger.warning(f"Không thể khởi tạo bảng Baidu OCR: {e}")
        else:
            from .extractors import BaiduOCRElementExtractor
            baidu_table_ocr_extractor = BaiduOCRElementExtractor(baidu_table_ocr_provider)
            logger.info("✅ Đã tạo bộ trích xuất bảng Baidu OCR (dùng cho trích xuất kết hợp)")
        
        # Backend logic
        registry = ExtractorRegistry()
        
        # Backend logic
        if hybrid_extractor:
            registry.register_default(hybrid_extractor)
            logger.info("✅ Sử dụng bộ trích xuất kết hợp làm bộ trích xuất mặc định")
        else:
            registry.register_default(mineru_extractor)
            logger.info("⚠️ Bộ trích xuất kết hợp không khả dụng, chuyển dự phòng sangMinerUbộ trích xuất")
        
        # Backend logic
        if baidu_table_ocr_extractor:
            registry.register_types(list(ExtractorRegistry.TABLE_TYPES), baidu_table_ocr_extractor)
        
        return registry


class InpaintProviderFactory:
    """ Backend docstring """
    
    @staticmethod
    def create_default_provider(inpainting_service: Optional[Any] = None) -> Optional[InpaintProvider]:
        """
        Inpaint (Volcengine Inpainting) 
        
        Args:
            inpainting_service: InpaintingService () 
        
        Returns:
            InpaintProvider, None
        """
        if inpainting_service is None:
            from services.inpainting_service import get_inpainting_service
            inpainting_service = get_inpainting_service()
        
        logger.info("TạoDefaultInpaintProvider")
        return DefaultInpaintProvider(inpainting_service)
    
    @staticmethod
    def create_generative_edit_provider(
        ai_service: Optional[Any] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "2K"
    ) -> InpaintProvider:
        """
        Inpaint
        
         (Gemini) . 
        bbox, . 
        
        Args:
            ai_service: AIService (, ) 
            aspect_ratio: 
            resolution: 
        
        Returns:
            GenerativeEditInpaintProvider
        
        Raises:
            AI, 
        """
        if ai_service is None:
            from services.ai_service_manager import get_ai_service
            ai_service = get_ai_service()
        
        logger.info("TạoGenerativeEditInpaintProvider")
        return GenerativeEditInpaintProvider(ai_service, aspect_ratio, resolution)
    
    @staticmethod
    def create_inpaint_registry(
        mask_provider: Optional[InpaintProvider] = None,
        generative_provider: Optional[InpaintProvider] = None,
        default_provider_type: str = "generative"
    ) -> InpaintProviderRegistry:
        """
        
        
        , . 
        
        Args:
            mask_provider: mask (, ) 
            generative_provider:  (, ) 
            default_provider_type: Loại nhà cung cấp được sử dụng mặc định ("mask" hoặc "generative")
        
        Returns:
            InpaintProviderRegistry
        """
        # Backend logic
        if mask_provider is None:
            mask_provider = InpaintProviderFactory.create_default_provider()
        
        if generative_provider is None:
            generative_provider = InpaintProviderFactory.create_generative_edit_provider()
        
        # Backend logic
        registry = InpaintProviderRegistry()
        
        # Backend logic
        if default_provider_type == "generative" and generative_provider:
            registry.register_default(generative_provider)
        elif mask_provider:
            registry.register_default(mask_provider)
        elif generative_provider:
            registry.register_default(generative_provider)
        
        # Backend logic
        if mask_provider:
            # Backend logic
            registry.register_types(['text', 'title', 'paragraph'], mask_provider)
            registry.register_types(['table', 'table_cell'], mask_provider)
        
        if generative_provider:
            # Backend logic
            registry.register_types(['image', 'figure', 'chart', 'diagram'], generative_provider)
        
        logger.info(f"TạoInpaintProviderRegistry: mặc định={default_provider_type}, "
                   f"mask={mask_provider is not None}, generative={generative_provider is not None}")
        
        return registry
    
    @staticmethod
    def create_baidu_inpaint_provider() -> Optional[BaiduInpaintProvider]:
        """
        
        
        AI. 
        
        Returns:
            BaiduInpaintProvider, None
        """
        try:
            from services.ai_providers.image.baidu_inpainting_provider import create_baidu_inpainting_provider
            baidu_provider = create_baidu_inpainting_provider()
            if baidu_provider:
                logger.info("✅ TạoBaiduInpaintProvider")
                return BaiduInpaintProvider(baidu_provider)
            else:
                logger.warning("⚠️ Không thể tạo bộ phục hồi ảnh BaiduProvider (API Keychưa cấu hình) ")
                return None
        except Exception as e:
            logger.warning(f"⚠️ TạoBaiduInpaintProviderthất bại: {e}")
            return None
    
    @staticmethod
    def create_hybrid_inpaint_provider(
        baidu_provider: Optional[BaiduInpaintProvider] = None,
        generative_provider: Optional[GenerativeEditInpaintProvider] = None,
        ai_service: Optional[Any] = None,
        enhance_quality: bool = True
    ) -> Optional[HybridInpaintProvider]:
        """
        Inpaint ( + ) 
        
        : 
        1. API
        2. 
        
        Args:
            baidu_provider:  (, ) 
            generative_provider:  (, ) 
            ai_service: AI () 
            enhance_quality: , True
        
        Returns:
            HybridInpaintProvider, None
        """
        # Backend logic
        if baidu_provider is None:
            baidu_provider = InpaintProviderFactory.create_baidu_inpaint_provider()
        
        if baidu_provider is None:
            logger.warning("⚠️ Không thể tạo bộ phục hồi ảnh BaiduProvider, kết hợpProviderTạo thất bại")
            return None
        
        # Backend logic
        if generative_provider is None:
            generative_provider = InpaintProviderFactory.create_generative_edit_provider(
                ai_service=ai_service
            )
        
        logger.info("✅ TạoHybridInpaintProvider (Baidu phục hồi + Nâng cấp chất lượng ảnh tạo sinh) ")
        return HybridInpaintProvider(
            baidu_provider=baidu_provider,
            generative_provider=generative_provider,
            enhance_quality=enhance_quality
        )


class ServiceConfig:
    """ Backend docstring """
    
    def __init__(
        self,
        upload_folder: Path,
        extractor_registry: ExtractorRegistry,
        inpaint_registry: InpaintProviderRegistry,
        max_depth: int = 1,
        min_image_size: int = 200,
        min_image_area: int = 40000,
        segmentation_provider: Optional[Any] = None,
        enable_icon_subject_extraction: bool = False,
    ):
        """
        

        Args:
            upload_folder: 
            extractor_registry: 
            inpaint_registry: 
            max_depth:  (1) 
            min_image_size: 
            min_image_area: 
            segmentation_provider:  Provider () , 
            enable_icon_subject_extraction:  ( False,  provider) 
        """
        self.upload_folder = upload_folder
        self.extractor_registry = extractor_registry
        self.inpaint_registry = inpaint_registry
        self.max_depth = max_depth
        self.min_image_size = min_image_size
        self.min_image_area = min_image_area
        self.segmentation_provider = segmentation_provider
        self.enable_icon_subject_extraction = enable_icon_subject_extraction
    
    @classmethod
    def from_defaults(
        cls,
        mineru_token: Optional[str] = None,
        mineru_api_base: Optional[str] = None,
        upload_folder: Optional[str] = None,
        ai_service: Optional[Any] = None,
        use_hybrid_extractor: bool = True,
        use_hybrid_inpaint: bool = True,
        extractor_method: Optional[str] = None,  # Backend logic
        inpaint_method: Optional[str] = None,    # Backend logic
        **kwargs
    ) -> 'ServiceConfig':
        """
        
        
         (PPTX) : 
        - :  (MinerU + OCR) 
        - : Inpaint ( + ) 
        - : 1
        
        : 
        1. bboxOCR bbox → 
        2. bboxOCR bbox → OCR, MinerUbbox
        3. OCR bbox → OCR
        
        Inpaint: 
        1. 
        2. 
        
        /. 
        
        ,  Flask app.config . 
        
        Args:
            mineru_token: MinerU API token (,  Flask config ) 
            mineru_api_base: MinerU API base URL (,  Flask config ) 
            upload_folder:  (,  Flask config ) 
            ai_service: AI (, ) 
            use_hybrid_extractor:  (True,  extractor_method ) 
            use_hybrid_inpaint: Inpaint (True,  inpaint_method ) 
            extractor_method: Phương pháp trích xuất thành phần, 'mineru' hoặc 'hybrid' (ưu tiên hơn use_hybrid_extractor) 
            inpaint_method: Phương pháp phục hồi nền, 'generative', 'baidu', 'hybrid' (ưu tiên hơn use_hybrid_inpaint) 
            **kwargs: 
                - max_depth:  (1) 
                - min_image_size:  (200) 
                - min_image_area:  (40000) 
                - contain_threshold:  (0.8) 
                - intersection_threshold:  (0.3) 
                - enhance_quality: Inpaint (True) 
        
        Returns:
            ServiceConfig
        
        Raises:
            ValueError:  mineru_token 
        """
        # Backend logic
        if extractor_method is not None:
            use_hybrid_extractor = (extractor_method == 'hybrid')
            logger.info(f"extractor_method={extractor_method} -> use_hybrid_extractor={use_hybrid_extractor}")
        # Backend logic
        from flask import current_app, has_app_context
        
        if has_app_context() and current_app:
            if mineru_token is None:
                mineru_token = current_app.config.get('MINERU_TOKEN')
            if mineru_api_base is None:
                mineru_api_base = current_app.config.get('MINERU_API_BASE', 'https://mineru.net')
            if upload_folder is None:
                upload_folder = current_app.config.get('UPLOAD_FOLDER', './uploads')
        else:
            # Backend logic
            if mineru_api_base is None:
                mineru_api_base = 'https://mineru.net'
            if upload_folder is None:
                upload_folder = './uploads'
        
        # Backend logic
        if not mineru_token:
            raise ValueError("MinerU token is required. Please configure MINERU_TOKEN.")
        
        from services.file_parser_service import FileParserService
        
        # Backend logic
        upload_path = Path(upload_folder)
        if not upload_path.is_absolute():
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent
            project_root = backend_dir.parent
            upload_path = project_root / upload_folder.lstrip('./')
        
        logger.info(f"Upload folder resolved to: {upload_path}")
        
        # Backend logic
        parser_service = FileParserService(
            mineru_token=mineru_token,
            mineru_api_base=mineru_api_base
        )
        
        # Backend logic
        extractor_registry = ExtractorRegistry()
        
        if use_hybrid_extractor:
            # Backend logic
            hybrid_extractor = ExtractorFactory.create_hybrid_extractor(
                parser_service=parser_service,
                upload_folder=upload_path,
                contain_threshold=kwargs.get('contain_threshold', 0.8),
                intersection_threshold=kwargs.get('intersection_threshold', 0.3)
            )
            
            if hybrid_extractor:
                extractor_registry.register_default(hybrid_extractor)
                logger.info("✅ Đã tạo bộ trích xuất kết hợp (MinerU + Baidu độ chính xác caoOCR) ")
            else:
                # Backend logic
                mineru_extractor = MinerUElementExtractor(parser_service, upload_path)
                extractor_registry.register_default(mineru_extractor)
                logger.warning("⚠️ Tạo bộ trích xuất kết hợp thất bại, chuyển dự phòng sangMinerUbộ trích xuất")
        else:
            # Backend logic
            mineru_extractor = MinerUElementExtractor(parser_service, upload_path)
            extractor_registry.register_default(mineru_extractor)
            logger.info("✅ MinerU () ")
        
        # Backend logic
        inpaint_registry = InpaintProviderRegistry()
        
        # Backend logic
        effective_inpaint_method = inpaint_method
        if effective_inpaint_method is None:
            # Backend logic
            effective_inpaint_method = 'hybrid' if use_hybrid_inpaint else 'generative'
        
        logger.info(f"inpaint_method={effective_inpaint_method}")
        
        if effective_inpaint_method == 'hybrid':
            # Backend logic
            hybrid_inpaint = InpaintProviderFactory.create_hybrid_inpaint_provider(
                ai_service=ai_service,
                enhance_quality=kwargs.get('enhance_quality', True)
            )
            
            if hybrid_inpaint:
                inpaint_registry.register_default(hybrid_inpaint)
                logger.info("✅ kết hợpInpaintĐã tạo nhà cung cấp (Baidu phục hồi + Nâng cấp chất lượng ảnh tạo sinh) ")
            else:
                # Backend logic
                generative_provider = InpaintProviderFactory.create_generative_edit_provider(
                    ai_service=ai_service
                )
                inpaint_registry.register_default(generative_provider)
                logger.warning("⚠️ kết hợpInpaintTạo thất bại, chuyển dự phòng sangGenerativeEdit")
        
        elif effective_inpaint_method == 'baidu':
            # Backend logic
            baidu_inpaint = InpaintProviderFactory.create_baidu_inpaint_provider()
            
            if baidu_inpaint:
                inpaint_registry.register_default(baidu_inpaint)
                logger.info("✅ BaiduInpaintĐã tạo nhà cung cấp (phục hồi thuần Baidu) ")
            else:
                # Backend logic
                generative_provider = InpaintProviderFactory.create_generative_edit_provider(
                    ai_service=ai_service
                )
                inpaint_registry.register_default(generative_provider)
                logger.warning("⚠️ kết hợpInpaintTạo thất bại, chuyển dự phòng sangGenerativeEdit")
        
        else:  # Backend logic
            # Backend logic
            generative_provider = InpaintProviderFactory.create_generative_edit_provider(
                ai_service=ai_service
            )
            inpaint_registry.register_default(generative_provider)
            logger.info("✅ Đã tạo bảng đăng ký vẽ lại (GenerativeEditChung) ")
        
        # Backend logic
        enable_icon_subject_extraction = kwargs.get('enable_icon_subject_extraction', False)
        segmentation_provider = None
        if enable_icon_subject_extraction:
            try:
                from services.ai_providers.image import create_rmbg_segmentation_provider
                segmentation_provider = create_rmbg_segmentation_provider()
                logger.info("✅ RMBG-2.0 Tách nền chủ thể Provider đã tạo (dùng cho nền trong suốt của biểu tượng) ")
            except Exception as e:
                logger.warning(f"Tạo tách nền chủ thể Provider thất bại: {e}")

        return cls(
            upload_folder=upload_path,
            extractor_registry=extractor_registry,
            inpaint_registry=inpaint_registry,
            max_depth=kwargs.get('max_depth', 1),
            min_image_size=kwargs.get('min_image_size', 200),
            min_image_area=kwargs.get('min_image_area', 40000),
            segmentation_provider=segmentation_provider,
            enable_icon_subject_extraction=enable_icon_subject_extraction and segmentation_provider is not None,
        )


class TextAttributeExtractorFactory:
    """ Backend docstring """
    
    @staticmethod
    def create_caption_model_extractor(
        ai_service: Optional[Any] = None,
        prompt_template: Optional[str] = None
    ) -> TextAttributeExtractor:
        """
        Caption Model
        
         (Gemini) , 
        JSON, , . 
        
        Args:
            ai_service: AIService (, ) 
            prompt_template: prompt () ,  {content_hint} 
        
        Returns:
            CaptionModelTextAttributeExtractor
        
        Raises:
            AI, 
        """
        if ai_service is None:
            from services.ai_service_manager import get_ai_service
            ai_service = get_ai_service()
        
        logger.info("TạoCaptionModelTextAttributeExtractor")
        return CaptionModelTextAttributeExtractor(ai_service, prompt_template)
    
    @staticmethod
    def create_text_attribute_registry(
        caption_extractor: Optional[TextAttributeExtractor] = None,
        ai_service: Optional[Any] = None
    ) -> TextAttributeExtractorRegistry:
        """
        
        
        , . 
        
        Args:
            caption_extractor: Caption Model (, ) 
            ai_service: AIService (, ) 
        
        Returns:
            TextAttributeExtractorRegistry
        
        Raises:
            , 
        """
        # Backend logic
        if caption_extractor is None:
            caption_extractor = TextAttributeExtractorFactory.create_caption_model_extractor(
                ai_service=ai_service
            )
        
        # Backend logic
        registry = TextAttributeExtractorRegistry()
        
        # Backend logic
        registry.register_default(caption_extractor)
        
        # Backend logic
        registry.register_types(
            ['text', 'title', 'paragraph', 'heading', 'table_cell'],
            caption_extractor
        )
        
        logger.info("TạoTextAttributeExtractorRegistry")
        
        return registry