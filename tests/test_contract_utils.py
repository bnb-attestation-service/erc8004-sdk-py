import pytest

from erc8004_sdk.contract import normalize_metadata_entries
from erc8004_sdk.exceptions import ContractInteractionError
from erc8004_sdk.types import MetadataEntry


def test_normalize_metadata_handles_multiple_types():
    entries = [
        MetadataEntry(key="foo", value=b"bar"),
        {"key": "baz", "value": "text"},
        {"key": "hex", "value": "0x1234"},
    ]

    result = normalize_metadata_entries(entries)

    assert result[0]["value"] == b"bar"
    assert result[1]["value"] == b"text"
    assert result[2]["value"] == bytes.fromhex("1234")


def test_normalize_metadata_requires_fields():
    with pytest.raises(ContractInteractionError):
        normalize_metadata_entries([{"key": "foo"}])


def test_normalize_metadata_rejects_invalid_value_type():
    with pytest.raises(ContractInteractionError):
        normalize_metadata_entries([{"key": "foo", "value": 123}])

