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

import shutil
from typing import Optional
from torch.utils.data import WeightedRandomSampler

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

class BinaryFocalLoss(nn.Module):
    """FL(pt) = -alpha_t * (1 - pt)^gamma * log(pt)."""
    def __init__(self, gamma: float = 2.0, alpha: float = 0.25, eps: float = 1e-6):
        super().__init__()
        self.gamma, self.alpha, self.eps = gamma, alpha, eps

    def forward(self, inputs, targets):
        targets = targets.float()
        bce = nn.functional.binary_cross_entropy_with_logits(inputs, targets, reduction="none")
        probs = torch.sigmoid(inputs).clamp(self.eps, 1.0 - self.eps)
        pt = torch.where(targets == 1, probs, 1.0 - probs)
        alpha_t = torch.where(targets == 1,
                               torch.full_like(targets, self.alpha),
                               torch.full_like(targets, 1.0 - self.alpha))
        return (alpha_t * (1.0 - pt).pow(self.gamma) * bce).mean()


class CombinedSpillLoss(nn.Module):
    """w_dice*L_dice + w_bce*L_bce + w_focal*L_focal. Dice term reuses the
    exact same formula as DiceBCELoss so it's numerically consistent."""
    def __init__(self, dice_weight=0.4, bce_weight=0.3, focal_weight=0.3,
                 focal_gamma=2.0, focal_alpha=0.25):
        super().__init__()
        self.dice_weight, self.bce_weight, self.focal_weight = dice_weight, bce_weight, focal_weight
        self.bce = nn.BCEWithLogitsLoss()
        self.focal = BinaryFocalLoss(gamma=focal_gamma, alpha=focal_alpha)

    def forward(self, inputs, targets):
        targets = targets.float()
        probs = torch.sigmoid(inputs)
        smooth = 1.0
        inputs_flat, targets_flat = probs.view(-1), targets.view(-1)
        intersection = (inputs_flat * targets_flat).sum()
        l_dice = 1.0 - (2.0 * intersection + smooth) / (inputs_flat.sum() + targets_flat.sum() + smooth)
        l_bce = self.bce(inputs, targets)
        l_focal = self.focal(inputs, targets)
        return self.dice_weight * l_dice + self.bce_weight * l_bce + self.focal_weight * l_focal


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
    f1 = float(2 * precision * recall / (precision + recall + 1e-6))
    
    return {
        "iou": round(iou, 4),
        "dice": round(dice, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }

def collect_probs_and_targets(model, loader, device):
    """Run inference once, cache probs so a threshold sweep doesn't re-run
    the model per threshold."""
    model.eval()
    all_probs, all_targets = [], []
    with torch.no_grad():
        for imgs, masks in loader:
            probs = torch.sigmoid(model(imgs.to(device))).cpu().numpy()
            all_probs.append(probs)
            all_targets.append(masks.numpy())
    return np.concatenate(all_probs, axis=0), np.concatenate(all_targets, axis=0)


def evaluate_at_threshold(probs: np.ndarray, targets: np.ndarray, threshold: float) -> Dict[str, float]:
    return calculate_metrics((probs > threshold).astype(np.uint8), targets.astype(np.uint8))


def evaluate_threshold_sweep(model, val_loader, thresholds: List[float], device: str) -> Dict[float, Dict[str, float]]:
    """VALIDATION ONLY. Never pass test_loader here."""
    probs, targets = collect_probs_and_targets(model, val_loader, device)
    results = {}
    for t in thresholds:
        results[t] = evaluate_at_threshold(probs, targets, t)
        m = results[t]
        logger.info(f"  τ={t:.3f} -> P={m['precision']:.4f} R={m['recall']:.4f} "
                    f"F1={m['f1']:.4f} IoU={m['iou']:.4f} Dice={m['dice']:.4f}")
    return results


def select_best_threshold(sweep_results: Dict[float, Dict[str, float]], min_precision: float = 0.35) -> float:
    candidates = {t: m for t, m in sweep_results.items() if m["precision"] >= min_precision}
    pool = candidates if candidates else sweep_results
    if not candidates:
        logger.warning(f"No threshold kept precision >= {min_precision}; falling back to best-F1 overall.")
    return max(pool, key=lambda t: pool[t]["f1"])


def mine_hard_negatives(model, lookalike_paths: List[str], device: str,
                         target_size: Tuple[int, int] = (256, 256), top_k: int = 30) -> List[str]:
    """Lookalike images have all-zero ground truth. Rank by mean predicted
    foreground prob -- high prob on a true-zero mask = false positive the
    model is being fooled by."""
    if not lookalike_paths:
        return []
    ds = SARDataset(lookalike_paths, target_size=target_size)
    model.eval()
    scored = []
    with torch.no_grad():
        for i in range(len(ds)):
            img, _ = ds[i]
            prob = torch.sigmoid(model(img.unsqueeze(0).to(device)))
            scored.append((lookalike_paths[i], prob.mean().item()))
    scored.sort(key=lambda x: x[1], reverse=True)
    hard = [p for p, _ in scored[:top_k]]
    logger.info(f"Mined {len(hard)} hard-negative lookalikes (top FP prob {scored[0][1]:.4f})")
    return hard

def train_spill_model(
    data_dir: str = "data/raw/SARSatelite",
    output_checkpoint: str = "models/checkpoints/spill_unet_resnet34.pth",

    final_model_path: str = "models/spill_unet.pth",
    backup_model_path: str = "models/spill_unet_backup_baseline.pth",
    epochs: int = 10,

    batch_size: int = 4,
    lr: float = 1e-3,
    target_size: Tuple[int, int] = (256, 256),
    init_from_checkpoint: Optional[str] = "models/spill_unet.pth",
    dice_weight: float = 0.4,
    bce_weight: float = 0.3,
    focal_weight: float = 0.3,
    focal_gamma: float = 2.0,
    focal_alpha: float = 0.25,
    hard_negative_top_k: int = 30,
    hard_negative_oversample_factor: float = 3.0,
    threshold_grid: Optional[List[float]] = None,
    min_precision_floor: float = 0.35,
):
    if smp is None:
        logger.error("segmentation-models-pytorch is required for training.")
        return

    if threshold_grid is None:
        threshold_grid = [0.20, 0.25, 0.30, 0.325, 0.35, 0.375, 0.40, 0.425, 0.45, 0.475, 0.50]

    # ---- stratified split (paste block from step 2 here) ----
    category_paths: Dict[str, List[str]] = {}
    for cat in ["Oil", "Lookalike", "No oil"]:
        cat_dir = os.path.join(data_dir, "Images", cat)
        files = sorted(glob.glob(os.path.join(cat_dir, "*.tif"))) if os.path.exists(cat_dir) else []
        random.shuffle(files)
        category_paths[cat] = files
        logger.info(f"Category '{cat}': {len(files)} samples")

    if not any(category_paths.values()):
        logger.error(f"No satellite images found in {data_dir}")
        return

    train_paths, val_paths, test_paths = [], [], []
    lookalike_train_paths: List[str] = []
    for cat, files in category_paths.items():
        n = len(files)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        cat_train, cat_val, cat_test = files[:n_train], files[n_train:n_train + n_val], files[n_train + n_val:]
        train_paths.extend(cat_train)
        val_paths.extend(cat_val)
        test_paths.extend(cat_test)
        if cat == "Lookalike":
            lookalike_train_paths = cat_train
    random.shuffle(train_paths)
    logger.info(f"Dataset Split -> Train: {len(train_paths)} | Val: {len(val_paths)} | Test: {len(test_paths)}")

    train_ds = SARDataset(train_paths, target_size=target_size)
    val_ds = SARDataset(val_paths, target_size=target_size)
    test_ds = SARDataset(test_paths, target_size=target_size)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Initializing U-Net (ResNet-34) model on device: {device}")

    have_existing = init_from_checkpoint and os.path.exists(init_from_checkpoint)
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None if have_existing else "imagenet",
        in_channels=2,
        classes=1,
        activation=None
    ).to(device)

    baseline_val_metrics = baseline_test_metrics = None
    if have_existing:
        model.load_state_dict(torch.load(init_from_checkpoint, map_location=device))
        logger.info(f"Initialized from existing checkpoint: {init_from_checkpoint}")

        # ---- Step 2: BASELINE EVAL (before touching weights at all) ----
        logger.info("=== Baseline evaluation (τ=0.5, currently-deployed weights) ===")
        v_probs, v_targets = collect_probs_and_targets(model, val_loader, device)
        t_probs, t_targets = collect_probs_and_targets(model, test_loader, device)
        baseline_val_metrics = evaluate_at_threshold(v_probs, v_targets, 0.5)
        baseline_test_metrics = evaluate_at_threshold(t_probs, t_targets, 0.5)
        logger.info(f"Baseline VAL:  {baseline_val_metrics}")
        logger.info(f"Baseline TEST: {baseline_test_metrics}")

        # ---- Step 6: hard-negative mining using the CURRENT (baseline) model ----
        hard_negatives = set(mine_hard_negatives(
            model, lookalike_train_paths, device, target_size, top_k=hard_negative_top_k
        ))
        if hard_negatives:
            weights = [hard_negative_oversample_factor if p in hard_negatives else 1.0 for p in train_paths]
            sampler = WeightedRandomSampler(weights, num_samples=len(train_paths), replacement=True)
            train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=0)
            logger.info(f"Training loader now oversamples {len(hard_negatives)} hard-negative lookalikes "
                        f"at {hard_negative_oversample_factor}x weight.")
    else:
        logger.warning(f"No existing checkpoint at {init_from_checkpoint}; training from ImageNet init, "
                        "no baseline comparison, no hard-negative mining (baseline model needed for that).")

    criterion = CombinedSpillLoss(dice_weight, bce_weight, focal_weight, focal_gamma, focal_alpha)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2, min_lr=1e-5)

    best_val_loss = float("inf")
    os.makedirs(os.path.dirname(output_checkpoint), exist_ok=True)

    logger.info("Starting PyTorch U-Net training loop (CombinedSpillLoss + ReduceLROnPlateau)...")

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for imgs, masks in train_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), masks)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
        train_loss /= len(train_ds)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                val_loss += criterion(model(imgs), masks).item() * imgs.size(0)
        val_loss /= len(val_ds)


        lr_before = optimizer.param_groups[0]["lr"]
        scheduler.step(val_loss)
        lr_after = optimizer.param_groups[0]["lr"]
        if lr_after < lr_before:
            logger.info(f"ReduceLROnPlateau: LR {lr_before:.2e} -> {lr_after:.2e}")

        logger.info(f"Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), output_checkpoint)
            logger.info(f"Saved new best model checkpoint to {output_checkpoint}")

    # ---- reload best checkpoint from this run ----
    model.load_state_dict(torch.load(output_checkpoint, map_location=device))

    # ---- Additional hard-negative fine-tuning pass (loss-based, on TRAIN set
    # only -- never mine from val_loader, that would leak val samples into
    # training and invalidate the later threshold sweep) ----
    logger.info("\n=== Loss-based Hard Negative Mining Pass (fine-tune 2 epochs) ===")
    model.eval()
    sample_losses = []
    train_eval_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    with torch.no_grad():
        for i, (imgs, masks) in enumerate(train_eval_loader):
            imgs, masks = imgs.to(device), masks.to(device)
            logits = model(imgs)
            loss_per_sample = nn.functional.binary_cross_entropy_with_logits(
                logits, masks, reduction="none"
            ).mean(dim=(1, 2, 3))
            for j in range(loss_per_sample.size(0)):
                idx = i * batch_size + j
                if idx < len(train_paths):
                    sample_losses.append((train_paths[idx], loss_per_sample[j].item()))

    sample_losses.sort(key=lambda x: x[1], reverse=True)
    n_hard = max(1, int(len(sample_losses) * 0.20))
    loss_hard_negative_paths = [s[0] for s in sample_losses[:n_hard]]
    logger.info(f"Identified {n_hard} loss-based hard negatives from TRAIN set (top 20% by loss)")

    combined_paths = train_paths + loss_hard_negative_paths * 3
    combined_ds = SARDataset(combined_paths, target_size=target_size)
    combined_loader = DataLoader(combined_ds, batch_size=batch_size, shuffle=True, num_workers=0)

    for ft_epoch in range(1, 3):
        model.train()
        epoch_loss = 0.0
        for imgs, masks in combined_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), masks)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * imgs.size(0)
        epoch_loss /= len(combined_ds)
        logger.info(f"Hard-Neg Fine-tune Epoch [{ft_epoch}/2] - Loss: {epoch_loss:.4f}")

    torch.save(model.state_dict(), output_checkpoint)
    logger.info(f"Saved hard-negative-finetuned checkpoint to {output_checkpoint}")

    # ---- Step 3/7: threshold sweep on VAL only (clean, un-contaminated), then select ----
    logger.info("=== Validation threshold sweep (final model) ===")
    sweep = evaluate_threshold_sweep(model, val_loader, threshold_grid, device)
    chosen_threshold = select_best_threshold(sweep, min_precision=min_precision_floor)
    logger.info(f"Selected threshold: {chosen_threshold} (best F1 subject to precision >= {min_precision_floor})")

    # ---- Step 7: final, ONE-TIME test evaluation at chosen threshold ----
    t_probs_new, t_targets_new = collect_probs_and_targets(model, test_loader, device)
    new_test_metrics = evaluate_at_threshold(t_probs_new, t_targets_new, chosen_threshold)
    new_val_metrics = sweep[chosen_threshold]

    logger.info("\n=========== BEFORE vs AFTER ===========")
    if baseline_val_metrics:
        logger.info(f"Baseline  VAL (τ=0.5):            {baseline_val_metrics}")
        logger.info(f"Baseline  TEST (τ=0.5):           {baseline_test_metrics}")
    logger.info(f"New model VAL  (τ={chosen_threshold}): {new_val_metrics}")
    logger.info(f"New model TEST (τ={chosen_threshold}): {new_test_metrics}")
    logger.info("========================================\n")

    # ---- Step 8: backup + save to the paths the rest of the team's pipeline loads ----
    if os.path.exists(final_model_path):
        shutil.copy2(final_model_path, backup_model_path)
        logger.info(f"Backed up existing model: {final_model_path} -> {backup_model_path}")
    torch.save(model.state_dict(), final_model_path)
    torch.save(model.state_dict(), output_checkpoint)
    logger.info(f"Saved verified model to {final_model_path} and {output_checkpoint}")

    # Update config with the chosen segmentation threshold
    try:
        import yaml
        config_path_str = "config/config.yaml"
        if os.path.exists(config_path_str):
            with open(config_path_str, "r") as f:
                cfg = yaml.safe_load(f) or {}
            cfg.setdefault("detection", {})["confidence_threshold"] = chosen_threshold
            with open(config_path_str, "w") as f:
                yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Updated config.yaml with confidence_threshold={chosen_threshold}")
    except Exception as e:
        logger.warning(f"Could not update config.yaml with threshold: {e}")
    return {
        "chosen_threshold": chosen_threshold,
        "baseline_val": baseline_val_metrics,
        "baseline_test": baseline_test_metrics,
        "new_val": new_val_metrics,
        "new_test": new_test_metrics,
        "sweep": sweep,
    }


if __name__ == "__main__":
    train_spill_model(epochs=10, batch_size=4, target_size=(256, 256))