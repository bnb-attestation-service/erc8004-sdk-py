"""Custom SDK exceptions."""


class SDKError(Exception):
    """Base SDK exception."""


class ContractInteractionError(SDKError):
    """Raised when contract interaction fails."""


class SignatureError(SDKError):
    """Raised when signing operations fail."""


class IPFSStorageError(SDKError):
    """Raised when IPFS storage operations fail."""

