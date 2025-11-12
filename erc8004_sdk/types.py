"""Type definitions and data models."""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Union


JsonDict = Dict[str, Any]


@dataclass
class ContractConfig:
    """Configuration required to initialise the contract service."""

    rpc_url: str
    contract_address: str
    contract_abi: Sequence[JsonDict]
    default_account: Optional[str] = None
    private_key: Optional[str] = None


MetadataValue = Union[str, bytes]
BytesLike = Union[str, bytes]


@dataclass
class MetadataEntry:
    """Metadata item supplied during registration."""

    key: str
    value: MetadataValue

    def to_contract_fields(self) -> Dict[str, bytes]:
        """Convert to the structure expected by the contract."""

        if isinstance(self.value, bytes):
            value_bytes = self.value
        else:
            if self.value.startswith("0x"):
                hex_body = self.value[2:]
                if len(hex_body) % 2 != 0:
                    hex_body = "0" + hex_body
                try:
                    value_bytes = bytes.fromhex(hex_body)
                except ValueError as err:  # pragma: no cover
                    raise ValueError(f"Unable to parse hexadecimal string: {self.value}") from err
            else:
                value_bytes = self.value.encode("utf-8")

        return {"key": self.key, "value": value_bytes}


@dataclass
class IdentityRegistrationArgs:
    """Arguments required to register an identity."""

    token_uri: str
    metadata: Sequence[Union[MetadataEntry, Mapping[str, MetadataValue]]] = ()
    gas_limit: int = 0
    value: int = 0


@dataclass
class IdentityRegistrationReceipt:
    """Wrapper for the registration transaction receipt."""

    raw_receipt: Dict[str, Any]
    agent_id: Optional[int]
    events: Sequence[Dict[str, Any]]


@dataclass
class IdentityRegistrationResult:
    """Result returned immediately after submitting a registration."""

    tx_hash: str
    agent_id: Optional[int]


@dataclass
class ReputationFeedbackArgs:
    """Arguments for submitting feedback."""

    agent_id: int
    score: int
    tag1: BytesLike
    tag2: BytesLike
    feedback_uri: str
    feedback_hash: BytesLike
    feedback_auth: BytesLike
    gas_limit: int = 0
    value: int = 0


@dataclass
class ReputationResponseArgs:
    """Arguments for appending a response to feedback."""

    agent_id: int
    client_address: str
    feedback_index: int
    response_uri: str
    response_hash: BytesLike
    gas_limit: int = 0
    value: int = 0


@dataclass
class ReputationRevokeFeedbackArgs:
    """Arguments for revoking feedback."""

    agent_id: int
    feedback_index: int
    gas_limit: int = 0
    value: int = 0

