"""Type definitions and data models."""

from dataclasses import dataclass, field
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


@dataclass
class FeedbackProofOfPayment:
    """Optional proof of payment payload that can be attached to feedback."""

    from_address: str
    to_address: str
    chain_id: str
    tx_hash: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "fromAddress": self.from_address,
            "toAddress": self.to_address,
            "chainId": self.chain_id,
            "txHash": self.tx_hash,
        }


@dataclass
class ReputationFeedbackRecord:
    """
    Structured record describing a feedback entry compliant with ERC-8004.

    Required fields mirror the MUST fields in the specification and optional
    properties can be provided via the dedicated attributes or the `extra` map.
    """

    agent_registry: str
    agent_id: int
    client_address: str
    created_at: str  # ISO-8601 timestamp string
    feedback_auth: str
    score: int

    tag1: Optional[str] = None
    tag2: Optional[str] = None
    skill: Optional[str] = None
    context: Optional[str] = None
    task: Optional[str] = None
    capability: Optional[str] = None  # prompts, resources, tools, completions
    name: Optional[str] = None  # Name of the MCP prompt/resource/tool
    proof_of_payment: Optional[FeedbackProofOfPayment] = None
    extra: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record into the JSON schema expected for feedback."""

        payload: Dict[str, Any] = {
            "agentRegistry": self.agent_registry,
            "agentId": self.agent_id,
            "clientAddress": self.client_address,
            "createdAt": self.created_at,
            "feedbackAuth": self.feedback_auth,
            "score": self.score,
        }

        optional_fields = {
            "tag1": self.tag1,
            "tag2": self.tag2,
            "skill": self.skill,
            "context": self.context,
            "task": self.task,
            "capability": self.capability,
            "name": self.name,
        }
        payload.update({k: v for k, v in optional_fields.items() if v is not None})

        if self.proof_of_payment:
            payload["proof_of_payment"] = self.proof_of_payment.to_dict()

        if self.extra:
            payload.update(dict(self.extra))

        return payload


@dataclass
class AgentEndpoint:
    """Endpoint information for an agent profile."""

    name: str
    endpoint: str
    version: Optional[str] = None
    capabilities: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serialisable dict."""

        data: Dict[str, Any] = {
            "name": self.name,
            "endpoint": self.endpoint,
        }
        if self.version:
            data["version"] = self.version
        if self.capabilities:
            data["capabilities"] = dict(self.capabilities)
        return data


@dataclass
class AgentRegistrationEntry:
    """Registration entry for an agent profile."""

    agent_id: int
    agent_registry: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serialisable dict."""

        return {
            "agentId": self.agent_id,
            "agentRegistry": self.agent_registry,
        }


@dataclass
class AgentProfile:
    """Structured data describing an agent for publication on IPFS."""
    name: str
    description: str
    image: Optional[str]
    endpoints: Sequence[Union[AgentEndpoint, Mapping[str, Any]]] = field(default_factory=list)
    registrations: Sequence[Union[AgentRegistrationEntry, Mapping[str, Any]]] = field(default_factory=list)
    supported_trust: Sequence[str] = field(default_factory=list)
    profile_type: str = "https://eips.ethereum.org/EIPS/eip-8004#registration-v1"
    additional_metadata: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to the JSON schema expected by ERC-8004."""

        data: Dict[str, Any] = {
            "type": self.profile_type,
            "name": self.name,
            "description": self.description,
            "supportedTrust": list(self.supported_trust),
        }
        if self.image:
            data["image"] = self.image

        data["endpoints"] = [self._coerce_endpoint(entry) for entry in self.endpoints]
        data["registrations"] = [
            self._coerce_registration(entry) for entry in self.registrations
        ]

        if self.additional_metadata:
            data.update(dict(self.additional_metadata))

        return data

    @staticmethod
    def _coerce_endpoint(entry: Union[AgentEndpoint, Mapping[str, Any]]) -> Dict[str, Any]:
        if isinstance(entry, AgentEndpoint):
            return entry.to_dict()
        return dict(entry)

    @staticmethod
    def _coerce_registration(
        entry: Union[AgentRegistrationEntry, Mapping[str, Any]]
    ) -> Dict[str, Any]:
        if isinstance(entry, AgentRegistrationEntry):
            return entry.to_dict()
        return dict(entry)
