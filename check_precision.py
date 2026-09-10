"""Standalone check: does morphological cleanup improve precision on val set,
using the already-trained checkpoint? No retraining needed."""
import logging
logging.basicConfig(level=logging.INFO)
import torch
import cv2
import numpy as np
import glob, os, random
import segmentation_models_pytorch as smp
from src.detection.train_model import SARDataset, calculate_metrics

SEED = 42
random.seed(SEED)

device = "cpu"
data_dir = "data/raw/SARSatelite"

# Rebuild the SAME stratified split used in training (deterministic given SEED)
category_paths = {}
for cat in ["Oil", "Lookalike", "No oil"]:
    cat_dir = os.path.join(data_dir, "Images", cat)
    files = sorted(glob.glob(os.path.join(cat_dir, "*.tif")))
    random.shuffle(files)
    category_paths[cat] = files

val_paths, test_paths = [], []
for cat, files in category_paths.items():
    n = len(files)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    val_paths.extend(files[n_train:n_train + n_val])
    test_paths.extend(files[n_train + n_val:])

val_ds = SARDataset(val_paths, target_size=(256, 256))
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=4, shuffle=False)

model = smp.Unet(encoder_name="resnet34", encoder_weights=None, in_channels=2, classes=1, activation=None)
model.load_state_dict(torch.load("models/checkpoints/spill_unet_resnet34.pth", map_location=device))
model.to(device).eval()

def evaluate(threshold, use_morph):
    all_preds, all_targets = [], []
    kernel = np.ones((3, 3), np.uint8)
    with torch.no_grad():
        for imgs, masks in val_loader:
            probs = torch.sigmoid(model(imgs.to(device))).cpu().numpy()
            for i in range(probs.shape[0]):
                pm = probs[i, 0]
                m = (pm > threshold).astype(np.uint8)
                if use_morph and m.sum() > 0:
                    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
                all_preds.append(m)
                all_targets.append(masks[i, 0].numpy().astype(np.uint8))
    preds = np.stack(all_preds)
    targets = np.stack(all_targets)
    return calculate_metrics(preds, targets)

test_ds = SARDataset(test_paths, target_size=(256, 256))
test_loader = torch.utils.data.DataLoader(test_ds, batch_size=4, shuffle=False)

def evaluate_test(threshold, use_morph):
    all_preds, all_targets = [], []
    kernel = np.ones((3, 3), np.uint8)
    with torch.no_grad():
        for imgs, masks in test_loader:
            probs = torch.sigmoid(model(imgs.to(device))).cpu().numpy()
            for i in range(probs.shape[0]):
                pm = probs[i, 0]
                m = (pm > threshold).astype(np.uint8)
                if use_morph and m.sum() > 0:
                    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel)
                all_preds.append(m)
                all_targets.append(masks[i, 0].numpy().astype(np.uint8))
    preds = np.stack(all_preds)
    targets = np.stack(all_targets)
    return calculate_metrics(preds, targets)

print("\n--- TEST SET (final check, only run this once you're settled on candidates) ---")
for t in [0.30, 0.35]:
    r = evaluate_test(t, use_morph=True)
    print(f"τ={t:.2f} + cleanup on TEST: P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f} IoU={r['iou']:.3f}")

for t in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35]:
    without = evaluate(t, use_morph=False)
    withm = evaluate(t, use_morph=True)
    print(f"τ={t:.2f}  no-cleanup: P={without['precision']:.3f} R={without['recall']:.3f} F1={without['f1']:.3f}"
          f"   |   with-cleanup: P={withm['precision']:.3f} R={withm['recall']:.3f} F1={withm['f1']:.3f}")