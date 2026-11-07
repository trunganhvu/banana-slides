"""RMBG-2.0 ONNX  provider. 

: AI-ModelScope/RMBG-2.0 (FP16 ONNX mirror), CPU . 
 ~/.cache/banana-slides/models/rmbg-2.0/model_fp16.onnx, 
 RMBG_MODEL_PATH . 

:  non-commercial license, . 
"""
import logging
import os
import threading
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

_MODEL_URL = "https://modelscope.cn/models/AI-ModelScope/RMBG-2.0/resolve/master/onnx/model_fp16.onnx"
_DEFAULT_MODEL_PATH = Path.home() / ".cache" / "banana-slides" / "models" / "rmbg-2.0" / "model_fp16.onnx"
_INPUT_SIZE = 1024
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def _resolve_model_path() -> Path:
    """ Backend docstring """
    env_path = os.environ.get("RMBG_MODEL_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return _DEFAULT_MODEL_PATH


def _download_model(target: Path) -> None:
    """ Backend docstring """
    import requests

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    logger.info(f"📥 Bắt đầu tải xuống RMBG-2.0 mô hình (~512MB) đến {target} ...")

    chunk_size = 1024 * 1024
    log_step = 5 * 1024 * 1024
    downloaded = 0
    next_log = log_step

    with requests.get(_MODEL_URL, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded >= next_log:
                    if total:
                        pct = downloaded * 100 / total
                        logger.info(f" Tiến độ tải xuống: {downloaded // (1024*1024)}MB / {total // (1024*1024)}MB ({pct:.1f}%)")
                    else:
                        logger.info(f" Tiến độ tải xuống: {downloaded // (1024*1024)}MB")
                    next_log += log_step

    tmp.rename(target)
    logger.info(f"✅ RMBG-2.0 Mô hình đã sẵn sàng: {target}")


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _decontaminate_foreground(
    rgb: np.ndarray,
    alpha: np.ndarray,
    bg_alpha_threshold: float = 0.05,
    fg_alpha_floor: float = 0.1,
) -> np.ndarray:
    """ alpha ,  RGB. 

    -  alpha < bg_alpha_threshold  B
    -  F = (C - (1-α)·B) / α, alpha  (< fg_alpha_floor) 
      
    -  () 
    """
    bg_mask = alpha < bg_alpha_threshold
    if bg_mask.sum() < 100:
        return rgb

    bg_color = rgb[bg_mask].mean(axis=0)
    a = np.clip(alpha[..., None], fg_alpha_floor, 1.0)
    fg = (rgb - (1.0 - a) * bg_color) / a
    fg = np.clip(fg, 0.0, 255.0)
    return np.where(alpha[..., None] >= bg_alpha_threshold, fg, rgb)


class RmbgSegmentationProvider:
    """ Backend docstring """

    def __init__(self, model_path: Optional[Path] = None):
        self._model_path = model_path or _resolve_model_path()
        self._session = None
        self._input_name: Optional[str] = None
        self._init_lock = threading.Lock()

    def _ensure_session(self) -> None:
        if self._session is not None:
            return
        with self._init_lock:
            if self._session is not None:
                return
            if not self._model_path.exists():
                _download_model(self._model_path)

            import onnxruntime as ort

            logger.info(f"🧠 Tải RMBG-2.0 ONNX mô hình: {self._model_path}")
            self._session = ort.InferenceSession(
                str(self._model_path), providers=["CPUExecutionProvider"]
            )
            self._input_name = self._session.get_inputs()[0].name

    def extract_subject(self, image: Image.Image) -> Optional[Image.Image]:
        """ Backend docstring """
        try:
            self._ensure_session()
            rgb = image.convert("RGB")
            orig_size = rgb.size  # (w, h)
            resized = rgb.resize((_INPUT_SIZE, _INPUT_SIZE), Image.LANCZOS)

            arr = np.asarray(resized, dtype=np.float32) / 255.0
            arr = (arr - _MEAN) / _STD
            tensor = arr.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)

            outputs = self._session.run(None, {self._input_name: tensor})
            mask = outputs[-1] if isinstance(outputs, (list, tuple)) else outputs

            mask = np.asarray(mask, dtype=np.float32)
            mask = np.squeeze(mask)
            if mask.ndim != 2:
                logger.warning(f"RMBG đầu ra shape bất thường: {mask.shape}, bỏ qua")
                return None

            # Backend logic
            # Backend logic
            if mask.min() < -0.5 or mask.max() > 1.5:
                mask = _sigmoid(mask)

            mask = np.clip(mask, 0.0, 1.0)
            mask_uint8 = (mask * 255.0).astype(np.uint8)
            mask_pil = Image.fromarray(mask_uint8, mode="L").resize(orig_size, Image.BILINEAR)
            alpha_full = np.asarray(mask_pil, dtype=np.float32) / 255.0

            # Backend logic
            # Backend logic
            rgb_decont = _decontaminate_foreground(np.asarray(rgb, dtype=np.float32), alpha_full)

            # Backend logic
            alpha_full = np.where(alpha_full < 0.05, 0.0, alpha_full)
            alpha_uint8 = np.clip(alpha_full * 255.0, 0, 255).astype(np.uint8)

            rgba = np.dstack([rgb_decont.astype(np.uint8), alpha_uint8])
            return Image.fromarray(rgba, mode="RGBA")
        except Exception as e:
            logger.warning(f"RMBG tách nền thất bại: {e}")
            return None


_singleton_lock = threading.Lock()
_singleton: Optional[RmbgSegmentationProvider] = None


def create_rmbg_segmentation_provider() -> RmbgSegmentationProvider:
    """ Backend docstring """
    global _singleton
    if _singleton is not None:
        return _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = RmbgSegmentationProvider()
    return _singleton