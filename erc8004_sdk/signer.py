"""Signing utilities tailored for feedback authorization."""

from __future__ import annotations

import binascii
from dataclasses import dataclass
from typing import Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_abi import encode as abi_encode
from eth_utils import keccak
from web3 import Web3

from .exceptions import SignatureError


ABI_TYPES = (
    "uint256",
    "address",
    "uint64",
    "uint256",
    "uint256",
    "address",
    "address",
)


@dataclass(frozen=True)
class FeedbackAuthPayload:
    """Feedback authorization payload returned by AuthFeedback."""

    agent_id: int
    client_address: str
    index_limit: int
    expiry: int
    chain_id: int
    identity_registry: str
    signer_address: str
    signature: bytes

    @property
    def encoded(self) -> bytes:
        """Return the ABI-encoded struct followed by the signature bytes."""

        struct_bytes = abi_encode(
            ABI_TYPES,
            (
                self.agent_id,
                Web3.to_checksum_address(self.client_address),
                self.index_limit,
                self.expiry,
                self.chain_id,
                Web3.to_checksum_address(self.identity_registry),
                Web3.to_checksum_address(self.signer_address),
            ),
        )
        return struct_bytes + self.signature

    def hex(self) -> str:
        """Return the payload as a hex string."""

        return "0x" + binascii.hexlify(self.encoded).decode()


class AuthFeedback:
    """Build the `feedbackAuth` bytes required by `_verifyFeedbackAuth`."""

    def __init__(self, *, private_key: str) -> None:
        if not private_key:
            raise SignatureError("A private key is required.")
        try:
            self._account = Account.from_key(private_key)
        except ValueError as err:
            raise SignatureError(f"Invalid private key: {err}") from err

    @property
    def signer_address(self) -> str:
        """Return the address backing the signer."""

        return self._account.address

    def build(
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
        """Construct a feedback authorization payload."""

        signer = Web3.to_checksum_address(signer_address or self.signer_address)
        client = Web3.to_checksum_address(client_address)
        registry = Web3.to_checksum_address(identity_registry)

        struct_bytes = abi_encode(
            ABI_TYPES,
            (
                agent_id,
                client,
                index_limit,
                expiry,
                chain_id,
                registry,
                signer,
            ),
        )
        message_hash = keccak(struct_bytes)

        try:
            encoded_message = encode_defunct(primitive=message_hash)
            signed = self._account.sign_message(encoded_message)
        except Exception as err:  # pylint: disable=broad-except
            raise SignatureError(f"Failed to sign feedback authorization: {err}") from err

        signature = signed.signature
        if len(signature) != 65:
            raise SignatureError("Derived signature must be 65 bytes long.")

        return FeedbackAuthPayload(
            agent_id=agent_id,
            client_address=client,
            index_limit=index_limit,
            expiry=expiry,
            chain_id=chain_id,
            identity_registry=registry,
            signer_address=signer,
            signature=signature,
        )