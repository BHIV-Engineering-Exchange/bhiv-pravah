from validators.bucket_contract_validator import (
    ContractValidationError,
    ensure_core_integration,
    ensure_payload_size_within_limit,
    ensure_lineage_request_valid,
)


def test_core_integration_allowed_values():
    ensure_core_integration("core")
    ensure_core_integration("bhiv_core")
    ensure_core_integration("core_gateway")


def test_core_integration_rejects_external():
    try:
        ensure_core_integration("external_system")
        assert False, "Expected ContractValidationError"
    except ContractValidationError:
        assert True


def test_payload_size_rejection():
    payload = {"blob": "x" * 200}

    try:
        ensure_payload_size_within_limit(payload, max_bytes=10)
        assert False, "Expected ContractValidationError"
    except ContractValidationError:
        assert True


def test_lineage_for_first_artifact_must_not_have_parent_hash():
    artifact = {"parent_hash": "abc"}

    try:
        ensure_lineage_request_valid(artifact, expected_parent_hash=None)
        assert False, "Expected ContractValidationError"
    except ContractValidationError:
        assert True


def test_lineage_for_non_first_artifact_must_match_parent_hash():
    artifact = {"parent_hash": "wrong"}

    try:
        ensure_lineage_request_valid(artifact, expected_parent_hash="expected")
        assert False, "Expected ContractValidationError"
    except ContractValidationError:
        assert True
