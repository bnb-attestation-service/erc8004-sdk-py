from types import SimpleNamespace
from unittest.mock import MagicMock

from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import ContractLogicError

from erc8004_sdk.contract import IdentityRegistryService
from erc8004_sdk.exceptions import ContractInteractionError
from erc8004_sdk.types import (
    IdentityRegistrationReceipt,
    IdentityRegistrationResult,
)


def _make_service_with_event(logs):
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    registered_event = MagicMock()
    registered_event.process_receipt.return_value = logs
    service._contract.events = MagicMock()
    service._contract.events.Registered = MagicMock(return_value=registered_event)
    return service


def test_decode_registration_receipt_extracts_agent_id():
    log = SimpleNamespace(
        event="Registered",
        args={"agentId": 99, "owner": "0xabc"},
        transactionHash=HexBytes("0x01"),
        logIndex=0,
    )
    service = _make_service_with_event([log])

    receipt = service._decode_registration_receipt({"status": 1})

    assert isinstance(receipt, IdentityRegistrationReceipt)
    assert receipt.agent_id == 99
    assert receipt.events[0]["event"] == "Registered"
    assert receipt.events[0]["args"]["owner"] == "0xabc"


def test_decode_registration_receipt_handles_missing_events():
    service = _make_service_with_event([])

    receipt = service._decode_registration_receipt({"status": 1})

    assert receipt.agent_id is None
    assert receipt.events == []


def test_register_agent_returns_result_with_agent_id():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.return_value = 7
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.register.return_value = fn_mock

    eth_mock = MagicMock()
    eth_mock.get_transaction_count.return_value = 1
    eth_mock.fee_history.return_value = {"reward": [[1]], "baseFeePerGas": [1]}
    eth_mock.send_transaction.return_value = HexBytes("0xaaa")
    service._web3 = MagicMock()
    service._web3.eth = eth_mock
    service._default_account = Web3.to_checksum_address("0x" + "3" * 40)
    service._account = None

    args = MagicMock()
    args.token_uri = "ipfs://abc"
    args.metadata = []
    args.gas_limit = 0
    args.value = 0

    result = service.register_agent(args)

    assert isinstance(result, IdentityRegistrationResult)
    assert result.tx_hash == Web3.to_hex(HexBytes("0xaaa"))
    assert result.agent_id == 7
    fn_mock.call.assert_called_once()
    fn_mock.build_transaction.assert_called_once()
    eth_mock.send_transaction.assert_called_once()


def test_register_agent_handles_call_failure():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.side_effect = ContractLogicError("reverted")
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.register.return_value = fn_mock

    eth_mock = MagicMock()
    eth_mock.get_transaction_count.return_value = 1
    eth_mock.fee_history.return_value = {"reward": [[1]], "baseFeePerGas": [1]}
    eth_mock.send_transaction.return_value = HexBytes("0xbbb")
    service._web3 = MagicMock()
    service._web3.eth = eth_mock
    service._default_account = Web3.to_checksum_address("0x" + "3" * 40)
    service._account = None

    args = MagicMock()
    args.token_uri = "ipfs://abc"
    args.metadata = []
    args.gas_limit = 0
    args.value = 0

    result = service.register_agent(args)

    assert result.agent_id is None
    assert result.tx_hash == Web3.to_hex(HexBytes("0xbbb"))
    fn_mock.call.assert_called_once()
    eth_mock.send_transaction.assert_called_once()


def test_register_minimal_uses_parameterless_overload():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.return_value = 8
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.register.return_value = fn_mock
    service._web3 = MagicMock()
    service._web3.eth = SimpleNamespace(
        get_transaction_count=MagicMock(return_value=1),
        fee_history=MagicMock(return_value={"reward": [[1]], "baseFeePerGas": [1]}),
        send_transaction=MagicMock(return_value=HexBytes("0xcafebabe")),
    )
    service._default_account = Web3.to_checksum_address("0x" + "4" * 40)
    service._account = None

    result = service.register_minimal()

    assert result.agent_id == 8
    assert result.tx_hash == Web3.to_hex(HexBytes("0xcafebabe"))
    service._contract.functions.register.assert_called_once_with()


def test_register_with_uri_calls_string_overload():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.return_value = 12
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.register.return_value = fn_mock
    service._web3 = MagicMock()
    service._web3.eth = SimpleNamespace(
        get_transaction_count=MagicMock(return_value=1),
        fee_history=MagicMock(return_value={"reward": [[1]], "baseFeePerGas": [1]}),
        send_transaction=MagicMock(return_value=HexBytes("0xc0ffee")),
    )
    service._default_account = Web3.to_checksum_address("0x" + "5" * 40)
    service._account = None

    result = service.register_with_uri("ipfs://uri")

    assert result.agent_id == 12
    service._contract.functions.register.assert_called_once_with("ipfs://uri")


def test_set_agent_uri_builds_transaction():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.setAgentUri.return_value = fn_mock
    service._web3 = MagicMock()
    service._web3.eth = SimpleNamespace(
        get_transaction_count=MagicMock(return_value=1),
        fee_history=MagicMock(return_value={"reward": [[1]], "baseFeePerGas": [1]}),
        send_transaction=MagicMock(return_value=HexBytes("0xaa")),
    )
    service._default_account = Web3.to_checksum_address("0x" + "6" * 40)
    service._account = None

    tx_hash = service.set_agent_uri(agent_id=1, new_uri="ipfs://new")

    assert tx_hash == Web3.to_hex(HexBytes("0xaa"))
    service._contract.functions.setAgentUri.assert_called_once_with(1, "ipfs://new")


def test_set_metadata_builds_transaction_bytes_conversion():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.setMetadata.return_value = fn_mock
    service._web3 = MagicMock()
    service._web3.eth = SimpleNamespace(
        get_transaction_count=MagicMock(return_value=1),
        fee_history=MagicMock(return_value={"reward": [[1]], "baseFeePerGas": [1]}),
        send_transaction=MagicMock(return_value=HexBytes("0xbb")),
    )
    service._default_account = Web3.to_checksum_address("0x" + "7" * 40)
    service._account = None

    tx_hash = service.set_metadata(
        agent_id=1,
        key="role",
        value_bytes="0x1234",
    )

    assert tx_hash == Web3.to_hex(HexBytes("0xbb"))
    service._contract.functions.setMetadata.assert_called_once()
def test_get_approved_returns_address():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.return_value = "0x" + "1" * 40
    service._contract.functions.getApproved.return_value = fn_mock

    result = service.get_approved(1)

    assert result == "0x" + "1" * 40
    service._contract.functions.getApproved.assert_called_once_with(1)


def test_get_approved_raises_on_logic_error():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.side_effect = ContractLogicError("reverted")
    service._contract.functions.getApproved.return_value = fn_mock

    try:
        service.get_approved(1)
    except ContractInteractionError as err:
        assert "Failed to query approval information" in str(err)
    else:
        assert False, "should raise"


def test_is_approved_for_all_returns_bool():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.call.return_value = True
    service._contract.functions.isApprovedForAll.return_value = fn_mock

    owner = "0x" + "1" * 40
    operator = "0x" + "2" * 40
    result = service.is_approved_for_all(owner, operator)

    assert result is True
    service._contract.functions.isApprovedForAll.assert_called_once_with(
        Web3.to_checksum_address(owner), Web3.to_checksum_address(operator)
    )


def test_approve_builds_and_sends_transaction():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.approve.return_value = fn_mock

    eth_mock = MagicMock()
    eth_mock.get_transaction_count.return_value = 1
    eth_mock.fee_history.return_value = {"reward": [[1]], "baseFeePerGas": [1]}
    eth_mock.send_transaction.return_value = HexBytes("0xabc")
    service._web3 = MagicMock()
    service._web3.eth = eth_mock
    service._default_account = Web3.to_checksum_address("0x" + "3" * 40)
    service._account = None

    tx_hash = service.approve("0x" + "4" * 40, 1)

    assert tx_hash == Web3.to_hex(HexBytes("0xabc"))
    fn_mock.build_transaction.assert_called_once()
    eth_mock.send_transaction.assert_called_once()


def test_set_approval_for_all_builds_and_sends_transaction():
    service = IdentityRegistryService.__new__(IdentityRegistryService)
    service._contract = MagicMock()
    fn_mock = MagicMock()
    fn_mock.estimate_gas.return_value = 21000
    fn_mock.build_transaction.return_value = {"nonce": 1}
    service._contract.functions.setApprovalForAll.return_value = fn_mock

    eth_mock = MagicMock()
    eth_mock.get_transaction_count.return_value = 1
    eth_mock.fee_history.return_value = {"reward": [[1]], "baseFeePerGas": [1]}
    eth_mock.send_transaction.return_value = HexBytes("0xdef")
    service._web3 = MagicMock()
    service._web3.eth = eth_mock
    service._default_account = Web3.to_checksum_address("0x" + "3" * 40)
    service._account = None

    tx_hash = service.set_approval_for_all("0x" + "5" * 40, True)

    assert tx_hash == Web3.to_hex(HexBytes("0xdef"))
    fn_mock.build_transaction.assert_called_once()
    eth_mock.send_transaction.assert_called_once()

