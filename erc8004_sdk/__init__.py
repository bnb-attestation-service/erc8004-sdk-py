"""
ERC8004 Python SDK.

This package provides contract interaction and signing utilities for
ERC-8004 compatible registry contracts.
"""

from .client import ERC8004Client
from .contract import ContractService, ReputationRegistryService
from .signer import AuthFeedbck, FeedbackAuthPayload
from .exceptions import ContractInteractionError, SignatureError

__all__ = [
    "ERC8004Client",
    "ContractService",
    "ReputationRegistryService",
    "AuthFeedbck",
    "FeedbackAuthPayload",
    "ContractInteractionError",
    "SignatureError",
]

