"""Contract interaction utilities."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Optional, Sequence, Union

from eth_account import Account
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError, TransactionNotFound

from .exceptions import ContractInteractionError
from .types import (
    ContractConfig,
    ReputationFeedbackArgs,
    MetadataEntry,
    MetadataValue,
    ReputationRevokeFeedbackArgs,
    IdentityRegistrationArgs,
    IdentityRegistrationReceipt,
    IdentityRegistrationResult,
    ReputationResponseArgs,
)


class BaseContractService:
    """Base contract service providing shared transaction helpers."""

    def __init__(self, config: ContractConfig, *, enable_poa: bool = False) -> None:
        self._config = config
        self._web3 = Web3(Web3.HTTPProvider(config.rpc_url))
        if not self._web3.is_connected():
            raise ContractInteractionError("Failed to connect to the specified RPC endpoint.")

        if enable_poa:
            from web3.middleware import (  # Local import to avoid optional dependency
                geth_poa_middleware,
            )

            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self._contract = self._web3.eth.contract(
            address=Web3.to_checksum_address(config.contract_address),
            abi=config.contract_abi,
        )

        self._account = None
        if config.private_key:
            self._account = Account.from_key(config.private_key)
            if not config.default_account:
                self._config.default_account = self._account.address

        if not self._config.default_account:
            raise ContractInteractionError("A default account address or private key must be provided.")

        self._default_account = Web3.to_checksum_address(
            self._config.default_account
        )

    @property
    def web3(self) -> Web3:
        """Return underlying Web3 instance."""

        return self._web3

    @property
    def contract(self) -> Contract:
        """Return underlying contract instance."""

        return self._contract

    def as_dict(self) -> dict:
        """Return current configuration for debugging."""

        return asdict(self._config)

    def _build_tx_params(
        self,
        *,
        gas_limit: int,
        value: int,
        contract_fn,
    ) -> dict:
        """Build transaction params with nonce, gas and fee suggestions."""

        from_address = self._default_account
        nonce = self.web3.eth.get_transaction_count(
            from_address, block_identifier="pending"
        )

        # Use EIP-1559 style fee parameters recommended by the network
        tx_params = {
            "from": from_address,
            "nonce": nonce,
            "value": value,
        }

        try:
            fee_history = self.web3.eth.fee_history(1, "latest")
            max_priority_fee = fee_history["reward"][0][0]
            base_fee = fee_history["baseFeePerGas"][-1]
            max_fee_per_gas = base_fee + max_priority_fee * 2
            tx_params.update(
                {
                    "maxFeePerGas": max_fee_per_gas,
                    "maxPriorityFeePerGas": max_priority_fee,
                }
            )
        except Exception:  # pylint: disable=broad-except
            tx_params["gasPrice"] = self.web3.eth.gas_price

        if gas_limit > 0:
            tx_params["gas"] = gas_limit
        else:
            try:
                tx_params["gas"] = contract_fn.estimate_gas(
                    {
                        "from": from_address,
                        "value": value,
                    }
                )
            except ContractLogicError:
                # Fallback to a default gas limit if estimation fails
                tx_params["gas"] = 200_000

        return tx_params

    def _send_transaction(
        self, contract_fn, *, gas_limit: int = 0, value: int = 0
    ) -> str:
        """Sign and send a transaction, returning its hash."""

        try:
            tx = contract_fn.build_transaction(
                self._build_tx_params(
                    gas_limit=gas_limit, value=value, contract_fn=contract_fn
                )
            )
        except ContractLogicError as err:
            raise ContractInteractionError(f"Contract execution reverted: {err}") from err
        except ValueError as err:
            raise ContractInteractionError(f"Failed to build transaction: {err}") from err

        if self._account:
            signed = self._account.sign_transaction(tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        else:
            tx_hash = self.web3.eth.send_transaction(tx)

        tx_hex = tx_hash.hex()
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex


class IdentityRegistryService(BaseContractService):
    """High-level helper for interacting with ERC-8004 compatible identity registry contracts."""

    def register_agent(self, args: IdentityRegistrationArgs) -> IdentityRegistrationResult:
        """Call the contract `register` function."""

        metadata_payload = normalize_metadata_entries(args.metadata)
        contract_fn = self.contract.functions.register(
            args.token_uri, metadata_payload
        )
        agent_id = self._simulate_agent_id(contract_fn, value=args.value)

        tx_hash = self._send_transaction(
            contract_fn, gas_limit=args.gas_limit, value=args.value
        )
        return IdentityRegistrationResult(tx_hash=tx_hash, agent_id=agent_id)

    def register_minimal(
        self, *, gas_limit: int = 0, value: int = 0
    ) -> IdentityRegistrationResult:
        """Call the parameterless `register()` overload."""

        contract_fn = self.contract.functions.register()
        agent_id = self._simulate_agent_id(contract_fn, value=value)
        tx_hash = self._send_transaction(contract_fn, gas_limit=gas_limit, value=value)
        return IdentityRegistrationResult(tx_hash=tx_hash, agent_id=agent_id)

    def register_with_uri(
        self,
        token_uri: str,
        *,
        gas_limit: int = 0,
        value: int = 0,
    ) -> IdentityRegistrationResult:
        """Call the `register(string)` overload."""

        contract_fn = self.contract.functions.register(token_uri)
        agent_id = self._simulate_agent_id(contract_fn, value=value)
        tx_hash = self._send_transaction(contract_fn, gas_limit=gas_limit, value=value)
        return IdentityRegistrationResult(tx_hash=tx_hash, agent_id=agent_id)

    def set_agent_uri(
        self,
        *,
        agent_id: int,
        new_uri: str,
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Call `setAgentUri` to update the agent metadata URI."""

        contract_fn = self.contract.functions.setAgentUri(agent_id, new_uri)
        return self._send_transaction(contract_fn, gas_limit=gas_limit, value=value)

    def set_metadata(
        self,
        *,
        agent_id: int,
        key: str,
        value_bytes: Union[str, bytes, bytearray],
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Call `setMetadata` to update a metadata entry."""

        contract_fn = self.contract.functions.setMetadata(
            agent_id,
            key,
            _to_bytes_general(value_bytes),
        )
        return self._send_transaction(contract_fn, gas_limit=gas_limit, value=value)

    def approve(
        self, to_address: str, token_id: int, *, gas_limit: int = 0, value: int = 0
    ) -> str:
        """Call contract `approve(address,uint256)`."""

        contract_fn = self.contract.functions.approve(
            Web3.to_checksum_address(to_address), token_id
        )
        return self._send_transaction(
            contract_fn, gas_limit=gas_limit, value=value
        )

    def set_approval_for_all(
        self, operator: str, approved: bool, *, gas_limit: int = 0, value: int = 0
    ) -> str:
        """Call contract `setApprovalForAll(address,bool)`."""

        contract_fn = self.contract.functions.setApprovalForAll(
            Web3.to_checksum_address(operator), approved
        )
        return self._send_transaction(
            contract_fn, gas_limit=gas_limit, value=value
        )

    def get_approved(self, token_id: int) -> str:
        """Call `getApproved(uint256)` and return the approved address."""

        try:
            return self.contract.functions.getApproved(token_id).call()
        except ContractLogicError as err:
            raise ContractInteractionError(f"Failed to query approval information: {err}") from err

    def is_approved_for_all(self, owner: str, operator: str) -> bool:
        """Call `isApprovedForAll(address,address)` and return the approval status."""

        try:
            return self.contract.functions.isApprovedForAll(
                Web3.to_checksum_address(owner),
                Web3.to_checksum_address(operator),
            ).call()
        except ContractLogicError as err:
            raise ContractInteractionError(f"Failed to query approval status: {err}") from err

    def wait_for_receipt(
        self, tx_hash: str, *, timeout: Optional[int] = 120
    ) -> IdentityRegistrationReceipt:
        """Wait for the transaction receipt and decode registration events."""

        try:
            receipt = self.web3.eth.wait_for_transaction_receipt(
                tx_hash, timeout=timeout
            )
        except TransactionNotFound as err:
            raise ContractInteractionError(f"Transaction not found: {tx_hash}") from err

        return self._decode_registration_receipt(receipt)

    def _decode_registration_receipt(
        self, receipt: Any
    ) -> IdentityRegistrationReceipt:
        """Decode the registration receipt and extract the agentId."""

        raw_receipt = dict(receipt)
        agent_id: Optional[int] = None
        events: Sequence[Dict[str, Any]] = ()

        try:
            event_abi = getattr(self.contract.events, "Registered", None)
            if event_abi is not None:
                decoded_logs = event_abi().process_receipt(receipt)
                events = [
                    {
                        "event": log.event,
                        "args": dict(log.args),
                        "transactionHash": log.transactionHash.hex(),
                        "logIndex": log.logIndex,
                    }
                    for log in decoded_logs
                ]
                if decoded_logs:
                    first_log = decoded_logs[0]
                    if "agentId" in first_log.args:
                        agent_id = int(first_log.args["agentId"])
        except Exception:  # pylint: disable=broad-except
            events = ()

        return IdentityRegistrationReceipt(
            raw_receipt=raw_receipt, agent_id=agent_id, events=events
        )

    def _simulate_agent_id(self, contract_fn, *, value: int) -> Optional[int]:
        """Attempt to execute a static call to obtain the agentId, if available."""

        try:
            raw_agent_id = contract_fn.call(
                {
                    "from": self._default_account,
                    "value": value,
                }
            )
            if raw_agent_id is not None:
                return int(raw_agent_id)
        except ContractLogicError:
            return None
        return None


class ReputationRegistryService(BaseContractService):
    """Interact with a reputation registry contract."""

    def __init__(self, config: ContractConfig, *, enable_poa: bool = False) -> None:
        super().__init__(config, enable_poa=enable_poa)

    def give_feedback(self, args: ReputationFeedbackArgs) -> str:
        """Call `giveFeedback` on the registry."""

        contract_fn = self.contract.functions.giveFeedback(
            args.agent_id,
            args.score,
            self._coerce_bytes32(args.tag1),
            self._coerce_bytes32(args.tag2),
            args.feedback_uri,
            self._coerce_bytes32(args.feedback_hash),
            _to_bytes_general(args.feedback_auth),
        )
        return self._send_transaction(
            contract_fn,
            gas_limit=args.gas_limit,
            value=args.value,
        )

    def append_response(self, args: ReputationResponseArgs) -> str:
        """Call `appendResponse` on the registry."""

        contract_fn = self.contract.functions.appendResponse(
            args.agent_id,
            Web3.to_checksum_address(args.client_address),
            args.feedback_index,
            args.response_uri,
            self._coerce_bytes32(args.response_hash),
        )
        return self._send_transaction(
            contract_fn,
            gas_limit=args.gas_limit,
            value=args.value,
        )

    def revoke_feedback(self, args: ReputationRevokeFeedbackArgs) -> str:
        """Call `revokeFeedback` on the registry."""

        contract_fn = self.contract.functions.revokeFeedback(
            args.agent_id,
            args.feedback_index,
        )
        return self._send_transaction(
            contract_fn,
            gas_limit=args.gas_limit,
            value=args.value,
        )

    @staticmethod
    def _coerce_bytes32(value) -> bytes:
        """Convert an input into bytes32."""

        raw = _to_bytes_general(value)
        if len(raw) > 32:
            raise ContractInteractionError("bytes32 values cannot exceed 32 bytes.")
        return raw.ljust(32, b"\x00")


def normalize_metadata_entries(
    metadata: Sequence[Union[MetadataEntry, Mapping[str, MetadataValue]]]
) -> Sequence[Mapping[str, bytes]]:
    """Standardize metadata into the contract-required format."""

    normalized = []
    for entry in metadata:
        if isinstance(entry, MetadataEntry):
            key = entry.key
            value = entry.value
        else:
            if "key" not in entry or "value" not in entry:
                raise ContractInteractionError("Metadata entries must include both `key` and `value`.")
            key = entry["key"]
            value = entry["value"]

        if not isinstance(key, str):
            raise ContractInteractionError("metadata.key must be a string.")
        value_bytes = _to_bytes(value)
        normalized.append({"key": key, "value": value_bytes})

    return normalized


def _to_bytes(value: MetadataValue) -> bytes:
    """Convert the metadata value to bytes."""

    try:
        return _to_bytes_general(value)
    except ContractInteractionError as err:
        raise ContractInteractionError("metadata.value must be bytes or str.") from err


def _to_bytes_general(value: Union[str, bytes, bytearray]) -> bytes:
    """Convert common string/bytes inputs into raw bytes."""

    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("0x"):
            try:
                return Web3.to_bytes(hexstr=value)
            except ValueError as err:
                raise ContractInteractionError(f"Invalid hexadecimal string: {value}") from err
        return value.encode("utf-8")
    raise ContractInteractionError("Expected bytes-like value.")
