"""
USP feature - Near-real-time monitor.

Watches a folder (standing in for a satellite-tasking feed/API) for newly
arrived SAR images and auto-triggers the full pipeline the moment one shows
up, instead of requiring a manual upload each time. This is what lets you
honestly say "near-real-time, triggered on every satellite pass" rather than
"you have to click run" - the actual latency is bounded by Sentinel-1's
revisit cadence, not by this code, and that's fine to say out loud.

Run standalone:
    python -m src.pipeline.monitor --watch data/raw/satellite/incoming --interval 30

Or import `Monitor` into the Streamlit app to run in a background thread so
the dashboard updates itself when a new image appears during the demo.
"""

import os
import time
import glob
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [monitor] %(message)s")
log = logging.getLogger("monitor")

class Monitor:
    def __init__(self, watch_dir: str, on_new_image, interval_seconds: int = 30):
        """
        Args:
            watch_dir: folder to poll for new .tif/.tiff files.
            on_new_image: callback fn(image_path: str) -> dict, typically
                          src.pipeline.run_pipeline.run
            interval_seconds: how often to poll. In production this maps to
                          how often you'd check a satellite provider's API
                          for a new pass - NOT continuous streaming, since
                          Sentinel-1 revisit is ~6-12 days, so polling this
                          often is already faster than new data can arrive.
        """
        self.watch_dir = watch_dir
        self.on_new_image = on_new_image
        self.interval_seconds = interval_seconds
        self._seen = set()
        self.log_events = []  # for the dashboard's "activity timeline"

    def _scan_once(self):
        # Create watch dir if not exists
        if not os.path.exists(self.watch_dir):
            try:
                os.makedirs(self.watch_dir)
            except Exception:
                pass
                
        files = set(glob.glob(os.path.join(self.watch_dir, "*.tif")) +
                    glob.glob(os.path.join(self.watch_dir, "*.tiff")))
        new_files = files - self._seen
        self._seen |= files

        checked_at = datetime.now(timezone.utc).isoformat()
        if not new_files:
            self.log_events.append({"time": checked_at, "event": "checked, no new pass"})
            log.info("checked %s - no new images", self.watch_dir)
            return

        for path in sorted(new_files):
            log.info("new image detected: %s", path)
            try:
                result = self.on_new_image(path)
                spill_found = bool(result and result.get("spill_detected"))
                self.log_events.append({
                    "time": checked_at,
                    "event": f"new pass processed: {os.path.basename(path)}",
                    "spill_detected": spill_found,
                })
            except Exception as e:  # noqa: BLE001 - monitor must never crash on one bad file
                log.exception("pipeline failed on %s", path)
                self.log_events.append({
                    "time": checked_at,
                    "event": f"FAILED processing {os.path.basename(path)}: {e}",
                })

    def run_forever(self):
        log.info("watching %s every %ss", self.watch_dir, self.interval_seconds)
        while True:
            self._scan_once()
            time.sleep(self.interval_seconds)

    def run_once(self):
        """For tests/demo control - scan a single time instead of looping."""
        self._scan_once()

if __name__ == "__main__":
    import argparse
    from src.pipeline.run_pipeline import run as run_pipeline

    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", required=True)
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()

    Monitor(args.watch, on_new_image=run_pipeline, interval_seconds=args.interval).run_forever()
