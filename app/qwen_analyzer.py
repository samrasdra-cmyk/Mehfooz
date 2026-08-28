"""
Image analysis module.

Real mode (QWEN_ENABLED=true): loads Qwen2-VL via transformers and asks it
to describe the scene, then still runs the pixel-based water measurement
below for the actual area number.

Mock/default mode: skips the VL model and estimates lake area directly from
pixel color (a simple water-index-style threshold), which is more reliable
for a quantitative metric than asking a vision-language model to guess a
number from a picture. Channel/snowmelt flags are heuristic in this mode.

NOTE ON DESIGN: Vision-language models are good at *describing* a scene in
natural language but are not a trustworthy source for precise measurements
like area in km^2 -- they tend to produce plausible-looking numbers that
aren't grounded in the actual pixel geometry. For a real deployment, area
and channel detection should come from a proper index (e.g. NDWI on
Sentinel-2 bands) or a trained segmentation model, with the VL model used
only for narrative description / anomaly flagging. This module is
structured so you can swap `_estimate_from_pixels` for a real NDWI pipeline
without touching the rest of the app.
"""
import json
import re
from PIL import Image
import numpy as np

from app.config import QWEN_ENABLED, QWEN_MODEL_NAME

_model = None
_processor = None


def _load_model():
    global _model, _processor
    if _model is None:
        from transformers import AutoModelForCausalLM, AutoProcessor

        _processor = AutoProcessor.from_pretrained(QWEN_MODEL_NAME, trust_remote_code=True)
        _model = AutoModelForCausalLM.from_pretrained(
            QWEN_MODEL_NAME, device_map="auto", trust_remote_code=True
        )
    return _model, _processor


def analyze_image(image_path: str, pixel_km2_per_pixel: float = 0.0004) -> dict:
    """
    Returns a dict:
      {
        "lake_area_km2": float,
        "new_channels": bool,
        "snowmelt_acceleration": "low" | "medium" | "high",
        "description": str,
        "source": "qwen-vl" | "pixel-heuristic"
      }
    """
    pixel_result = _estimate_from_pixels(image_path, pixel_km2_per_pixel)

    if QWEN_ENABLED:
        try:
            description = _describe_with_qwen(image_path)
            pixel_result["description"] = description
            pixel_result["source"] = "qwen-vl+pixel-heuristic"
        except Exception as e:
            pixel_result["description"] = f"(Qwen-VL unavailable: {e})"
    else:
        pixel_result["description"] = (
            "Qwen-VL disabled (QWEN_ENABLED=false); using pixel-based water "
            "detection only. Enable QWEN_ENABLED and provide GPU resources "
            "for natural-language scene description."
        )

    return pixel_result


def _estimate_from_pixels(image_path: str, km2_per_pixel: float) -> dict:
    """Rough water-body detection via a blue-dominant color threshold.

    This stands in for a real NDWI computation (which needs the actual
    Sentinel-2 B03/B08 bands, not an RGB PNG). Swap this out for real
    band math when wiring up Sentinel Hub for production.
    """
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img).astype(int)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    water_mask = (b > r + 20) & (b > g + 10)
    water_pixels = int(water_mask.sum())
    lake_area_km2 = round(water_pixels * km2_per_pixel, 3)

    # crude channel heuristic: elongated thin water regions touching the main blob
    # (real implementation: connected-component + shape analysis)
    edge_water = water_mask[:, -60:].sum() if water_mask.shape[1] > 60 else 0
    new_channels = bool(edge_water > 50)

    # placeholder snowmelt heuristic: brightness of non-water terrain
    terrain_mask = ~water_mask
    if terrain_mask.sum() > 0:
        brightness = arr[terrain_mask].mean()
    else:
        brightness = 0
    if brightness > 140:
        snowmelt = "high"
    elif brightness > 100:
        snowmelt = "medium"
    else:
        snowmelt = "low"

    return {
        "lake_area_km2": lake_area_km2,
        "new_channels": new_channels,
        "snowmelt_acceleration": snowmelt,
        "source": "pixel-heuristic",
    }


def _describe_with_qwen(image_path: str) -> str:
    model, processor = _load_model()
    image = Image.open(image_path)
    prompt = (
        "Describe this satellite image of a glacial lake region in 2-3 "
        "sentences, noting anything unusual about water extent, channels, "
        "or surrounding terrain."
    )
    inputs = processor(text=prompt, images=image, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=150)
    return processor.decode(outputs[0], skip_special_tokens=True)
