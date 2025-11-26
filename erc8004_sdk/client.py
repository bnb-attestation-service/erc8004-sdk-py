"""Public SDK interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Union

from .abi import IDENTITY_REGISTRY_ABI, REPUTATION_REGISTRY_ABI
from .contract import IdentityRegistryService, ReputationRegistryService
from .exceptions import ContractInteractionError, IPFSStorageError, SignatureError
from .signer import AuthFeedback, FeedbackAuthPayload
from .storage import IPFSStorage
from .types import (
    AgentProfile,
    ContractConfig,
    ReputationFeedbackArgs,
    MetadataEntry,
    MetadataValue,
    ReputationRevokeFeedbackArgs,
    IdentityRegistrationArgs,
    IdentityRegistrationResult,
    ReputationResponseArgs,
)


class ERC8004Client:
    """User-facing high-level façade."""
    def __init__(
        self,
        *,
        rpc_url: str,
        identity_contract_address: str,
        reputation_contract_address: str,
        default_account: Optional[str] = None,
        private_key: Optional[str] = None,
        enable_poa: bool = False,
        ipfs_storage: Optional[IPFSStorage] = None,
        ipfs_config: Optional[Mapping[str, Any]] = None,
        auth_builder: Optional[AuthFeedback] = None,
        auth_private_key: Optional[str] = None,
    ) -> None:
        if not identity_contract_address:
            raise ContractInteractionError(
                "identity_contract_address must be provided."
            )
        if not reputation_contract_address:
            raise ContractInteractionError(
                "reputation_contract_address must be provided."
            )

        identity_registry_config = ContractConfig(
            rpc_url=rpc_url,
            contract_address=identity_contract_address,
            contract_abi=IDENTITY_REGISTRY_ABI,
            default_account=default_account,
            private_key=private_key,
        )
        self._identity_registry_service = IdentityRegistryService(identity_registry_config, enable_poa=enable_poa)

        reputation_registry_config = ContractConfig(
            rpc_url=rpc_url,
            contract_address=reputation_contract_address,
            contract_abi=REPUTATION_REGISTRY_ABI,
            default_account=default_account,
            private_key=private_key,
        )
        self._reputation_registry_service = ReputationRegistryService(reputation_registry_config, enable_poa=enable_poa)

        self._ipfs_storage = ipfs_storage or (
            IPFSStorage(**dict(ipfs_config)) if ipfs_config else None
        )

        # Prefer an explicitly supplied AuthFeedback instance, then an explicit
        # auth_private_key, and finally fall back to the client's private_key
        # so that basic usage only requires one key argument.
        effective_auth_key = auth_private_key or private_key
        self._auth_builder = auth_builder or (
            AuthFeedback(private_key=effective_auth_key)
            if effective_auth_key
            else None
        )

    @property
    def contract_address(self) -> str:
        """Return current contract address."""
        return self._identity_registry_service.contract.address

    @property
    def ipfs_storage(self) -> Optional[IPFSStorage]:
        """Return the configured IPFS storage helper, if any."""

        return self._ipfs_storage

    @property
    def auth_builder(self) -> Optional[AuthFeedback]:
        """Return the configured feedback authorization builder, if any."""

        return self._auth_builder

    # Helper configuration -----------------------------------------------------

    def configure_ipfs_storage(
        self,
        *,
        storage: Optional[IPFSStorage] = None,
        config: Optional[Mapping[str, Any]] = None,
        **storage_kwargs: Any,
    ) -> IPFSStorage:
        """
        Configure or replace the IPFS storage helper.

        Provide either an existing IPFSStorage instance, a config mapping, or
        direct keyword arguments accepted by IPFSStorage.
        """

        if storage is not None:
            self._ipfs_storage = storage
        elif config is not None:
            self._ipfs_storage = IPFSStorage(**dict(config))
        elif storage_kwargs:
            self._ipfs_storage = IPFSStorage(**storage_kwargs)
        elif self._ipfs_storage is None:
            raise IPFSStorageError(
                "IPFS storage is not configured. Provide a storage instance or"
                " configuration values."
            )
        return self._ipfs_storage

    def configure_auth_builder(
        self,
        *,
        builder: Optional[AuthFeedback] = None,
        private_key: Optional[str] = None,
    ) -> AuthFeedback:
        """
        Configure the feedback authorization builder.

        Provide either an AuthFeedback instance or the private key used for
        producing signatures.
        """

        if builder is not None:
            self._auth_builder = builder
        elif private_key:
            self._auth_builder = AuthFeedback(private_key=private_key)
        elif self._auth_builder is None:
            raise SignatureError(
                "Auth builder is not configured. Provide a builder or a"
                " private key."
            )
        return self._auth_builder

    # Storage helpers ----------------------------------------------------------

    def store_agent_profile(
        self,
        profile: AgentProfile,
        *,
        pin: bool = True,
    ) -> str:
        """Store an AgentProfile document via the configured IPFS storage."""

        storage = self._ensure_ipfs_storage()
        return storage.store_agent_profile(profile, pin=pin)

    def store_json(self, data: Dict[str, Any], *, pin: bool = True) -> str:
        """Store an arbitrary JSON document via the configured IPFS storage."""

        storage = self._ensure_ipfs_storage()
        return storage.store_json(data, pin=pin)

    def store_file(
        self,
        file_path: Union[str, Path],
        *,
        pin: bool = True,
    ) -> str:
        """Store a local file via the configured IPFS storage."""

        storage = self._ensure_ipfs_storage()
        return storage.store_file(file_path, pin=pin)

    # Feedback helpers ---------------------------------------------------------

    def build_feedback_auth(
        self,
        *,
        agent_id: int,
        client_address: str,
        index_limit: int,
        expiry: int,
        chain_id: int,
        identity_registry: str,
        signer_address: Optional[str] = None,
    ) -> FeedbackAuthPayload:
        """Construct a feedback authorization payload using the configured builder."""

        builder = self._ensure_auth_builder()
        return builder.build(
            agent_id=agent_id,
            client_address=client_address,
            index_limit=index_limit,
            expiry=expiry,
            chain_id=chain_id,
            identity_registry=identity_registry,
            signer_address=signer_address,
        )

    def register_minimal(
        self,
        *,
        gas_limit: int = 0,
        value: int = 0,
    ) -> IdentityRegistrationResult:
        """Register an agent with no parameters (empty agent)."""

        return self._identity_registry_service.register_minimal(
            gas_limit=gas_limit, value=value
        )

    def register_agent(
        self,
        *,
        token_uri: str,
        metadata: Optional[
            Sequence[Union[MetadataEntry, Mapping[str, MetadataValue]]]
        ] = None,
        gas_limit: int = 0,
        value: int = 0,
    ) -> IdentityRegistrationResult:
        """Register identity information through the contract."""

        args = IdentityRegistrationArgs(
            token_uri=token_uri,
            metadata=metadata or (),
            gas_limit=gas_limit,
            value=value,
        )
        return self._identity_registry_service.register_agent(args)

    def register_with_uri(
        self,
        token_uri: str,
        *,
        gas_limit: int = 0,
        value: int = 0,
    ) -> IdentityRegistrationResult:
        """Register an agent with only a token URI."""

        return self._identity_registry_service.register_with_uri(
            token_uri, gas_limit=gas_limit, value=value
        )

    def set_agent_uri(
        self,
        *,
        agent_id: int,
        new_uri: str,
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Update the token URI for an agent."""

        return self._identity_registry_service.set_agent_uri(
            agent_id=agent_id,
            new_uri=new_uri,
            gas_limit=gas_limit,
            value=value,
        )

    def set_metadata(
        self,
        *,
        agent_id: int,
        key: str,
        value: Union[str, bytes],
        gas_limit: int = 0,
        value_amount: int = 0,
    ) -> str:
        """Update a metadata entry for an agent."""

        return self._identity_registry_service.set_metadata(
            agent_id=agent_id,
            key=key,
            value_bytes=value,
            gas_limit=gas_limit,
            value=value_amount,
        )

    def approve(
        self,
        *,
        to_address: str,
        token_id: int,
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Call the contract `approve` function."""

        return self._identity_registry_service.approve(
            to_address, token_id, gas_limit=gas_limit, value=value
        )

    def set_approval_for_all(
        self,
        *,
        operator: str,
        approved: bool,
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Call the contract `setApprovalForAll` function."""

        return self._identity_registry_service.set_approval_for_all(
            operator, approved, gas_limit=gas_limit, value=value
        )

    def get_approved(self, token_id: int) -> str:
        """Return the approved address for the specified token."""

        return self._identity_registry_service.get_approved(token_id)

    def is_approved_for_all(self, owner: str, operator: str) -> bool:
        """Return whether the operator is approved for all tokens."""

        return self._identity_registry_service.is_approved_for_all(owner, operator)

    def wait_for_receipt(self, tx_hash: str, *, timeout: int = 120) -> Dict[str, Any]:
        """Wait for inclusion and return receipt details including agentId."""

        receipt = self._identity_registry_service.wait_for_receipt(
            tx_hash, timeout=timeout
        )
        return {
            "agentId": receipt.agent_id,
            "receipt": receipt.raw_receipt,
            "events": receipt.events,
        }

    # Reputation registry helpers -------------------------------------------------

    def give_feedback(
        self,
        *,
        agent_id: int,
        score: int,
        tag1: Union[str, bytes],
        tag2: Union[str, bytes],
        feedback_uri: str,
        feedback_hash: Union[str, bytes],
        feedback_auth: Union[str, bytes],
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Submit feedback to the reputation registry."""

        args = ReputationFeedbackArgs(
            agent_id=agent_id,
            score=score,
            tag1=tag1,
            tag2=tag2,
            feedback_uri=feedback_uri,
            feedback_hash=feedback_hash,
            feedback_auth=feedback_auth,
            gas_limit=gas_limit,
            value=value,
        )
        return self._reputation_registry_service.give_feedback(args)

    def append_response(
        self,
        *,
        agent_id: int,
        client_address: str,
        feedback_index: int,
        response_uri: str,
        response_hash: Union[str, bytes],
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Append a response to existing feedback."""

        args = ReputationResponseArgs(
            agent_id=agent_id,
            client_address=client_address,
            feedback_index=feedback_index,
            response_uri=response_uri,
            response_hash=response_hash,
            gas_limit=gas_limit,
            value=value,
        )
        return self._reputation_registry_service.append_response(args)

    def revoke_feedback(
        self,
        *,
        agent_id: int,
        feedback_index: int,
        gas_limit: int = 0,
        value: int = 0,
    ) -> str:
        """Revoke previously submitted feedback."""

        args = ReputationRevokeFeedbackArgs(
            agent_id=agent_id,
            feedback_index=feedback_index,
            gas_limit=gas_limit,
        )
        return self._reputation_registry_service.revoke_feedback(args)

    def get_last_index(self, agent_id: int, client_address: str) -> int:
        """Return the most recent feedback index for a given client."""

        return self._reputation_registry_service.get_last_index(
            agent_id, client_address
        )

    # Internal helpers ---------------------------------------------------------

    def _ensure_ipfs_storage(self) -> IPFSStorage:
        if self._ipfs_storage is None:
            raise IPFSStorageError(
                "IPFS storage is not configured. Pass `ipfs_storage`, provide"
                " `ipfs_config`, or call `configure_ipfs_storage()` before"
                " using storage helpers."
            )
        return self._ipfs_storage

    def _ensure_auth_builder(self) -> AuthFeedback:
        if self._auth_builder is None:
            raise SignatureError(
                "Auth builder is not configured. Pass `auth_builder`, provide"
                " `auth_private_key`, or call `configure_auth_builder()` before"
                " building feedback authorization payloads."
            )
        return self._auth_builder


# todo: add sign feedback auth