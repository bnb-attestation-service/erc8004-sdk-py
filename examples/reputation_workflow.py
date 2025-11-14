"""
Example workflow demonstrating the complete feedback flow:

1. Bob registers an empty agent and gets an agent ID
2. Bob sets the token URI for his agent
3. Bob approves his agent to Alice
4. Alice generates feedback auth and calls giveFeedback for Bob's agent

This script reads configuration from a .env file. See .env.example for required variables.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

from erc8004_sdk import AuthFeedbck, ERC8004Client
from erc8004_sdk.storage import IPFSStorage
from erc8004_sdk.types import (
    AgentEndpoint,
    AgentProfile,
    AgentRegistrationEntry,
)


def main() -> None:
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    # Configuration from environment variables
    rpc_url = _require_env("RPC_URL")
    identity_contract = _require_env("IDENTITY_CONTRACT_ADDRESS")
    reputation_contract = _require_env("REPUTATION_CONTRACT_ADDRESS")

    # Bob's credentials
    bob_private_key = _require_env("BOB_PRIVATE_KEY")
    bob_address = _require_env("BOB_ADDRESS")

    # Alice's credentials
    alice_private_key = _require_env("ALICE_PRIVATE_KEY")
    alice_address = _require_env("ALICE_ADDRESS")

    # Chain configuration
    chain_id = int(os.getenv("CHAIN_ID", "11155111"))

    # IPFS configuration (defaults to local daemon)
    ipfs_config = {
        "ipfs_url": os.getenv("IPFS_API_URL", "http://127.0.0.1:5001"),
        "ipfs_gateway": os.getenv("IPFS_GATEWAY_URL"),
        "api_key": os.getenv("IPFS_API_KEY"),
        "api_secret": os.getenv("IPFS_API_SECRET"),
    }
    ipfs_storage = IPFSStorage(**{k: v for k, v in ipfs_config.items() if v})

    # ============================================================================
    # Step 1: Bob registers an empty agent
    # ============================================================================
    print("Step 1: Bob registers an empty agent...")
    bob_client = ERC8004Client(
        rpc_url=rpc_url,
        identity_contract_address=identity_contract,
        reputation_contract_address=reputation_contract,
        default_account=bob_address,
        private_key=bob_private_key,
    )

    registration_result = bob_client.register_minimal()
    agent_id = registration_result.agent_id
    print(f"  ✓ Registration tx: {registration_result.tx_hash}")
    print(f"  ✓ Agent ID: {agent_id}")

    if not agent_id:
        print("  ⚠ Warning: Agent ID not returned, waiting for receipt...")
        receipt = bob_client.wait_for_receipt(registration_result.tx_hash)
        agent_id = receipt["agentId"]
        if not agent_id:
            raise ValueError("Failed to get agent ID from registration")

    # Store agent profile
    agent_profile = _build_agent_profile(
        agent_id=agent_id,
        identity_contract=identity_contract,
        bob_address=bob_address,
        name="Bob's Agent",
        description="Bob's agent is a helpful assistant that can answer questions and help with tasks. It is powered by the Reputation Registry contract.",
        image="https://example.com/bob.png",
        a2a_endpoint="https://example.com/bob.json",
        supported_trust=["reputation", "crypto-economic", "tee-attestation"],
    )

    # ============================================================================
    # Step 3: Bob approves his agent to Alice
    # ============================================================================
    print("\nStep 3: Bob approves his agent to Alice...")
    approve_tx = bob_client.approve(
        to_address=alice_address,
        token_id=agent_id,
    )
    print(f"  ✓ Approval tx: {approve_tx}")

    # ============================================================================
    # Step 4: Alice generates feedback auth and calls giveFeedback
    # ============================================================================
    print("\nStep 4: Alice generates feedback auth and submits feedback...")

    # Alice creates a feedback auth builder
    alice_auth_builder = AuthFeedbck(private_key=alice_private_key)

    # Build the feedback authorization
    expiry = int(time.time()) + 3600  # 1 hour from now
    feedback_auth = alice_auth_builder.build(
        agent_id=agent_id,
        client_address=alice_address,
        index_limit=1,
        expiry=expiry,
        chain_id=chain_id,
        identity_registry=identity_contract,
    )

    # Alice creates her own client (or uses the same one with her credentials)
    alice_client = ERC8004Client(
        rpc_url=rpc_url,
        identity_contract_address=identity_contract,
        reputation_contract_address=reputation_contract,
        default_account=alice_address,
        private_key=alice_private_key,
    )

    # Submit feedback
    feedback_tx = alice_client.give_feedback(
        agent_id=agent_id,
        score=9,
        tag1="excellent",
        tag2="helpful",
        feedback_uri="ipfs://QmAliceFeedback",
        feedback_hash="0x" + "ab" * 32,
        feedback_auth=feedback_auth.encoded,
    )
    print(f"  ✓ Feedback tx: {feedback_tx}")
    print("\n✓ Complete workflow finished successfully!")


if __name__ == "__main__":
    main()


def _require_env(key: str) -> str:
    """Fetch an environment variable and fail loudly if missing."""

    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"Environment variable '{key}' is required. "
            "Please update your .env file (see .env.example)."
        )
    return value


def _build_agent_profile(
    *,
    agent_id: int,
    identity_contract: str,
    bob_address: str,
    name: str,
    description: str,
    image: str,
    a2a_endpoint: str,
    supported_trust: List[str],
) -> AgentProfile:
    """Build the agent profile document using the ERC-8004 reference schema."""

    if agent_id is None:
        raise ValueError("agent_id is required to build the agent profile.")

    registry_ref = f"eip155:1:{identity_contract}"
    return AgentProfile(
        name=name,
        description=(
            description
        ),
        image=image,
        endpoints=[
            AgentEndpoint(
                name="A2A",
                endpoint=a2a_endpoint,
                version="0.3.0",
            ),
            AgentEndpoint(
                name="agentWallet",
                endpoint=f"eip155:1:{bob_address}",
            ),
        ],
        registrations=[
            AgentRegistrationEntry(agent_id=agent_id, agent_registry=registry_ref),
        ],
        supported_trust=supported_trust,
    )
