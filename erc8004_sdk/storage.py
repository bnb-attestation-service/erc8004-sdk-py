"""IPFS storage utilities for storing JSON metadata and files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

from .exceptions import IPFSStorageError
from .types import AgentProfile


class IPFSStorage:
    """Service for storing data to IPFS."""

    def __init__(
        self,
        *,
        ipfs_url: str = "http://127.0.0.1:5001",
        ipfs_gateway: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> None:
        """
        Initialize IPFS storage service.

        Args:
            ipfs_url: IPFS API endpoint URL (default: http://127.0.0.1:5001)
            ipfs_gateway: Optional IPFS gateway URL for pinning services (e.g., Pinata)
            api_key: Optional API key for IPFS pinning service
            api_secret: Optional API secret for IPFS pinning service
        """
        self.ipfs_url = ipfs_url.rstrip("/")
        self.ipfs_gateway = ipfs_gateway.rstrip("/") if ipfs_gateway else None
        self.api_key = api_key
        self.api_secret = api_secret

    def store_json(
        self,
        data: Dict[str, Any],
        *,
        pin: bool = True,
    ) -> str:
        """
        Serialize a data structure to JSON and store it to IPFS.

        Args:
            data: Dictionary containing the data to store
            pin: Whether to pin the content (default: True)

        Returns:
            IPFS CID (Content Identifier) as a string, prefixed with "ipfs://"

        Raises:
            IPFSStorageError: If the storage operation fails
        """
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            json_bytes = json_str.encode("utf-8")
            return self.store_file_content(json_bytes, pin=pin)
        except (TypeError, ValueError) as err:
            raise IPFSStorageError(f"Failed to serialize data to JSON: {err}") from err

    def store_file(
        self,
        file_path: Union[str, Path],
        *,
        pin: bool = True,
    ) -> str:
        """
        Store a file directly to IPFS.

        Args:
            file_path: Path to the file to upload
            pin: Whether to pin the content (default: True)

        Returns:
            IPFS CID (Content Identifier) as a string, prefixed with "ipfs://"

        Raises:
            IPFSStorageError: If the storage operation fails
        """
        path = Path(file_path)
        if not path.exists():
            raise IPFSStorageError(f"File not found: {file_path}")

        try:
            with path.open("rb") as f:
                file_content = f.read()
            return self.store_file_content(file_content, pin=pin)
        except IOError as err:
            raise IPFSStorageError(f"Failed to read file: {err}") from err

    def store_file_content(
        self,
        content: bytes,
        *,
        pin: bool = True,
    ) -> str:
        """
        Store raw bytes content to IPFS.

        Args:
            content: Raw bytes content to store
            pin: Whether to pin the content (default: True)

        Returns:
            IPFS CID (Content Identifier) as a string, prefixed with "ipfs://"

        Raises:
            IPFSStorageError: If the storage operation fails
        """
        # Try using pinning service first if configured
        if self.ipfs_gateway and self.api_key:
            try:
                return self._store_via_pinning_service(content, pin=pin)
            except IPFSStorageError:
                # Fall back to local IPFS node
                pass

        # Use local IPFS node
        return self._store_via_local_node(content, pin=pin)

    def store_agent_profile(self, profile: AgentProfile, *, pin: bool = True) -> str:
        """
        Store a structured agent profile document on IPFS.

        Args:
            profile: AgentProfile dataclass containing the metadata
            pin: Whether to pin the generated JSON (default: True)

        Returns:
            IPFS URI (ipfs://<cid>) of the stored profile document.
        """
        return self.store_json(profile.to_dict(), pin=pin)

    def _store_via_local_node(
        self,
        content: bytes,
        *,
        pin: bool = True,
    ) -> str:
        """Store content via local IPFS node."""
        try:
            # Use IPFS HTTP API /api/v0/add endpoint
            files = {"file": ("data", content)}
            params = {"pin": "true" if pin else "false"}

            response = requests.post(
                f"{self.ipfs_url}/api/v0/add",
                files=files,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            cid = result.get("Hash")
            if not cid:
                raise IPFSStorageError("IPFS API did not return a CID")

            return f"ipfs://{cid}"
        except requests.RequestException as err:
            raise IPFSStorageError(
                f"Failed to connect to IPFS node at {self.ipfs_url}: {err}"
            ) from err
        except (KeyError, ValueError) as err:
            raise IPFSStorageError(f"Invalid response from IPFS API: {err}") from err

    def _store_via_pinning_service(
        self,
        content: bytes,
        *,
        pin: bool = True,
    ) -> str:
        """Store content via IPFS pinning service (e.g., Pinata)."""
        if not self.ipfs_gateway or not self.api_key:
            raise IPFSStorageError("Pinning service credentials not configured")

        try:
            # Support Pinata API format
            headers = {
                "pinata_api_key": self.api_key,
            }
            if self.api_secret:
                headers["pinata_secret_api_key"] = self.api_secret

            files = {"file": ("data", content)}
            data = {"pinataOptions": json.dumps({"cidVersion": 1})}

            response = requests.post(
                f"{self.ipfs_gateway}/pinning/pinFileToIPFS",
                files=files,
                data=data,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            cid = result.get("IpfsHash")
            if not cid:
                raise IPFSStorageError("Pinning service did not return a CID")

            return f"ipfs://{cid}"
        except requests.RequestException as err:
            raise IPFSStorageError(
                f"Failed to upload to IPFS pinning service: {err}"
            ) from err
        except (KeyError, ValueError) as err:
            raise IPFSStorageError(f"Invalid response from pinning service: {err}") from err