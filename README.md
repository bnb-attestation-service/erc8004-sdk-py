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

from erc8004_sdk import ERC8004Client, AuthFeedbck

client = ERC8004Client(
    rpc_url="https://mainnet.infura.io/v3/YOUR_KEY",
    contract_address="0xYourContract",
    contract_abi=[...],  # contract ABI
    default_account="0xYourAccount",
    reputation_contract_address="0xReputation",
    reputation_contract_abi=[...],
)

result = client.register_agent(
    token_uri="ipfs://your_metadata",
    metadata=[
        {"key": "name", "value": "Sample Agent"},
        {"key": "data", "value": "0x1234"},
    ],
    gas_limit=200_000,
)
print(result.tx_hash, result.agent_id)

auth_builder = AuthFeedbck(private_key="0xabc123...")
feedback_auth = auth_builder.build(
    agent_id=result.agent_id or 0,
    client_address="0xClient",
    index_limit=10,
    expiry=int(time.time()) + 3600,
    chain_id=1,
    identity_registry=client.contract_address,
).hex()
print(feedback_auth)

# Authorization helpers
client.approve(to_address="0xAnother", token_id=42)
client.set_approval_for_all(operator="0xOperator", approved=True)
approved = client.get_approved(42)
is_all = client.is_approved_for_all("0xOwner", "0xOperator")

# Reputation registry helpers
client.give_feedback(
    agent_id=result.agent_id or 0,
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

