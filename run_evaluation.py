"""
Baseline evaluation and threshold sweep for SagarDrishti segmentation model.
Uses the existing checkpoint to establish baseline metrics.
"""
import sys
import os
import glob
import random
import logging
import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

import segmentation_models_pytorch as smp
from src.detection.train_model import (
    SARDataset, evaluate_at_threshold, evaluate_threshold_sweep,
    collect_probs_and_targets, select_best_threshold,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval")

def setup_splits(data_dir="data/raw/SARSatelite"):
    category_paths = {}
    for cat in ["Oil", "Lookalike", "No oil"]:
        cat_dir = os.path.join(data_dir, "Images", cat)
        files = sorted(glob.glob(os.path.join(cat_dir, "*.tif")))
        category_paths[cat] = files

    train_paths, val_paths, test_paths = [], [], []
    for cat, files in category_paths.items():
        n = len(files)
        n_train = int(n * 0.70)
        n_val = int(n * 0.15)
        cat_train, cat_val, cat_test = files[:n_train], files[n_train:n_train+n_val], files[n_train+n_val:]
        train_paths.extend(cat_train)
        val_paths.extend(cat_val)
        test_paths.extend(cat_test)

    random.shuffle(train_paths)
    return train_paths, val_paths, test_paths

def main():
    data_dir = "data/raw/SARSatelite"
    target_size = (256, 256)
    batch_size = 4
    device = "cuda" if torch.cuda.is_available() else "cpu"

    train_paths, val_paths, test_paths = setup_splits(data_dir)
    print(f"Split: Train={len(train_paths)}, Val={len(val_paths)}, Test={len(test_paths)}")

    val_ds = SARDataset(val_paths, target_size=target_size)
    test_ds = SARDataset(test_paths, target_size=target_size)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    model = smp.Unet(encoder_name="resnet34", encoder_weights=None, in_channels=2, classes=1, activation=None)
    ckpt = torch.load("models/spill_unet.pth", map_location=device)
    model.load_state_dict(ckpt)
    model.to(device).eval()
    print(f"Loaded existing checkpoint, device={device}")

    # BASELINE EVALUATION
    print("\n=== BASELINE EVALUATION (tau=0.5) ===")
    v_probs, v_targets = collect_probs_and_targets(model, val_loader, device)
    t_probs, t_targets = collect_probs_and_targets(model, test_loader, device)

    baseline_val = evaluate_at_threshold(v_probs, v_targets, 0.5)
    baseline_test = evaluate_at_threshold(t_probs, t_targets, 0.5)
    print(f"Baseline VAL  (tau=0.5): {baseline_val}")
    print(f"Baseline TEST (tau=0.5): {baseline_test}")

    # THRESHOLD SWEEP ON VALIDATION ONLY
    print("\n=== VALIDATION THRESHOLD SWEEP ===")
    threshold_grid = [0.20, 0.25, 0.30, 0.325, 0.35, 0.375, 0.40, 0.425, 0.45, 0.475, 0.50]
    sweep = evaluate_threshold_sweep(model, val_loader, threshold_grid, device)

    print("\nThreshold Sweep Results:")
    print(f"{'tau':>6} {'Precision':>10} {'Recall':>8} {'F1':>8} {'IoU':>8} {'Dice':>8}")
    for t in threshold_grid:
        m = sweep[t]
        print(f"{t:>6.3f} {m['precision']:>10.4f} {m['recall']:>8.4f} {m['f1']:>8.4f} {m['iou']:>8.4f} {m['dice']:>8.4f}")

    chosen_threshold = select_best_threshold(sweep, min_precision=0.35)
    print(f"\nSelected threshold: {chosen_threshold}")

    # FINAL TEST EVALUATION AT SELECTED THRESHOLD (one-time)
    print("\n=== FINAL TEST EVALUATION AT SELECTED THRESHOLD ===")
    new_test_metrics = evaluate_at_threshold(t_probs, t_targets, chosen_threshold)
    print(f"Test metrics at tau={chosen_threshold}: {new_test_metrics}")
    new_val_metrics = sweep[chosen_threshold]
    print(f"Val metrics at tau={chosen_threshold}: {new_val_metrics}")

    return {
        "baseline_val": baseline_val,
        "baseline_test": baseline_test,
        "chosen_threshold": chosen_threshold,
        "new_val": new_val_metrics,
        "new_test": new_test_metrics,
        "sweep": sweep,
    }

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    main()
