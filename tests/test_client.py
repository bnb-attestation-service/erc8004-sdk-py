"""Tests for the ERC8004Client."""

from unittest.mock import MagicMock, patch

import pytest

from erc8004_sdk.client import ERC8004Client
from erc8004_sdk.exceptions import ContractInteractionError
from erc8004_sdk.types import (
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
