"""
ERC8004 Python SDK.

This package provides contract interaction and signing utilities for
ERC-8004 compatible registry contracts.
"""

from .client import ERC8004Client
from .contract import IdentityRegistryService, ReputationRegistryService
from .signer import AuthFeedbck, FeedbackAuthPayload
from .storage import IPFSStorage
from .exceptions import ContractInteractionError, SignatureError, IPFSStorageError

__all__ = [
    "ERC8004Client",
    "IdentityRegistryService",
    "ReputationRegistryService",
    "AuthFeedbck",
    "FeedbackAuthPayload",
    "IPFSStorage",
    "ContractInteractionError",
    "SignatureError",
    "IPFSStorageError",
]

