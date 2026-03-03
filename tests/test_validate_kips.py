"""Tests for the KIP schema validator."""

from src.common.validate_kips import validate


def _valid_kip_data(**overrides):
    """Return a minimal valid KIP document, with optional overrides."""
    base = {
        "artifact_id": "test-artifact",
        "artifact_type": "meeting_transcript",
        "extracted_by": "Test Author",
        "extraction_date": "2026-04-08",
        "kips": [
            {
                "id": "KIP-001",
                "text": "Decision to migrate database to CosmosDB",
                "category": "decision",
            }
        ],
    }
    base.update(overrides)
    return base


class TestValidKips:
    def test_minimal_valid_document(self):
        assert validate(_valid_kip_data()) == []

    def test_optional_fields_accepted(self):
        data = _valid_kip_data(
            validated_by="Domain Expert",
            validation_date="2026-04-10",
        )
        data["kips"][0]["source_hint"] = "line 5"
        assert validate(data) == []

    def test_multiple_kips_sequential(self):
        data = _valid_kip_data()
        data["kips"].append({
            "id": "KIP-002",
            "text": "Migration owner assigned to Person A",
            "category": "action_item",
        })
        assert validate(data) == []


class TestInvalidKips:
    def test_missing_required_field(self):
        data = _valid_kip_data()
        del data["artifact_id"]
        errors = validate(data)
        assert any("artifact_id" in e for e in errors)

    def test_bad_artifact_id_pattern(self):
        errors = validate(_valid_kip_data(artifact_id="INVALID ID"))
        assert any("does not match" in e for e in errors)

    def test_invalid_artifact_type(self):
        errors = validate(_valid_kip_data(artifact_type="podcast"))
        assert any("podcast" in e for e in errors)

    def test_bad_date_format(self):
        errors = validate(_valid_kip_data(extraction_date="April 8"))
        assert len(errors) > 0

    def test_invalid_kip_category(self):
        data = _valid_kip_data()
        data["kips"][0]["category"] = "opinion"
        errors = validate(data)
        assert any("opinion" in e for e in errors)

    def test_kip_text_too_short(self):
        data = _valid_kip_data()
        data["kips"][0]["text"] = "short"
        errors = validate(data)
        assert any("too short" in e for e in errors)

    def test_kip_id_wrong_format(self):
        data = _valid_kip_data()
        data["kips"][0]["id"] = "KIP-1"
        errors = validate(data)
        assert any("does not match" in e for e in errors)

    def test_non_sequential_ids(self):
        data = _valid_kip_data()
        data["kips"].append({
            "id": "KIP-003",
            "text": "This skips KIP-002 and should fail",
            "category": "decision",
        })
        errors = validate(data)
        assert any("sequential" in e for e in errors)

    def test_extra_top_level_field(self):
        data = _valid_kip_data(extra_field="not allowed")
        errors = validate(data)
        assert len(errors) > 0

    def test_extra_kip_field(self):
        data = _valid_kip_data()
        data["kips"][0]["confidence"] = 0.9
        errors = validate(data)
        assert len(errors) > 0

    def test_empty_kips_array(self):
        errors = validate(_valid_kip_data(kips=[]))
        assert len(errors) > 0
