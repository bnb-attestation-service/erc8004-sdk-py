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

from dotenv import load_dotenv

from erc8004_sdk import AuthFeedbck, ERC8004Client


def main() -> None:
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    # Configuration from environment variables
    rpc_url = os.getenv("RPC_URL")
    identity_contract = os.getenv("IDENTITY_CONTRACT_ADDRESS")
    reputation_contract = os.getenv("REPUTATION_CONTRACT_ADDRESS")

    # Bob's credentials
    bob_private_key = os.getenv("BOB_PRIVATE_KEY")
    bob_address = os.getenv("BOB_ADDRESS")

    # Alice's credentials
    alice_private_key = os.getenv("ALICE_PRIVATE_KEY")
    alice_address = os.getenv("ALICE_ADDRESS")

    # Chain configuration
    chain_id = int(os.getenv("CHAIN_ID", "11155111"))

    # Validate required environment variables
    required_vars = {
        "RPC_URL": rpc_url,
        "IDENTITY_CONTRACT_ADDRESS": identity_contract,
        "REPUTATION_CONTRACT_ADDRESS": reputation_contract,
        "BOB_PRIVATE_KEY": bob_private_key,
        "BOB_ADDRESS": bob_address,
        "ALICE_PRIVATE_KEY": alice_private_key,
        "ALICE_ADDRESS": alice_address,
    }
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please create a .env file based on .env.example"
        )

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

    # ============================================================================
    # Step 2: Bob sets the token URI for his agent
    # ============================================================================
    print("\nStep 2: Bob sets the token URI...")
    token_uri = "ipfs://QmBobAgentProfile"
    set_uri_tx = bob_client.set_agent_uri(
        agent_id=agent_id,
        new_uri=token_uri,
    )
    print(f"  ✓ Set URI tx: {set_uri_tx}")

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
