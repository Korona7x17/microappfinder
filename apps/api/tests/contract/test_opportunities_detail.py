"""
T004: Contract test for GET /api/opportunities/{id} (detail endpoint)
Tests opportunity detail endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestOpportunitiesDetailContract:
    """Contract tests for GET /api/opportunities/{id} endpoint"""

    def test_get_opportunity_returns_200_with_full_details(self, client: TestClient):
        """Test successful retrieval returns 200 with full opportunity details"""
        # First, get list to obtain a valid ID
        list_response = client.get("/api/opportunities?limit=1")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]
        if len(opportunities) == 0:
            pytest.skip("No opportunities available for testing")

        opportunity_id = opportunities[0]["id"]

        # Get detail
        response = client.get(f"/api/opportunities/{opportunity_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields per contract
        required_fields = [
            "id", "title", "summary",
            "problem_severity", "market_size_indicator",
            "monetization_potential", "technical_complexity",
            "competition_level", "trend_direction",
            "confidence_level", "analyzed_at",
            "trend_data", "geographic_spread", "affected_industries",
            "pain_point_id", "enrichment_count", "last_enriched_at"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify types
        assert isinstance(data["id"], str)
        assert len(data["id"]) == 36  # UUID format
        assert isinstance(data["title"], str)
        assert isinstance(data["summary"], str)
        assert isinstance(data["problem_severity"], (int, float))
        assert isinstance(data["market_size_indicator"], str)
        assert isinstance(data["monetization_potential"], (int, float))
        assert isinstance(data["technical_complexity"], (int, float))
        assert isinstance(data["competition_level"], str)
        assert isinstance(data["trend_direction"], str)
        assert isinstance(data["confidence_level"], (int, float))
        assert isinstance(data["analyzed_at"], str)
        assert isinstance(data["enrichment_count"], int)

        # Nullable fields
        assert data["trend_data"] is None or isinstance(data["trend_data"], dict)
        assert data["geographic_spread"] is None or isinstance(data["geographic_spread"], list)
        assert data["affected_industries"] is None or isinstance(data["affected_industries"], list)
        assert data["pain_point_id"] is None or isinstance(data["pain_point_id"], str)
        assert data["last_enriched_at"] is None or isinstance(data["last_enriched_at"], str)

    def test_trend_data_structure_when_present(self, client: TestClient):
        """Test trend_data has correct structure when present"""
        # Get first opportunity with trend_data
        list_response = client.get("/api/opportunities")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]

        # Find opportunity with trend_data
        opportunity_with_trends = None
        for opp in opportunities:
            detail_response = client.get(f"/api/opportunities/{opp['id']}")
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                if detail_data.get("trend_data") is not None:
                    opportunity_with_trends = detail_data
                    break

        if opportunity_with_trends is None:
            pytest.skip("No opportunities with trend_data available")

        trend_data = opportunity_with_trends["trend_data"]

        # Verify structure per contract
        assert "timestamps" in trend_data
        assert "frequencies" in trend_data
        assert "sentiment" in trend_data

        assert isinstance(trend_data["timestamps"], list)
        assert isinstance(trend_data["frequencies"], list)
        assert isinstance(trend_data["sentiment"], list)

        # All arrays should have equal length
        assert len(trend_data["timestamps"]) == len(trend_data["frequencies"])
        assert len(trend_data["timestamps"]) == len(trend_data["sentiment"])

        # Verify element types
        for ts in trend_data["timestamps"]:
            assert isinstance(ts, str)  # ISO8601 strings

        for freq in trend_data["frequencies"]:
            assert isinstance(freq, int)

        for sent in trend_data["sentiment"]:
            assert isinstance(sent, (int, float))
            assert -1.0 <= sent <= 1.0  # Sentiment range

    def test_field_value_ranges(self, client: TestClient):
        """Test that numeric fields are within contract-specified ranges"""
        # Get first opportunity
        list_response = client.get("/api/opportunities?limit=1")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]
        if len(opportunities) == 0:
            pytest.skip("No opportunities available")

        opportunity_id = opportunities[0]["id"]
        response = client.get(f"/api/opportunities/{opportunity_id}")
        assert response.status_code == 200

        data = response.json()

        # Verify ranges per contract
        assert 0.0 <= data["problem_severity"] <= 10.0
        assert 0.0 <= data["monetization_potential"] <= 10.0
        assert 0.0 <= data["technical_complexity"] <= 10.0
        assert 0.0 <= data["confidence_level"] <= 1.0

    def test_enum_field_values(self, client: TestClient):
        """Test that enum fields contain valid values per contract"""
        # Get first opportunity
        list_response = client.get("/api/opportunities?limit=1")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]
        if len(opportunities) == 0:
            pytest.skip("No opportunities available")

        opportunity_id = opportunities[0]["id"]
        response = client.get(f"/api/opportunities/{opportunity_id}")
        assert response.status_code == 200

        data = response.json()

        # Verify enum values per contract
        assert data["market_size_indicator"] in ["niche", "mid", "large"]
        assert data["competition_level"] in ["low", "medium", "high", "saturated"]
        assert data["trend_direction"] in ["declining", "stable", "growing", "explosive"]

    def test_get_nonexistent_opportunity_returns_404(self, client: TestClient):
        """Test retrieving nonexistent opportunity returns 404"""
        nonexistent_id = str(uuid.uuid4())

        response = client.get(f"/api/opportunities/{nonexistent_id}")

        assert response.status_code == 404
        data = response.json()

        # Verify error response structure per contract
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert "not found" in data["detail"].lower()

    def test_get_invalid_uuid_returns_422(self, client: TestClient):
        """Test retrieving with invalid UUID format returns 422"""
        invalid_id = "not-a-uuid"

        response = client.get(f"/api/opportunities/{invalid_id}")

        assert response.status_code == 422

    def test_pain_point_id_null_after_ttl(self, client: TestClient):
        """Test that pain_point_id can be null (after 48h TTL deletion)"""
        # This test verifies the contract allows null pain_point_id
        # In practice, this would happen after 48h Reddit compliance deletion

        list_response = client.get("/api/opportunities")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]

        # Find opportunity with null pain_point_id
        for opp in opportunities:
            detail_response = client.get(f"/api/opportunities/{opp['id']}")
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                # Contract allows pain_point_id to be null
                assert detail_data["pain_point_id"] is None or isinstance(detail_data["pain_point_id"], str)

    def test_enrichment_count_non_negative(self, client: TestClient):
        """Test that enrichment_count is always non-negative"""
        list_response = client.get("/api/opportunities?limit=5")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]

        for opp in opportunities:
            response = client.get(f"/api/opportunities/{opp['id']}")
            assert response.status_code == 200

            data = response.json()
            assert data["enrichment_count"] >= 0

    def test_analyzed_at_is_iso8601_format(self, client: TestClient):
        """Test that analyzed_at is in ISO8601 format"""
        list_response = client.get("/api/opportunities?limit=1")
        assert list_response.status_code == 200

        opportunities = list_response.json()["opportunities"]
        if len(opportunities) == 0:
            pytest.skip("No opportunities available")

        opportunity_id = opportunities[0]["id"]
        response = client.get(f"/api/opportunities/{opportunity_id}")
        assert response.status_code == 200

        data = response.json()

        # Verify ISO8601 format (basic check)
        analyzed_at = data["analyzed_at"]
        assert "T" in analyzed_at or " " in analyzed_at  # Contains time separator
        assert len(analyzed_at) > 10  # More than just date

        if data["last_enriched_at"] is not None:
            assert "T" in data["last_enriched_at"] or " " in data["last_enriched_at"]
