"""Checkpoint and Resume state manager (Bonus Feature).

Saves progress periodically so an interrupted crawl can resume without restarting.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set


class CheckpointManager:
    """Manages crawl checkpoints and page-level state persistence."""

    def __init__(self, checkpoint_path: Path):
        self.checkpoint_path = checkpoint_path

    def load_checkpoint(self) -> Dict[str, Any]:
        """Load saved checkpoint data if file exists."""
        if self.checkpoint_path.exists():
            try:
                with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def is_page_completed(self, url: str) -> bool:
        """Check if a specific page URL has already been scraped."""
        data = self.load_checkpoint()
        completed_pages: Set[str] = set(data.get("completed_pages", []))
        return url in completed_pages

    def record_page_progress(self, url: str, records: List[Dict[str, Any]]) -> None:
        """Record completed page URL and its scraped records to the checkpoint file."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.load_checkpoint()
        completed = set(data.get("completed_pages", []))
        completed.add(url)

        saved_records = data.get("saved_records", [])
        saved_records.extend(records)

        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "completed_pages": list(completed),
                    "saved_records": saved_records,
                },
                f,
                indent=2,
            )

    def clear(self) -> None:
        """Remove checkpoint file upon successful pipeline completion."""
        if self.checkpoint_path.exists():
            try:
                self.checkpoint_path.unlink()
            except Exception:
                pass
