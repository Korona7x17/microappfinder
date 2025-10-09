"""
T004: Contract test for GET /api/opportunities (list endpoint)
Tests opportunities list endpoint contract compliance
"""
import pytest
from fastapi.testclient import TestClient
import uuid


class TestOpportunitiesListContract:
    """Contract tests for GET /api/opportunities endpoint"""

    def test_list_opportunities_returns_200(self, client: TestClient):
        """Test successful list returns 200 with array and pagination fields"""
        response = client.get("/api/opportunities")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure per contract
        assert "opportunities" in data
        assert isinstance(data["opportunities"], list)
        assert "next_cursor" in data
        assert "has_more" in data
        assert isinstance(data["has_more"], bool)

    def test_opportunity_item_has_required_fields(self, client: TestClient):
        """Test each opportunity item contains all required fields per contract"""
        response = client.get("/api/opportunities")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        if len(opportunities) > 0:
            opp = opportunities[0]

            # Required fields per contract
            required_fields = [
                "id", "title", "summary",
                "problem_severity", "market_size_indicator",
                "monetization_potential", "technical_complexity",
                "competition_level", "trend_direction",
                "confidence_level", "analyzed_at"
            ]

            for field in required_fields:
                assert field in opp, f"Missing required field: {field}"

            # Verify types
            assert isinstance(opp["id"], str)
            assert len(opp["id"]) == 36  # UUID format
            assert isinstance(opp["title"], str)
            assert isinstance(opp["summary"], str)
            assert isinstance(opp["problem_severity"], (int, float))
            assert isinstance(opp["market_size_indicator"], str)
            assert isinstance(opp["monetization_potential"], (int, float))
            assert isinstance(opp["technical_complexity"], (int, float))
            assert isinstance(opp["competition_level"], str)
            assert isinstance(opp["trend_direction"], str)
            assert isinstance(opp["confidence_level"], (int, float))
            assert isinstance(opp["analyzed_at"], str)

    def test_severity_filter_min(self, client: TestClient):
        """Test filtering by minimum severity threshold"""
        response = client.get("/api/opportunities?severity_min=7.0")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        # All returned opportunities should have severity >= 7.0
        for opp in opportunities:
            assert opp["problem_severity"] >= 7.0

    def test_severity_filter_max(self, client: TestClient):
        """Test filtering by maximum severity threshold"""
        response = client.get("/api/opportunities?severity_max=5.0")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        # All returned opportunities should have severity <= 5.0
        for opp in opportunities:
            assert opp["problem_severity"] <= 5.0

    def test_market_size_filter(self, client: TestClient):
        """Test filtering by market size indicator"""
        valid_sizes = ["niche", "mid", "large"]

        for size in valid_sizes:
            response = client.get(f"/api/opportunities?market_size={size}")

            assert response.status_code == 200
            opportunities = response.json()["opportunities"]

            # All returned opportunities should match filter
            for opp in opportunities:
                assert opp["market_size_indicator"] == size

    def test_competition_level_filter(self, client: TestClient):
        """Test filtering by competition level"""
        valid_levels = ["low", "medium", "high", "saturated"]

        for level in valid_levels:
            response = client.get(f"/api/opportunities?competition_level={level}")

            assert response.status_code == 200
            opportunities = response.json()["opportunities"]

            # All returned opportunities should match filter
            for opp in opportunities:
                assert opp["competition_level"] == level

    def test_trend_direction_filter(self, client: TestClient):
        """Test filtering by trend direction"""
        valid_trends = ["declining", "stable", "growing", "explosive"]

        for trend in valid_trends:
            response = client.get(f"/api/opportunities?trend_direction={trend}")

            assert response.status_code == 200
            opportunities = response.json()["opportunities"]

            # All returned opportunities should match filter
            for opp in opportunities:
                assert opp["trend_direction"] == trend

    def test_sort_by_severity_desc(self, client: TestClient):
        """Test sorting by severity in descending order"""
        response = client.get("/api/opportunities?sort_by=severity&sort_order=desc&limit=10")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        # Verify descending order
        severities = [opp["problem_severity"] for opp in opportunities]
        assert severities == sorted(severities, reverse=True)

    def test_sort_by_monetization_asc(self, client: TestClient):
        """Test sorting by monetization potential in ascending order"""
        response = client.get("/api/opportunities?sort_by=monetization&sort_order=asc&limit=10")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        # Verify ascending order
        monetizations = [opp["monetization_potential"] for opp in opportunities]
        assert monetizations == sorted(monetizations)

    def test_pagination_limit_respected(self, client: TestClient):
        """Test that limit parameter is respected"""
        for limit in [1, 5, 10, 20]:
            response = client.get(f"/api/opportunities?limit={limit}")

            assert response.status_code == 200
            opportunities = response.json()["opportunities"]

            assert len(opportunities) <= limit

    def test_pagination_limit_range_validation(self, client: TestClient):
        """Test that limit parameter validates range [1, 50]"""
        # Too low
        response = client.get("/api/opportunities?limit=0")
        assert response.status_code == 422

        # Too high
        response = client.get("/api/opportunities?limit=51")
        assert response.status_code == 422

        # Valid boundaries
        response = client.get("/api/opportunities?limit=1")
        assert response.status_code == 200

        response = client.get("/api/opportunities?limit=50")
        assert response.status_code == 200

    def test_pagination_cursor_works(self, client: TestClient):
        """Test cursor-based pagination returns next page"""
        # Get first page
        response = client.get("/api/opportunities?limit=5")
        assert response.status_code == 200

        data = response.json()
        first_page_ids = [opp["id"] for opp in data["opportunities"]]

        if data["has_more"] and data["next_cursor"]:
            # Get second page using cursor
            response = client.get(f"/api/opportunities?limit=5&cursor={data['next_cursor']}")
            assert response.status_code == 200

            second_data = response.json()
            second_page_ids = [opp["id"] for opp in second_data["opportunities"]]

            # Pages should not overlap
            assert set(first_page_ids).isdisjoint(set(second_page_ids))

    def test_default_limit_is_12(self, client: TestClient):
        """Test default limit is 12 when not specified (per contract)"""
        response = client.get("/api/opportunities")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        # Should return at most 12 items by default
        assert len(opportunities) <= 12

    def test_default_sort_is_analyzed_at_desc(self, client: TestClient):
        """Test default sort is analyzed_at descending (per contract)"""
        response = client.get("/api/opportunities?limit=10")

        assert response.status_code == 200
        opportunities = response.json()["opportunities"]

        if len(opportunities) > 1:
            # Verify analyzed_at is in descending order
            analyzed_dates = [opp["analyzed_at"] for opp in opportunities]
            assert analyzed_dates == sorted(analyzed_dates, reverse=True)

    def test_invalid_enum_values_return_422(self, client: TestClient):
        """Test invalid enum values return 422 validation error"""
        # Invalid market_size
        response = client.get("/api/opportunities?market_size=invalid")
        assert response.status_code == 422

        # Invalid competition_level
        response = client.get("/api/opportunities?competition_level=invalid")
        assert response.status_code == 422

        # Invalid trend_direction
        response = client.get("/api/opportunities?trend_direction=invalid")
        assert response.status_code == 422

        # Invalid sort_by
        response = client.get("/api/opportunities?sort_by=invalid")
        assert response.status_code == 422

        # Invalid sort_order
        response = client.get("/api/opportunities?sort_order=invalid")
        assert response.status_code == 422

    def test_severity_range_validation(self, client: TestClient):
        """Test severity filters validate range [0.0, 10.0]"""
        # Below min
        response = client.get("/api/opportunities?severity_min=-1.0")
        assert response.status_code == 422

        # Above max
        response = client.get("/api/opportunities?severity_max=11.0")
        assert response.status_code == 422

        # Valid boundaries
        response = client.get("/api/opportunities?severity_min=0.0")
        assert response.status_code == 200

        response = client.get("/api/opportunities?severity_max=10.0")
        assert response.status_code == 200
