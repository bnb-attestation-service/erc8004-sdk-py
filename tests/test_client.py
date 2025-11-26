"""Tests for the ERC8004Client."""

from unittest.mock import MagicMock, patch

import pytest

from erc8004_sdk.client import ERC8004Client
from erc8004_sdk.exceptions import (
    ContractInteractionError,
    IPFSStorageError,
    SignatureError,
)
from erc8004_sdk.storage import IPFSStorage
from erc8004_sdk.signer import AuthFeedback
from erc8004_sdk.types import (
    AgentProfile,
    IdentityRegistrationReceipt,
    IdentityRegistrationResult,
)


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_client_initialization(mock_rep_cls, mock_id_cls):
    """Test that client initializes with built-in ABIs."""
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
        default_account="0x" + "3" * 40,
        private_key="0x" + "4" * 64,
    )

    assert client is not None
    mock_id_cls.assert_called_once()
    mock_rep_cls.assert_called_once()


def test_client_requires_identity_address():
    """Test that client requires identity contract address."""
    with pytest.raises(ContractInteractionError):
        ERC8004Client(
            rpc_url="http://localhost:8545",
            identity_contract_address="",
            reputation_contract_address="0x" + "2" * 40,
        )


def test_client_requires_reputation_address():
    """Test that client requires reputation contract address."""
    with pytest.raises(ContractInteractionError):
        ERC8004Client(
            rpc_url="http://localhost:8545",
            identity_contract_address="0x" + "1" * 40,
            reputation_contract_address="",
        )


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_register_minimal(mock_rep_cls, mock_id_cls):
    """Test registering an empty agent."""
    id_service = MagicMock()
    id_service.register_minimal.return_value = IdentityRegistrationResult(
        tx_hash="0xabc", agent_id=42
    )
    mock_id_cls.return_value = id_service
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    result = client.register_minimal()
    assert result.tx_hash == "0xabc"
    assert result.agent_id == 42
    id_service.register_minimal.assert_called_once()


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_set_agent_uri(mock_rep_cls, mock_id_cls):
    """Test setting agent URI."""
    id_service = MagicMock()
    id_service.set_agent_uri.return_value = "0xseturi"
    mock_id_cls.return_value = id_service
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    tx_hash = client.set_agent_uri(agent_id=42, new_uri="ipfs://new")
    assert tx_hash == "0xseturi"
    id_service.set_agent_uri.assert_called_once_with(
        agent_id=42, new_uri="ipfs://new", gas_limit=0, value=0
    )


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_approve(mock_rep_cls, mock_id_cls):
    """Test approving an agent."""
    id_service = MagicMock()
    id_service.approve.return_value = "0xapprove"
    mock_id_cls.return_value = id_service
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    tx_hash = client.approve(to_address="0x" + "5" * 40, token_id=42)
    assert tx_hash == "0xapprove"
    id_service.approve.assert_called_once_with(
        "0x" + "5" * 40, 42, gas_limit=0, value=0
    )


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_give_feedback(mock_rep_cls, mock_id_cls):
    """Test giving feedback."""
    mock_id_cls.return_value = MagicMock()
    rep_service = MagicMock()
    rep_service.give_feedback.return_value = "0xfeedback"
    mock_rep_cls.return_value = rep_service

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    tx_hash = client.give_feedback(
        agent_id=1,
        score=5,
        tag1="tag1",
        tag2="tag2",
        feedback_uri="ipfs://feedback",
        feedback_hash="0x" + "aa" * 32,
        feedback_auth=b"\x00" * 289,
    )
    assert tx_hash == "0xfeedback"
    rep_service.give_feedback.assert_called_once()


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_wait_for_receipt(mock_rep_cls, mock_id_cls):
    """Test waiting for receipt."""
    id_service = MagicMock()
    id_service.wait_for_receipt.return_value = IdentityRegistrationReceipt(
        raw_receipt={"status": 1},
        agent_id=42,
        events=[{"event": "Registered"}],
    )
    mock_id_cls.return_value = id_service
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    result = client.wait_for_receipt("0xabc")
    assert result["agentId"] == 42
    assert result["receipt"]["status"] == 1
    assert result["events"] == [{"event": "Registered"}]


def _make_profile(agent_id: int = 1) -> AgentProfile:
    return AgentProfile(
        name="Agent",
        description="Desc",
        image=None,
        endpoints=[],
        registrations=[{"agentId": agent_id, "agentRegistry": "eip155:1:0x1"}],
        supported_trust=["reputation"],
    )


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_store_agent_profile_requires_storage(mock_rep_cls, mock_id_cls):
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    with pytest.raises(IPFSStorageError):
        client.store_agent_profile(_make_profile())


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_store_agent_profile_uses_storage(mock_rep_cls, mock_id_cls):
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()
    storage = MagicMock(spec=IPFSStorage)
    storage.store_agent_profile.return_value = "ipfs://mock"

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
        ipfs_storage=storage,
    )

    profile = _make_profile()
    uri = client.store_agent_profile(profile, pin=False)
    assert uri == "ipfs://mock"
    storage.store_agent_profile.assert_called_once_with(profile, pin=False)


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_build_feedback_auth_requires_builder(mock_rep_cls, mock_id_cls):
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    with pytest.raises(SignatureError):
        client.build_feedback_auth(
            agent_id=1,
            client_address="0x" + "3" * 40,
            index_limit=1,
            expiry=1234,
            chain_id=1,
            identity_registry="0x" + "4" * 40,
        )


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_build_feedback_auth_uses_builder(mock_rep_cls, mock_id_cls):
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()
    builder = MagicMock(spec=AuthFeedback)
    payload = MagicMock()
    builder.build.return_value = payload

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
        auth_builder=builder,
    )

    result = client.build_feedback_auth(
        agent_id=1,
        client_address="0x" + "3" * 40,
        index_limit=1,
        expiry=1234,
        chain_id=1,
        identity_registry="0x" + "4" * 40,
    )
    assert result is payload
    builder.build.assert_called_once()


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_configure_auth_builder_from_key(mock_rep_cls, mock_id_cls):
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    builder = client.configure_auth_builder(private_key="0x" + "1" * 64)
    assert builder is client.auth_builder


@patch("erc8004_sdk.client.IdentityRegistryService")
@patch("erc8004_sdk.client.ReputationRegistryService")
def test_configure_ipfs_storage_from_kwargs(mock_rep_cls, mock_id_cls):
    mock_id_cls.return_value = MagicMock()
    mock_rep_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        identity_contract_address="0x" + "1" * 40,
        reputation_contract_address="0x" + "2" * 40,
    )

    storage = client.configure_ipfs_storage(ipfs_url="http://127.0.0.1:5001")
    assert storage is client.ipfs_storage
