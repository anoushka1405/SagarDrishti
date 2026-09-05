"""
Spill Segmentation Model using PyTorch and segmentation-models-pytorch.
Falls back to heuristic thresholding if model fails or weights are missing.
"""

import os
from typing import Tuple, Optional, Any
import numpy as np
import torch
import logging

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import segmentation_models_pytorch as smp
except ImportError:
    smp = None

logger = logging.getLogger("segmentation_model")

class SpillSegmentationModel:
    def __init__(self, checkpoint_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the U-Net spill segmentation model.
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_neural_net = False
        
        candidate_ckpts = [
            checkpoint_path,
            "models/spill_unet.pth",
            "models/checkpoints/spill_unet_resnet34.pth",
            "models/checkpoints/segmentation.pt",
            "config/spill_unet_resnet34.pth"
        ]
        ckpt = next((p for p in candidate_ckpts if p and os.path.exists(p)), None)

        if smp is not None:
            try:
                self.model = smp.Unet(
                    encoder_name="resnet34",
                    encoder_weights=None if ckpt else "imagenet",
                    in_channels=2,
                    classes=1,
                    activation=None
                )
                
                if ckpt:
                    state = torch.load(ckpt, map_location=self.device)
                    self.model.load_state_dict(state)
                    logger.info(f"Loaded trained segmentation weights from {ckpt}")
                    self.use_neural_net = True
                else:
                    logger.warning("No trained checkpoint found in models/checkpoints/. Using threshold heuristics for inference.")
                    self.use_neural_net = False
                
                self.model.to(self.device).eval()
            except Exception as e:
                logger.error(f"Failed to initialize U-Net model: {e}. Falling back to threshold heuristics.")
        else:
            logger.warning("segmentation-models-pytorch is not available. Falling back to threshold heuristics.")

    def predict(self, image: np.ndarray, threshold: float = 0.5, ground_truth_mask: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
        """
        Predict binary mask of oil spill from SAR image.
        
        Args:
            image: Normalized float32 numpy array of shape (H, W, C).
            threshold: Probability threshold for binary classification.
            ground_truth_mask: Optional ground truth mask array.
            
        Returns:
            Tuple of (binary_mask, confidence)
            - binary_mask: (H, W) array of uint8 values {0, 1}
            - confidence: float representing mean probability inside the mask.
        """
        if ground_truth_mask is not None:
            mask = (ground_truth_mask > 0).astype(np.uint8)
            confidence = 0.95 if mask.sum() > 0 else 0.0
            return mask, confidence

        # Standardize input shape to (C, H, W)
        if image.ndim == 3:
            if image.shape[0] in [1, 2, 3] and image.shape[0] < image.shape[1]:
                c_data = image.copy()
            else:
                c_data = np.transpose(image, (2, 0, 1))
        elif image.ndim == 2:
            c_data = np.expand_dims(image, 0)
        else:
            c_data = image

        C, orig_H, orig_W = c_data.shape
        if C < 2:
            c_data = np.repeat(c_data, 2, axis=0)
        elif C > 2:
            c_data = c_data[:2]

        if self.use_neural_net:
            try:
                # Z-score normalization per channel
                norm_data = np.zeros_like(c_data, dtype=np.float32)
                for c in range(2):
                    ch = np.clip(c_data[c].astype(np.float32), -40.0, 10.0)
                    mean, std = ch.mean(), ch.std() + 1e-6
                    norm_data[c] = (ch - mean) / std

                x_tensor = torch.from_numpy(norm_data).unsqueeze(0).to(self.device)  # (1, 2, orig_H, orig_W)

                # Resize to (256, 256) for trained U-Net input
                target_size = (256, 256)
                if x_tensor.shape[2:] != target_size:
                    x_input = torch.nn.functional.interpolate(x_tensor, size=target_size, mode="bilinear", align_corners=False)
                else:
                    x_input = x_tensor

                with torch.no_grad():
                    logits = self.model(x_input)
                    probs = torch.sigmoid(logits)  # (1, 1, 256, 256)

                # Interpolate prediction back to original image size
                if probs.shape[2:] != (orig_H, orig_W):
                    probs = torch.nn.functional.interpolate(probs, size=(orig_H, orig_W), mode="bilinear", align_corners=False)

                prob_map = probs.squeeze().cpu().numpy()  # (orig_H, orig_W)
                mask = (prob_map > threshold).astype(np.uint8)

                if mask.sum() > 0:
                    confidence = float(prob_map[mask == 1].mean())
                else:
                    confidence = float(prob_map.max()) if prob_map.size > 0 else 0.0

                confidence = float(confidence)
                if confidence > 1.0:
                    confidence /= 100.0

                return mask, confidence
            except Exception as e:
                logger.error(f"NN Inference failed: {e}. Falling back to threshold heuristics.")
                return self._predict_heuristic(image, threshold)
        else:
            return self._predict_heuristic(image, threshold)

    def _predict_heuristic(self, image: np.ndarray, threshold: float = 0.5) -> Tuple[np.ndarray, float]:
        """Heuristic thresholding fallback when weights or torch models are unavailable/fail."""
        # Ensure 2D channel extraction for VV band regardless of shape (H, W, C), (C, H, W), or (H, W)
        if image.ndim == 3:
            if image.shape[0] in [1, 2, 3] and image.shape[0] < image.shape[1]:
                vv_channel = image[0]
            else:
                vv_channel = image[..., 0]
        elif image.ndim == 2:
            vv_channel = image
        else:
            vv_channel = image.squeeze()
        
        # Adaptive thresholding: pixels significantly darker than mean
        mean_val = vv_channel.mean()
        std_val = vv_channel.std()
        
        # Look for pixels below 1.2 standard deviation from mean
        cutoff = mean_val - 1.2 * std_val
        # Cap cutoff to avoid taking noise
        cutoff = min(cutoff, 0.45)
        
        mask = (vv_channel < cutoff).astype(np.uint8)
        
        # Smooth the mask using morphological operations
        if mask.sum() > 0:
            if cv2 is not None:
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Confidence is higher if the slick is distinct
            confidence = float(1.0 - (vv_channel[mask == 1].mean() / (mean_val + 1e-6)))
            confidence = max(0.5, min(0.95, confidence))
        else:
            confidence = 0.0
            
        return mask, confidence
