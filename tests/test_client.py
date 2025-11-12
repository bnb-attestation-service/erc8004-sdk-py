from unittest.mock import MagicMock, patch

import pytest

from erc8004_sdk.client import ERC8004Client
from erc8004_sdk.exceptions import ContractInteractionError
from erc8004_sdk.types import RegistrationReceipt, RegistrationResult


@patch("erc8004_sdk.client.ContractService")
def test_register_agent_calls_service(mock_service_cls):
    service_instance = MagicMock()
    service_instance.register_agent.return_value = RegistrationResult(
        tx_hash="0xabc", agent_id=7
    )
    mock_service_cls.return_value = service_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    result = client.register_agent(
        token_uri="ipfs://abc", metadata=[{"key": "foo", "value": "bar"}]
    )
    assert result.tx_hash == "0xabc"
    assert result.agent_id == 7
    service_instance.register_agent.assert_called_once()


@patch("erc8004_sdk.client.ContractService")
def test_register_function_alias_rejects_legacy_params(mock_service_cls):
    mock_service_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    with pytest.raises(ContractInteractionError):
        client.register_function(
            function_selector="0x12345678", metadata_uri="ipfs://abc"
        )

    client.register_function(token_uri="ipfs://abc", metadata=[])
    mock_service_cls.return_value.register_agent.assert_called_once()


@patch("erc8004_sdk.client.ContractService")
def test_wait_for_receipt_returns_structured_data(mock_service_cls):
    service_instance = MagicMock()
    service_instance.wait_for_receipt.return_value = RegistrationReceipt(
        raw_receipt={"status": 1},
        agent_id=42,
        events=[{"event": "Registered"}],
    )
    mock_service_cls.return_value = service_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    result = client.wait_for_receipt("0xabc")
    assert result["agentId"] == 42
    assert result["receipt"]["status"] == 1
    assert result["events"] == [{"event": "Registered"}]


@patch("erc8004_sdk.client.ContractService")
def test_approve_delegates_to_service(mock_service_cls):
    service_instance = MagicMock()
    service_instance.approve.return_value = "0xapprove"
    mock_service_cls.return_value = service_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    tx_hash = client.approve(
        to_address="0x" + "4" * 40, token_id=1, gas_limit=100_000, value=0
    )

    assert tx_hash == "0xapprove"
    service_instance.approve.assert_called_once_with(
        "0x" + "4" * 40, 1, gas_limit=100_000, value=0
    )


@patch("erc8004_sdk.client.ContractService")
def test_set_approval_for_all_delegates_to_service(mock_service_cls):
    service_instance = MagicMock()
    service_instance.set_approval_for_all.return_value = "0xset"
    mock_service_cls.return_value = service_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    tx_hash = client.set_approval_for_all(
        operator="0x" + "5" * 40, approved=True, gas_limit=120_000
    )

    assert tx_hash == "0xset"
    service_instance.set_approval_for_all.assert_called_once_with(
        "0x" + "5" * 40, True, gas_limit=120_000, value=0
    )


@patch("erc8004_sdk.client.ContractService")
def test_get_approved_delegates_to_service(mock_service_cls):
    service_instance = MagicMock()
    service_instance.get_approved.return_value = "0xapproved"
    mock_service_cls.return_value = service_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    result = client.get_approved(1)

    assert result == "0xapproved"
    service_instance.get_approved.assert_called_once_with(1)


@patch("erc8004_sdk.client.ContractService")
def test_is_approved_for_all_delegates_to_service(mock_service_cls):
    service_instance = MagicMock()
    service_instance.is_approved_for_all.return_value = True
    mock_service_cls.return_value = service_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    result = client.is_approved_for_all("0x" + "6" * 40, "0x" + "7" * 40)

    assert result is True
    service_instance.is_approved_for_all.assert_called_once_with(
        "0x" + "6" * 40, "0x" + "7" * 40
    )


@patch("erc8004_sdk.client.ReputationRegistryService")
@patch("erc8004_sdk.client.ContractService")
def test_give_feedback_delegates_to_reputation(mock_contract_cls, mock_rep_cls):
    mock_contract_cls.return_value = MagicMock()
    rep_instance = MagicMock()
    rep_instance.give_feedback.return_value = "0xfeed"
    mock_rep_cls.return_value = rep_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
        reputation_contract_address="0x" + "4" * 40,
        reputation_contract_abi=[{}],
    )

    tx_hash = client.give_feedback(
        agent_id=1,
        score=5,
        tag1="tag1",
        tag2="tag2",
        feedback_uri="ipfs://feedback",
        feedback_hash="0x" + "aa" * 32,
        feedback_auth=b"\x00" * 65,
    )

    assert tx_hash == "0xfeed"
    rep_instance.give_feedback.assert_called_once()


@patch("erc8004_sdk.client.ReputationRegistryService")
@patch("erc8004_sdk.client.ContractService")
def test_append_response_delegates_to_reputation(mock_contract_cls, mock_rep_cls):
    mock_contract_cls.return_value = MagicMock()
    rep_instance = MagicMock()
    rep_instance.append_response.return_value = "0xresp"
    mock_rep_cls.return_value = rep_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
        reputation_contract_address="0x" + "4" * 40,
        reputation_contract_abi=[{}],
    )

    tx_hash = client.append_response(
        agent_id=1,
        client_address="0x" + "5" * 40,
        feedback_index=2,
        response_uri="ipfs://response",
        response_hash="0x" + "bb" * 32,
    )

    assert tx_hash == "0xresp"
    rep_instance.append_response.assert_called_once()


@patch("erc8004_sdk.client.ReputationRegistryService")
@patch("erc8004_sdk.client.ContractService")
def test_revoke_feedback_delegates_to_reputation(mock_contract_cls, mock_rep_cls):
    mock_contract_cls.return_value = MagicMock()
    rep_instance = MagicMock()
    rep_instance.revoke_feedback.return_value = "0xdead"
    mock_rep_cls.return_value = rep_instance

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
        reputation_contract_address="0x" + "4" * 40,
        reputation_contract_abi=[{}],
    )

    tx_hash = client.revoke_feedback(agent_id=1, feedback_index=3)

    assert tx_hash == "0xdead"
    rep_instance.revoke_feedback.assert_called_once()


@patch("erc8004_sdk.client.ContractService")
def test_reputation_service_required(mock_contract_cls):
    mock_contract_cls.return_value = MagicMock()

    client = ERC8004Client(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key="0x" + "3" * 64,
    )

    with pytest.raises(ContractInteractionError):
        client.give_feedback(
            agent_id=1,
            score=5,
            tag1="tag",
            tag2="tag",
            feedback_uri="ipfs://feedback",
            feedback_hash="0x" + "aa" * 32,
            feedback_auth=b"\x00" * 65,
        )

