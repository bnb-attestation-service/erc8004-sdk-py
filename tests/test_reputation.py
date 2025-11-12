from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from web3 import Web3

from erc8004_sdk.exceptions import ContractInteractionError
from erc8004_sdk.contract import ReputationRegistryService
from erc8004_sdk.types import ContractConfig, FeedbackArgs, RevokeFeedbackArgs, ResponseArgs


def _make_service() -> ReputationRegistryService:
    config = ContractConfig(
        rpc_url="http://localhost:8545",
        contract_address="0x" + "1" * 40,
        contract_abi=[],
        default_account="0x" + "2" * 40,
        private_key=None,
    )
    service = ReputationRegistryService.__new__(ReputationRegistryService)
    service._config = config
    service._web3 = SimpleNamespace(
        eth=SimpleNamespace(
            get_transaction_count=MagicMock(return_value=1),
            fee_history=MagicMock(return_value={"reward": [[1]], "baseFeePerGas": [1]}),
            gas_price=MagicMock(return_value=1),
            send_transaction=MagicMock(return_value=HexBytes("0xabc")),
        )
    )
    service._contract = MagicMock()
    service._account = None
    service._default_account = to_checksum_address(config.default_account)  # type: ignore[arg-type]
    return service


def test_give_feedback_builds_transaction(monkeypatch):
    service = _make_service()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.giveFeedback.return_value = fn_mock

    args = FeedbackArgs(
        agent_id=1,
        score=9,
        tag1="tag-1",
        tag2="0x" + "ab" * 32,
        feedback_uri="ipfs://feedback",
        feedback_hash=b"\x00" * 32,
        feedback_auth=b"\x01" * 65,
    )

    tx_hash = service.give_feedback(args)

    assert tx_hash == Web3.to_hex(HexBytes("0xabc"))
    fn_mock.build_transaction.assert_called_once()
    service._contract.functions.giveFeedback.assert_called_once()


def test_append_response_builds_transaction():
    service = _make_service()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.appendResponse.return_value = fn_mock

    args = ResponseArgs(
        agent_id=1,
        client_address="0x" + "3" * 40,
        feedback_index=5,
        response_uri="ipfs://response",
        response_hash="0x" + "cd" * 32,
    )

    tx_hash = service.append_response(args)

    assert tx_hash == Web3.to_hex(HexBytes("0xabc"))
    service._contract.functions.appendResponse.assert_called_once()


def test_revoke_feedback_builds_transaction():
    service = _make_service()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.revokeFeedback.return_value = fn_mock

    args = RevokeFeedbackArgs(agent_id=1, feedback_index=2)

    tx_hash = service.revoke_feedback(args)

    assert tx_hash == Web3.to_hex(HexBytes("0xabc"))
    service._contract.functions.revokeFeedback.assert_called_once()


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0x" + "12" * 16, bytes.fromhex("12" * 16) + b"\x00" * 16),
        ("tag", b"tag" + b"\x00" * 29),
        (b"raw", b"raw" + b"\x00" * 29),
    ],
)
def test_coerce_bytes32(value, expected):
    assert ReputationRegistryService._coerce_bytes32(value) == expected


def test_coerce_bytes32_rejects_long_values():
    with pytest.raises(ContractInteractionError):
        ReputationRegistryService._coerce_bytes32(b"a" * 33)

