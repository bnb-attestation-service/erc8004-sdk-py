"""Built-in contract ABIs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

_ABI_DIR = Path(__file__).parent


def _load_abi(filename: str) -> List[Dict[str, Any]]:
    """Load an ABI JSON file from the package."""
    abi_path = _ABI_DIR / filename
    with abi_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


IDENTITY_REGISTRY_ABI: List[Dict[str, Any]] = _load_abi("identityRegistry.json")
REPUTATION_REGISTRY_ABI: List[Dict[str, Any]] = _load_abi("reputationRegistry.json")

__all__ = [
    "IDENTITY_REGISTRY_ABI",
    "REPUTATION_REGISTRY_ABI",
]

