import time

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_abi import decode as abi_decode
from eth_utils import keccak
from web3 import Web3

from erc8004_sdk.exceptions import SignatureError
from erc8004_sdk.signer import ABI_TYPES, AuthFeedbck, FeedbackAuthPayload


def _strip_hex_prefix(value: str) -> str:
    return value[2:] if value.startswith("0x") else value


def test_build_feedback_auth_payload_roundtrip():
    acct = Account.create()
    builder = AuthFeedbck(private_key=acct.key.hex())

    payload = builder.build(
        agent_id=123,
        client_address="0x" + "1" * 40,
        index_limit=5,
        expiry=int(time.time()) + 3600,
        chain_id=1,
        identity_registry="0x" + "2" * 40,
    )

    assert isinstance(payload, FeedbackAuthPayload)
    encoded = payload.encoded
    assert len(encoded) == 224 + 65

    struct_part = encoded[:224]
    signature = encoded[224:]

    (
        agent_id,
        client_address,
        index_limit,
        expiry,
        chain_id,
        identity_registry,
        signer_address,
    ) = abi_decode(ABI_TYPES, struct_part)

    assert agent_id == 123
    assert Web3.to_checksum_address(client_address) == "0x" + "1" * 40
    assert index_limit == 5
    assert expiry == payload.expiry
    assert chain_id == 1
    assert Web3.to_checksum_address(identity_registry) == "0x" + "2" * 40
    assert Web3.to_checksum_address(signer_address) == Web3.to_checksum_address(
        builder.signer_address
    )

    message_hash = keccak(struct_part)
    recovered = Account.recover_message(
        encode_defunct(primitive=message_hash), signature=signature
    )
    assert recovered == Web3.to_checksum_address(builder.signer_address)


def test_build_feedback_auth_payload_with_custom_signer():
    acct = Account.create()
    builder = AuthFeedbck(private_key=acct.key.hex())

    payload = builder.build(
        agent_id=1,
        client_address="0x" + "3" * 40,
        index_limit=10,
        expiry=int(time.time()) + 1000,
        chain_id=10,
        identity_registry="0x" + "4" * 40,
        signer_address="0x" + "5" * 40,
    )

    assert payload.signer_address == Web3.to_checksum_address("0x" + "5" * 40)
    assert payload.agent_id == 1
    assert len(_strip_hex_prefix(payload.hex())) == (224 + 65) * 2


def test_authfeedback_requires_private_key():
    with pytest.raises(SignatureError):
        AuthFeedbck(private_key="")

