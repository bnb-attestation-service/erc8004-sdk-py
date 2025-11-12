"""Public SDK interface."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Union

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
        default_account: Optional[str] = None,
        private_key: Optional[str] = None,
        identity_contract_address: Optional[str] = None,
        identity_contract_abi: Optional[Sequence[Dict[str, Any]]] = None,
        enable_poa: bool = False,
        reputation_contract_address: Optional[str] = None,
        reputation_contract_abi: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        if not identity_contract_address or not identity_contract_abi:
            raise ContractInteractionError(
                "identity_contract_address and identity_contract_abi must be provided."
            )
        if not reputation_contract_address or not reputation_contract_abi:
            raise ContractInteractionError(
                "reputation_contract_address and reputation_contract_abi must be provided."
            )

        identity_registry_config = ContractConfig(
            rpc_url=rpc_url,
            contract_address=identity_contract_address,
            contract_abi=identity_contract_abi,
            default_account=default_account,
            private_key=private_key,
        )
        self._identity_registry_service = IdentityRegistryService(identity_registry_config, enable_poa=enable_poa)

        reputation_registry_config = ContractConfig(
            rpc_url=rpc_url,
            contract_address=reputation_contract_address,
            contract_abi=reputation_contract_abi,
            default_account=default_account,
            private_key=private_key,
        )
        self._reputation_registry_service = ReputationRegistryService(reputation_registry_config, enable_poa=enable_poa)

    @property
    def contract_address(self) -> str:
        """Return current contract address."""
        return self._identity_registry_service.contract.address

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

    def register_function(self, **kwargs: Any) -> IdentityRegistrationResult:
        """Backward-compatible alias that forwards to `register_agent`."""

        if "function_selector" in kwargs or "metadata_uri" in kwargs:
            raise ContractInteractionError(
                "Contract interface has changed; please use register_agent(token_uri=..., metadata=...)."
            )
        return self.register_agent(**kwargs)

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



