"""
ERC8004 Python SDK.

This package provides contract interaction and signing utilities for
ERC-8004 compatible registry contracts.
"""

from .client import ERC8004Client
from .contract import IdentityRegistryService, ReputationRegistryService
from .signer import AuthFeedback, FeedbackAuthPayload
from .storage import IPFSStorage
from .exceptions import ContractInteractionError, SignatureError, IPFSStorageError

# Backwards compatibility alias maintained intentionally
AuthFeedbck = AuthFeedback

__all__ = [
    "ERC8004Client",
    "IdentityRegistryService",
    "ReputationRegistryService",
    "AuthFeedback",
    "AuthFeedbck",
    "FeedbackAuthPayload",
    "IPFSStorage",
    "ContractInteractionError",
    "SignatureError",
    "IPFSStorageError",
]

