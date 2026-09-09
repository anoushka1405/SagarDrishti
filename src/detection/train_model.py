"""
PyTorch Training Script for SagarDrishti Oil Spill U-Net Segmentation Model.
Trains a ResNet-34 U-Net model on Sentinel-1 SAR dataset (450 samples: Oil, Lookalike, No oil).
Saves trained weights to config/spill_unet_resnet34.pth.
"""

import os
import sys
import glob
import math
import random
import logging
from typing import Tuple, List, Dict, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import rasterio

# Ensure workspace root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import segmentation_models_pytorch as smp
except ImportError:
    smp = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_model")

# Set random seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

class SARDataset(Dataset):
    def __init__(self, image_paths: List[str], target_size: Tuple[int, int] = (256, 256)):
        self.image_paths = image_paths
        self.target_size = target_size

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        img_path = self.image_paths[idx]
        
        # Load 2-channel SAR raster (VV, VH)
        with rasterio.open(img_path) as src:
            bands = src.read()  # (C, H, W)
            if bands.shape[0] < 2:
                bands = np.repeat(bands, 2, axis=0)
            elif bands.shape[0] > 2:
                bands = bands[:2]
                
        # Z-score normalize per channel
        normalized_bands = np.zeros_like(bands, dtype=np.float32)
        for c in range(bands.shape[0]):
            b = bands[c].astype(np.float32)
            b = np.clip(b, -40.0, 10.0)
            mean_val, std_val = b.mean(), b.std() + 1e-6
            normalized_bands[c] = (b - mean_val) / std_val

        # Load corresponding ground truth mask
        mask = np.zeros((bands.shape[1], bands.shape[2]), dtype=np.float32)
        norm_path = os.path.normpath(img_path)
        parts = norm_path.split(os.sep)
        if "Images" in parts:
            idx_part = parts.index("Images")
            parts[idx_part] = "Mask"
            filename = parts[-1]
            name_part, ext_part = os.path.splitext(filename)
            parts[-1] = f"{name_part}_segmentation{ext_part}"
            mask_path = os.sep.join(parts)
            
            if os.path.exists(mask_path):
                with rasterio.open(mask_path) as msrc:
                    m_arr = msrc.read(1)
                    mask = (m_arr > 0).astype(np.float32)

        # Convert to Tensors and resize to target_size
        img_tensor = torch.from_numpy(normalized_bands).float()  # (2, H, W)
        mask_tensor = torch.from_numpy(mask).unsqueeze(0).float() # (1, H, W)

        # Interpolate to target size
        if img_tensor.shape[1:] != self.target_size:
            img_tensor = torch.nn.functional.interpolate(
                img_tensor.unsqueeze(0), size=self.target_size, mode="bilinear", align_corners=False
            ).squeeze(0)
            mask_tensor = torch.nn.functional.interpolate(
                mask_tensor.unsqueeze(0), size=self.target_size, mode="nearest"
            ).squeeze(0)

        return img_tensor, mask_tensor

class DiceBCELoss(nn.Module):
    def __init__(self, weight_bce=0.5, weight_dice=0.5):
        super(DiceBCELoss, self).__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.weight_bce = weight_bce
        self.weight_dice = weight_dice

    def forward(self, inputs, targets):
        bce_loss = self.bce(inputs, targets)
        
        probs = torch.sigmoid(inputs)
        smooth = 1.0
        
        inputs_flat = probs.view(-1)
        targets_flat = targets.view(-1)
        
        intersection = (inputs_flat * targets_flat).sum()
        dice_loss = 1.0 - (2.0 * intersection + smooth) / (inputs_flat.sum() + targets_flat.sum() + smooth)
        
        return self.weight_bce * bce_loss + self.weight_dice * dice_loss


class FocalLoss(nn.Module):
    def __init__(self, alpha=0.75, gamma=2.0):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets):
        bce = nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction="none")
        probs = torch.sigmoid(inputs)
        pt = torch.where(targets == 1, probs, 1 - probs)
        focal_weight = self.alpha * (1 - pt) ** self.gamma
        return (focal_weight * bce).mean()


class CombinedLoss(nn.Module):
    """Weighted combination: 0.4 * Focal + 0.35 * Dice + 0.25 * BCE."""
    def __init__(self):
        super(CombinedLoss, self).__init__()
        self.focal = FocalLoss(alpha=0.75, gamma=2.0)
        self.dice_bce = DiceBCELoss(weight_bce=0.5, weight_dice=0.5)

    def forward(self, inputs, targets):
        focal_loss = self.focal(inputs, targets)
        dice_bce_loss = self.dice_bce(inputs, targets)
        return 0.4 * focal_loss + 0.6 * dice_bce_loss

def calculate_metrics(preds_binary: np.ndarray, targets_binary: np.ndarray) -> Dict[str, float]:
    """Calculate IoU, Dice, Precision, Recall."""
    intersection = np.logical_and(preds_binary, targets_binary).sum()
    union = np.logical_or(preds_binary, targets_binary).sum()
    iou = float(intersection / (union + 1e-6))
    
    dice = float((2.0 * intersection) / (preds_binary.sum() + targets_binary.sum() + 1e-6))
    precision = float(intersection / (preds_binary.sum() + 1e-6))
    recall = float(intersection / (targets_binary.sum() + 1e-6))
    
    return {
        "iou": round(iou, 4),
        "dice": round(dice, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4)
    }

def train_spill_model(
    data_dir: str = "data/raw/SARSatelite",
    output_checkpoint: str = "models/checkpoints/spill_unet_resnet34.pth",
    epochs: int = 15,
    batch_size: int = 4,
    lr: float = 1e-3,
    target_size: Tuple[int, int] = (256, 256)
):
    if smp is None:
        logger.error("segmentation-models-pytorch is required for training.")
        return

    # Collect all image file paths across Oil, Lookalike, No oil
    all_images = []
    for cat in ["Oil", "Lookalike", "No oil"]:
        cat_dir = os.path.join(data_dir, "Images", cat)
        if os.path.exists(cat_dir):
            files = sorted(glob.glob(os.path.join(cat_dir, "*.tif")))
            all_images.extend(files)

    logger.info(f"Total dataset samples found: {len(all_images)}")
    if not all_images:
        logger.error(f"No satellite images found in {data_dir}")
        return

    # Shuffle & Split dataset: 70% Train, 15% Val, 15% Test
    random.shuffle(all_images)
    n_total = len(all_images)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)
    
    train_paths = all_images[:n_train]
    val_paths = all_images[n_train:n_train + n_val]
    test_paths = all_images[n_train + n_val:]
    
    logger.info(f"Dataset Split -> Train: {len(train_paths)} | Val: {len(val_paths)} | Test: {len(test_paths)}")

    train_ds = SARDataset(train_paths, target_size=target_size)
    val_ds = SARDataset(val_paths, target_size=target_size)
    test_ds = SARDataset(test_paths, target_size=target_size)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    # Initialize U-Net model with ResNet34 encoder
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Initializing U-Net (ResNet-34) model on device: {device}")
    
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=2,
        classes=1,
        activation=None
    ).to(device)

    criterion = CombinedLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    best_val_loss = float("inf")
    os.makedirs(os.path.dirname(output_checkpoint), exist_ok=True)

    # Training Loop
    logger.info("Starting PyTorch U-Net training loop with Focal+Dice+BCE Loss & LR Scheduler...")
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for imgs, masks in train_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, masks)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
            
        train_loss /= len(train_ds)

        # Validation Loop
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                logits = model(imgs)
                loss = criterion(logits, masks)
                val_loss += loss.item() * imgs.size(0)
                
        val_loss /= len(val_ds)

        # Step the scheduler
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        logger.info(f"Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | LR: {current_lr:.6f}")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), output_checkpoint)
            logger.info(f"Saved new best model checkpoint to {output_checkpoint}")

    # --- Hard Negative Mining: reweight loader to oversample worst cases ---
    logger.info("\n=== Hard Negative Mining Pass (1 additional epoch) ===")
    model.load_state_dict(torch.load(output_checkpoint, map_location=device))
    model.eval()

    sample_losses = []
    with torch.no_grad():
        for i, (imgs, masks) in enumerate(val_loader):
            imgs, masks = imgs.to(device), masks.to(device)
            logits = model(imgs)
            loss_per_sample = nn.functional.binary_cross_entropy_with_logits(logits, masks, reduction="none").mean(dim=(1, 2, 3))
            for j in range(loss_per_sample.size(0)):
                sample_losses.append((val_paths[i * batch_size + j], loss_per_sample[j].item()))

    # Sort by loss descending, take top 20% as hard negatives
    sample_losses.sort(key=lambda x: x[1], reverse=True)
    n_hard = max(1, int(len(sample_losses) * 0.20))
    hard_negative_paths = [s[0] for s in sample_losses[:n_hard]]
    logger.info(f"Identified {n_hard} hard negative samples (top 20% by loss)")

    # Create oversampled training set: original train + hard negatives repeated
    hard_ds = SARDataset(hard_negative_paths, target_size=target_size)
    combined_paths = train_paths + hard_negative_paths * 3
    combined_ds = SARDataset(combined_paths, target_size=target_size)
    combined_loader = DataLoader(combined_ds, batch_size=batch_size, shuffle=True, num_workers=0)

    # Fine-tune for 2 more epochs with lower LR
    for epoch in range(1, 3):
        model.train()
        epoch_loss = 0.0
        for imgs, masks in combined_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss = criterion(logits, masks)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * imgs.size(0)
        epoch_loss /= len(combined_ds)
        logger.info(f"Hard Neg Epoch [{epoch}/2] - Loss: {epoch_loss:.4f}")

    # Save final model
    torch.save(model.state_dict(), output_checkpoint)
    logger.info(f"Saved hard-negative-finetuned checkpoint to {output_checkpoint}")

    # --- Threshold Grid Search on Validation Set ---
    logger.info("\n=== Threshold Grid Search on Validation Set ===")
    model.load_state_dict(torch.load(output_checkpoint, map_location=device))
    model.eval()

    thresholds_to_test = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55]
    best_threshold = 0.5
    best_f1 = 0.0

    all_val_preds, all_val_targets = [], []
    all_val_probs = []
    with torch.no_grad():
        for imgs, masks in val_loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.sigmoid(logits)
            all_val_probs.append(probs.cpu().numpy())
            all_val_targets.append(masks.cpu().numpy().astype(np.uint8))
    all_val_probs = np.concatenate(all_val_probs, axis=0)
    all_val_targets = np.concatenate(all_val_targets, axis=0)

    for t in thresholds_to_test:
        preds = (all_val_probs > t).astype(np.uint8)
        m = calculate_metrics(preds, all_val_targets)
        f1 = 2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"] + 1e-6)
        logger.info(f"  Threshold {t:.2f} -> IoU: {m['iou']:.4f} | Dice: {m['dice']:.4f} | Precision: {m['precision']:.4f} | Recall: {m['recall']:.4f} | F1: {f1:.4f}")
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t

    logger.info(f"\nBest threshold: {best_threshold:.2f} (F1={best_f1:.4f})")

    # Also test at best threshold for recall-focused selection
    best_recall = 0.0
    recall_threshold = 0.5
    for t in thresholds_to_test:
        preds = (all_val_probs > t).astype(np.uint8)
        m = calculate_metrics(preds, all_val_targets)
        if m["recall"] > best_recall and m["precision"] >= 0.30:
            best_recall = m["recall"]
            recall_threshold = t

    logger.info(f"Best recall-focused threshold: {recall_threshold:.2f} (Recall={best_recall:.4f}, min precision 0.30)")

    # Use the F1-optimal threshold as final
    final_threshold = best_threshold
    logger.info(f"Using final threshold: {final_threshold}")

    # --- Evaluate on Test Set ---
    logger.info("\n=== Evaluating Model on Held-Out Test Set ===")
    model.load_state_dict(torch.load(output_checkpoint, map_location=device))
    model.eval()
    
    test_preds, test_targets = [], []
    with torch.no_grad():
        for imgs, masks in test_loader:
            imgs = imgs.to(device)
            logits = model(imgs)
            probs = torch.sigmoid(logits)
            preds = (probs > final_threshold).cpu().numpy().astype(np.uint8)
            targets = masks.cpu().numpy().astype(np.uint8)
            
            test_preds.append(preds)
            test_targets.append(targets)

    test_preds = np.concatenate(test_preds, axis=0)
    test_targets = np.concatenate(test_targets, axis=0)

    metrics = calculate_metrics(test_preds, test_targets)
    logger.info(f"Test Set Metrics (threshold={final_threshold}) -> IoU: {metrics['iou']} | Dice: {metrics['dice']} | Precision: {metrics['precision']} | Recall: {metrics['recall']}")
    print(f"\n=======================================================")
    print(f"SUCCESS: Model Training & Evaluation Complete!")
    print(f"Trained Checkpoint: {output_checkpoint}")
    print(f"Optimal Threshold: {final_threshold}")
    print(f"Test Set IoU (Jaccard Index): {metrics['iou'] * 100:.2f}%")
    print(f"Test Set Dice Score: {metrics['dice'] * 100:.2f}%")
    print(f"Test Set Precision: {metrics['precision'] * 100:.2f}%")
    print(f"Test Set Recall: {metrics['recall'] * 100:.2f}%")
    print(f"=======================================================\n")

    return final_threshold

if __name__ == "__main__":
    best_threshold = train_spill_model(epochs=10, batch_size=4, target_size=(256, 256))
    if best_threshold:
        print(f"\nOptimal detection threshold for segmentation_model.py: {best_threshold}")
        print("Update the default threshold in SpillSegmentationModel.predict() if needed.")
