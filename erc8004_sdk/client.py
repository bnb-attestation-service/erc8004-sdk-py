"""Public SDK interface."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union

from .abi import IDENTITY_REGISTRY_ABI, REPUTATION_REGISTRY_ABI
from .contract import IdentityRegistryService, ReputationRegistryService
from .exceptions import ContractInteractionError
from .types import (
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

    @property
    def contract_address(self) -> str:
        """Return current contract address."""
        return self._identity_registry_service.contract.address

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



