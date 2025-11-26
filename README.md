# ERC8004 Python SDK

This project ships a lightweight Python SDK that helps you:

- Interact with ERC-8004-compatible Solidity contracts to register identities.
- Produce EIP-191 / EIP-712 signatures for on-chain verification.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Example

```python
import time

from erc8004_sdk import ERC8004Client
from erc8004_sdk.types import AgentProfile

client = ERC8004Client(
    rpc_url="https://mainnet.infura.io/v3/YOUR_KEY",
    identity_contract_address="0xYourIdentityRegistry",
    reputation_contract_address="0xYourReputationRegistry",
    default_account="0xYourAccount",
    private_key="0xYourPrivateKey",
    ipfs_config={"ipfs_url": "http://127.0.0.1:5001"},
    auth_private_key="0xabc123...",
)

result = client.register_agent(
    token_uri="ipfs://placeholder",
    metadata=[
        {"key": "name", "value": "Sample Agent"},
        {"key": "data", "value": "0x1234"},
    ],
)
agent_id = result.agent_id or 0

profile_uri = client.store_agent_profile(
    AgentProfile(
        name="Sample Agent",
        description="Always-on helper",
        image=None,
        endpoints=[{"name": "A2A", "endpoint": "https://example.com/agent.json"}],
        registrations=[
            {"agentId": agent_id, "agentRegistry": f"eip155:1:{client.contract_address}"},
        ],
        supported_trust=["reputation"],
    )
)
client.set_agent_uri(agent_id=agent_id, new_uri=profile_uri)

feedback_auth = client.build_feedback_auth(
    agent_id=agent_id,
    client_address="0xClient",
    index_limit=10,
    expiry=int(time.time()) + 3600,
    chain_id=1,
    identity_registry=client.contract_address,
).hex()

client.give_feedback(
    agent_id=agent_id,
    score=9,
    tag1="customer_support",
    tag2="satisfaction",
    feedback_uri="ipfs://feedback",
    feedback_hash="0x" + "ab" * 32,
    feedback_auth=feedback_auth,
)
```

## Project Layout

```
erc8004_sdk/
├── client.py           # high-level public interface
├── contract.py         # contract interaction layer
├── signer.py           # feedback authorization utilities
├── reputation.py       # reputation registry helpers
├── exceptions.py       # custom exceptions
└── types.py            # data models and helpers
examples/
└── reputation_workflow.py
tests/
├── test_client.py
├── test_contract.py
├── test_contract_utils.py
└── test_signer.py
```

## License

MIT

## Examples

Run the full reputation workflow demo:

```bash
python examples/reputation_workflow.py
```

The example script reads configuration from a `.env` file in the project root. Create a `.env` file with the following variables:

```bash
# RPC Configuration
RPC_URL=https://data-seed-prebsc-1-s1.bnbchain.org:8545

# Contract Addresses
IDENTITY_CONTRACT_ADDRESS=0xYourIdentityRegistryAddress
REPUTATION_CONTRACT_ADDRESS=0xYourReputationRegistryAddress

# Bob's Credentials (Agent Owner)
BOB_PRIVATE_KEY=0xYourBobPrivateKey
BOB_ADDRESS=0xYourBobAddress

# Alice's Credentials (Feedback Provider)
ALICE_PRIVATE_KEY=0xYourAlicePrivateKey
ALICE_ADDRESS=0xYourAliceAddress

# Chain Configuration
CHAIN_ID=11155111

# IPFS Configuration (optional; defaults to local daemon)
IPFS_API_URL=http://127.0.0.1:5001
IPFS_GATEWAY_URL=
IPFS_API_KEY=
IPFS_API_SECRET=
```

# Network

## BSC Testnet
- Identity Registry: `0xa98a5542a1aab336397d487e32021e0e48bef717`
- Reputation Registry: `0x8602bf1bd40f1e840cadf402a2710c846c4c4ad5`
- Validator Registry: `0x5b4015b372a83b517a38abe4d4c67687d77fca5a`
- Comment Contract:  `0x07b0fd536e7b392393b5c6fcadbac4b4f1092d25`