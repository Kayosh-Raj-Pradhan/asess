"""
Image Quality Grading & Eye Region Detection Service
=====================================================
Pipeline:
  [1] Image Quality Grader  – checks blur, brightness, glare, contrast
  [2] Eye Region Detector   – validates the image contains an eye and crops ROI
  [3] Disease Classifier    – (existing model in ml_service.py)

Uses only PIL + numpy + torch/torchvision (already in requirements).
"""

import numpy as np
from PIL import Image, ImageFilter, ImageStat
import io
from dataclasses import dataclass, field
from typing import Tuple, Optional, List


@dataclass
class QualityReport:
    """Result of the image-quality + eye-detection pipeline."""
    passed: bool = True
    is_eye_image: bool = True
    issues: List[str] = field(default_factory=list)
    quality_score: float = 100.0       # 0-100
    brightness: float = 0.0
    contrast: float = 0.0
    sharpness: float = 0.0
    cropped_image: Optional[Image.Image] = None   # ROI after eye detection

    def to_dict(self):
        return {
            "passed": self.passed,
            "is_eye_image": self.is_eye_image,
            "issues": self.issues,
            "quality_score": round(self.quality_score, 1),
            "brightness": round(self.brightness, 1),
            "contrast": round(self.contrast, 1),
            "sharpness": round(self.sharpness, 1),
        }


# ─────────────── Thresholds (tuneable) ───────────────
BRIGHTNESS_LOW   = 45      # below → "Too dark"
BRIGHTNESS_HIGH  = 215     # above → "Too bright"
CONTRAST_LOW     = 25      # below → "Low contrast"
SHARPNESS_LOW    = 30      # below → "Blurry image"
GLARE_RATIO      = 0.18    # if >18% pixels near-white → "Glare detected"
MIN_EYE_COLOR_RATIO = 0.008  # minimum ratio of eye-like colours


# ─────────────── 1. Quality Grading ───────────────
def _measure_brightness(img: Image.Image) -> float:
    """Mean luminance (0-255)."""
    gray = img.convert("L")
    stat = ImageStat.Stat(gray)
    return stat.mean[0]


def _measure_contrast(img: Image.Image) -> float:
    """Standard deviation of luminance."""
    gray = img.convert("L")
    stat = ImageStat.Stat(gray)
    return stat.stddev[0]


def _measure_sharpness(img: Image.Image) -> float:
    """Variance of Laplacian-like filter (higher = sharper)."""
    gray = img.convert("L")
    # Approximate Laplacian via edge-detect kernel
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return stat.stddev[0]


def _measure_glare(img: Image.Image) -> float:
    """Fraction of near-white (>240) pixels."""
    gray = np.array(img.convert("L"))
    total = gray.size
    bright_pixels = np.sum(gray > 240)
    return bright_pixels / total if total > 0 else 0


def grade_quality(img: Image.Image) -> QualityReport:
    """
    Step 1: Grade image quality.
    Returns a QualityReport with issues list.
    """
    report = QualityReport()

    # Resize for speed
    thumb = img.copy()
    thumb.thumbnail((512, 512))

    report.brightness = _measure_brightness(thumb)
    report.contrast   = _measure_contrast(thumb)
    report.sharpness  = _measure_sharpness(thumb)
    glare_ratio       = _measure_glare(thumb)

    penalties = 0

    if report.brightness < BRIGHTNESS_LOW:
        report.issues.append("Too dark – insufficient lighting")
        penalties += 25

    if report.brightness > BRIGHTNESS_HIGH:
        report.issues.append("Too bright – image overexposed")
        penalties += 25

    if report.contrast < CONTRAST_LOW:
        report.issues.append("Low contrast – image appears washed out")
        penalties += 20

    if report.sharpness < SHARPNESS_LOW:
        report.issues.append("Blurry – image is not sharp enough")
        penalties += 25

    if glare_ratio > GLARE_RATIO:
        report.issues.append("Glare detected – bright reflections visible")
        penalties += 20

    report.quality_score = max(0, 100 - penalties)

    if len(report.issues) > 0:
        report.passed = False

    return report


# ─────────────── 2. Eye Region Detection ───────────────
def _has_eye_heuristics(img: Image.Image) -> Tuple[bool, Optional[Tuple[int, int, int, int]]]:
    """
    Heuristic eye-region detector using colour analysis.
    Looks for:
      - Reddish/pink tones (conjunctiva, blood vessels)
      - Sclera-white regions bordered by darker iris/pupil
      - Circular-ish warm-toned blob surrounded by skin tones

    Returns (is_eye, bounding_box_or_None).
    The bounding box is (left, upper, right, lower).
    """
    rgb = np.array(img.convert("RGB"))
    h, w = rgb.shape[:2]

    r, g, b = rgb[:,:,0].astype(float), rgb[:,:,1].astype(float), rgb[:,:,2].astype(float)

    # === Sclera detection: bright, low-saturation pixels ===
    brightness = (r + g + b) / 3.0
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    saturation = np.where(max_c > 0, (max_c - min_c) / max_c, 0)

    sclera_mask = (brightness > 160) & (saturation < 0.20)
    sclera_ratio = np.sum(sclera_mask) / sclera_mask.size

    # === Dark region detection: iris/pupil ===
    dark_mask = brightness < 60
    dark_ratio = np.sum(dark_mask) / dark_mask.size

    # === Reddish/pinkish tones (conjunctiva, veins) ===
    reddish_mask = (r > g + 15) & (r > b + 15) & (r > 80)
    reddish_ratio = np.sum(reddish_mask) / reddish_mask.size

    # === Brownish tones (iris for brown-eyed people) ===
    brownish_mask = (r > 80) & (g > 40) & (b < g) & (r > g) & ((r - b) > 20)
    brownish_ratio = np.sum(brownish_mask) / brownish_mask.size

    # === Skin tone detection (should be present around eye) ===
    skin_mask = (r > 95) & (g > 40) & (b > 20) & \
                (np.abs(r - g) > 15) & (r > g) & (r > b)
    skin_ratio = np.sum(skin_mask) / skin_mask.size

    # === Combined eye-likeness score ===
    eye_score = 0.0

    # Sclera presence (white of the eye)
    if 0.02 < sclera_ratio < 0.65:
        eye_score += 2.0

    # Dark pupil/iris region
    if 0.01 < dark_ratio < 0.40:
        eye_score += 1.5

    # Reddish tones (blood vessels, conjunctiva)
    if reddish_ratio > MIN_EYE_COLOR_RATIO:
        eye_score += 1.5

    # Brownish iris tones
    if brownish_ratio > 0.01:
        eye_score += 1.0

    # Skin around the eye
    if 0.05 < skin_ratio < 0.70:
        eye_score += 1.0

    # Combination: sclera + dark = very likely an eye
    if sclera_ratio > 0.03 and dark_ratio > 0.015:
        eye_score += 1.5

    is_eye = eye_score >= 3.0

    # Find bounding box of the eye region (combined interest mask)
    if is_eye:
        interest = sclera_mask | dark_mask | reddish_mask | brownish_mask
        rows = np.any(interest, axis=1)
        cols = np.any(interest, axis=0)
        if np.any(rows) and np.any(cols):
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            # Add padding (15%)
            pad_h = int((rmax - rmin) * 0.15)
            pad_w = int((cmax - cmin) * 0.15)
            rmin = max(0, rmin - pad_h)
            rmax = min(h, rmax + pad_h)
            cmin = max(0, cmin - pad_w)
            cmax = min(w, cmax + pad_w)
            return True, (cmin, rmin, cmax, rmax)

    return is_eye, None


def detect_eye_region(img: Image.Image) -> Tuple[bool, Optional[Image.Image]]:
    """
    Step 2: Eye region detection and ROI cropping.
    Returns (is_eye, cropped_eye_image_or_None).
    """
    # Work on a downsized copy for speed
    analysis_img = img.copy()
    analysis_img.thumbnail((640, 640))

    is_eye, bbox = _has_eye_heuristics(analysis_img)

    if not is_eye:
        return False, None

    if bbox:
        # Scale bbox back to original image dimensions
        scale_x = img.width / analysis_img.width
        scale_y = img.height / analysis_img.height
        orig_bbox = (
            int(bbox[0] * scale_x),
            int(bbox[1] * scale_y),
            int(bbox[2] * scale_x),
            int(bbox[3] * scale_y),
        )
        cropped = img.crop(orig_bbox)
        # Only crop if bounding box is meaningfully smaller than original
        crop_area = (orig_bbox[2] - orig_bbox[0]) * (orig_bbox[3] - orig_bbox[1])
        orig_area = img.width * img.height
        if crop_area < orig_area * 0.85:
            return True, cropped

    return True, img   # eye detected but ROI ≈ full image, return as-is


# ─────────────── Full Pipeline ───────────────
def run_preprocess_pipeline(image_bytes: bytes) -> QualityReport:
    """
    Full pre-processing pipeline:
      1. Grade image quality
      2. Detect eye region
    Returns a QualityReport.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Step 1: Quality grading
    report = grade_quality(img)

    # Step 2: Eye region detection (even if quality failed, still check)
    is_eye, cropped = detect_eye_region(img)

    if not is_eye:
        report.is_eye_image = False
        report.passed = False
        report.issues.append("No eye detected – this does not appear to be an eye image")
        report.quality_score = max(0, report.quality_score - 30)
    else:
        report.cropped_image = cropped

    return report
