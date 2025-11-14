"""Tests for IPFS storage functionality."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from requests import RequestException

from erc8004_sdk.exceptions import IPFSStorageError
from erc8004_sdk.storage import IPFSStorage
from erc8004_sdk.types import AgentEndpoint, AgentProfile, AgentRegistrationEntry


def test_store_json_serializes_and_uploads():
    """Test that store_json serializes data and uploads to IPFS."""
    storage = IPFSStorage(ipfs_url="http://localhost:5001")

    test_data = {
        "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
        "name": "testAgent",
        "description": "A test agent",
    }

    with patch("erc8004_sdk.storage.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"Hash": "QmTest123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        cid = storage.store_json(test_data)

        assert cid == "ipfs://QmTest123"
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/v0/add" in call_args[0][0]
        assert "files" in call_args[1]


def test_store_file_reads_and_uploads():
    """Test that store_file reads a file and uploads to IPFS."""
    storage = IPFSStorage(ipfs_url="http://localhost:5001")

    # Create a temporary test file
    test_file = Path("/tmp/test_ipfs_file.txt")
    test_file.write_text("test content")

    try:
        with patch("erc8004_sdk.storage.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"Hash": "QmFile123"}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            cid = storage.store_file(test_file)

            assert cid == "ipfs://QmFile123"
            mock_post.assert_called_once()
    finally:
        if test_file.exists():
            test_file.unlink()


def test_store_file_raises_on_missing_file():
    """Test that store_file raises error for missing file."""
    storage = IPFSStorage(ipfs_url="http://localhost:5001")

    with pytest.raises(IPFSStorageError, match="File not found"):
        storage.store_file("/nonexistent/file.txt")


def test_store_json_raises_on_invalid_data():
    """Test that store_json raises error for non-serializable data."""
    storage = IPFSStorage(ipfs_url="http://localhost:5001")

    # Create a non-serializable object
    class NonSerializable:
        pass

    with pytest.raises(IPFSStorageError, match="Failed to serialize"):
        storage.store_json({"data": NonSerializable()})


def test_store_via_pinning_service():
    """Test storing via pinning service (e.g., Pinata)."""
    storage = IPFSStorage(
        ipfs_url="http://localhost:5001",
        ipfs_gateway="https://api.pinata.cloud",
        api_key="test_key",
        api_secret="test_secret",
    )

    test_data = {"test": "data"}

    with patch("erc8004_sdk.storage.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"IpfsHash": "QmPinata123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        cid = storage.store_json(test_data)

        assert cid == "ipfs://QmPinata123"
        call_args = mock_post.call_args
        assert "pinata.cloud" in call_args[0][0]
        assert call_args[1]["headers"]["pinata_api_key"] == "test_key"


def test_store_handles_connection_error():
    """Test that storage handles connection errors gracefully."""
    storage = IPFSStorage(ipfs_url="http://localhost:5001")

    with patch("erc8004_sdk.storage.requests.post") as mock_post:
        mock_post.side_effect = RequestException("Connection refused")

        with pytest.raises(IPFSStorageError, match="Failed to connect"):
            storage.store_json({"test": "data"})


def test_store_agent_profile_generates_expected_payload():
    """Test storing a structured agent profile to IPFS."""
    storage = IPFSStorage(ipfs_url="http://localhost:5001")

    profile = AgentProfile(
        name="myAgentName",
        description="A natural language description of the Agent",
        image="https://example.com/agentimage.png",
        endpoints=[
            AgentEndpoint(name="A2A", endpoint="https://agent.example/.well-known/agent-card.json", version="0.3.0"),
            {
                "name": "agentWallet",
                "endpoint": "eip155:1:0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7",
            },
        ],
        registrations=[
            AgentRegistrationEntry(agent_id=22, agent_registry="eip155:1:0xRegistry"),
        ],
        supported_trust=["reputation", "crypto-economic", "tee-attestation"],
    )

    with patch("erc8004_sdk.storage.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"Hash": "QmProfile123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        cid = storage.store_agent_profile(profile)

        assert cid == "ipfs://QmProfile123"
        args, kwargs = mock_post.call_args
        assert "/api/v0/add" in args[0]
        payload_bytes = kwargs["files"]["file"][1]
        payload = json.loads(payload_bytes.decode("utf-8"))
        assert payload["name"] == "myAgentName"
        assert payload["supportedTrust"] == [
            "reputation",
            "crypto-economic",
            "tee-attestation",
        ]
        assert payload["endpoints"][0]["name"] == "A2A"

