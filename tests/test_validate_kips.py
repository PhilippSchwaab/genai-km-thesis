"""Tests for the KIP schema validator."""

from src.common.validate_kips import validate


def _valid_kip_data(**overrides):
    """Return a minimal valid KIP document, with optional overrides."""
    base = {
        "artifact_id": "cs-06",
        "artifact_type": "dev_compilation",
        "source_file": "CS-06_Testing_Strategy_compiled.md",
        "extracted_by": "Test Author",
        "extraction_date": "2026-04-16",
        "narrative_summary": "Replacing brittle E2E tests with robust integration tests.",
        "kips": [
            {
                "id": "KIP-001",
                "text": "E2E tests were removed from the project",
                "category": "DEC",
                "source_ref": "commit:27bbf4f",
                "implicit": False,
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
            validation_date="2026-04-20",
        )
        assert validate(data) == []

    def test_multiple_kips_sequential(self):
        data = _valid_kip_data()
        data["kips"].append({
            "id": "KIP-002",
            "text": "Integration tests were introduced as the replacement testing strategy",
            "category": "DEC",
            "source_ref": "commit:5088faa",
            "implicit": False,
        })
        assert validate(data) == []

    def test_implicit_kip_accepted(self):
        data = _valid_kip_data()
        data["kips"][0]["implicit"] = True
        data["kips"][0]["source_ref"] = "inferred:ce26c70,79a4931"
        assert validate(data) == []

    def test_all_dev_categories_accepted(self):
        """Each dev compilation category should be valid."""
        for cat in ["DEC", "IMP", "FIX", "RAT", "CFG", "DEP"]:
            data = _valid_kip_data()
            data["kips"][0]["category"] = cat
            assert validate(data) == [], f"Category {cat} rejected"

    def test_all_support_categories_accepted(self):
        """Each support report category should be valid."""
        for cat in ["ISS", "RES", "TEC", "BLK", "RAT", "CFG"]:
            data = _valid_kip_data(artifact_type="support_report")
            data["kips"][0]["category"] = cat
            assert validate(data) == [], f"Category {cat} rejected"

    def test_source_ref_formats(self):
        """Various source_ref formats should be accepted."""
        for ref in ["commit:27bbf4f", "PR#354", "WI:AB#3651", "inferred:ce26c70,79a4931"]:
            data = _valid_kip_data()
            data["kips"][0]["source_ref"] = ref
            assert validate(data) == [], f"source_ref '{ref}' rejected"


class TestInvalidKips:
    def test_missing_required_field(self):
        data = _valid_kip_data()
        del data["artifact_id"]
        errors = validate(data)
        assert any("artifact_id" in e for e in errors)

    def test_bad_artifact_id_pattern(self):
        errors = validate(_valid_kip_data(artifact_id="CS-06"))
        assert any("does not match" in e for e in errors)

    def test_invalid_artifact_type(self):
        errors = validate(_valid_kip_data(artifact_type="meeting_transcript"))
        assert any("meeting_transcript" in e for e in errors)

    def test_bad_date_format(self):
        errors = validate(_valid_kip_data(extraction_date="April 16"))
        assert len(errors) > 0

    def test_invalid_kip_category(self):
        data = _valid_kip_data()
        data["kips"][0]["category"] = "decision"
        errors = validate(data)
        assert any("decision" in e for e in errors)

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
            "category": "DEC",
            "source_ref": "commit:abc1234",
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

    def test_missing_source_ref(self):
        data = _valid_kip_data()
        del data["kips"][0]["source_ref"]
        errors = validate(data)
        assert any("source_ref" in e for e in errors)
