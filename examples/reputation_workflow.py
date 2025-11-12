"""
Example workflow for registering an agent, constructing feedback authorization,
and submitting feedback through the reputation registry.

The script demonstrates how to wire up the SDK. It assumes that the ABIs and
contract addresses are available locally.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from erc8004_sdk import AuthFeedbck, ERC8004Client


def load_abi(path: str | os.PathLike[str]) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as fp:
        return json.load(fp)


def main() -> None:
    identity_abi = load_abi("abi/identityRegistry.json")
    reputation_abi = load_abi("abi/reputationRegistry.json")

    client = ERC8004Client(
        rpc_url="https://sepolia.infura.io/v3/YOUR_KEY",
        contract_address="0xIdentityRegistryAddress",
        contract_abi=identity_abi,
        default_account="0xYourEOA",
        private_key="0xyourEOAPrivateKey",
        reputation_contract_address="0xReputationRegistryAddress",
        reputation_contract_abi=reputation_abi,
    )

    registration = client.register_agent(
        token_uri="ipfs://QmAgentProfile",
        metadata=[
            {"key": "name", "value": "Example Agent"},
            {"key": "category", "value": "Support"},
        ],
        gas_limit=180_000,
    )
    print("registration tx:", registration.tx_hash)

    auth_builder = AuthFeedbck(private_key="0xyourSignerPrivateKey")
    
    feedback_auth = auth_builder.build(
        agent_id=registration.agent_id or 0,
        client_address="0xClientEOA",
        index_limit=1,
        expiry=int(time.time()) + 3600,
        chain_id=11155111,  # Sepolia
        identity_registry=client.contract_address,
    ).encoded

    feedback_tx = client.give_feedback(
        agent_id=registration.agent_id or 0,
        score=9,
        tag1="support",
        tag2="positive",
        feedback_uri="ipfs://QmFeedbackContent",
        feedback_hash="0x" + "ab" * 32,
        feedback_auth=feedback_auth,
        gas_limit=220_000,
    )
    print("feedback tx:", feedback_tx)


if __name__ == "__main__":
    main()

