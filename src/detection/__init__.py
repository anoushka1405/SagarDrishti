"""
Detection module for SagarDrishti.
Contains preprocessing, segmentation model, lookalike filter, and geometry extractor.
"""
from src.detection.preprocess import preprocess_sar
from src.detection.segmentation_model import SpillSegmentationModel
from src.detection.lookalike_filter import classify_dark_region
from src.detection.spill_geometry import compute_geometry
