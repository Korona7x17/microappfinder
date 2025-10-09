"""
T003: Contract test for opportunity analysis worker task
Verifies task signature and return value contract per opportunity_analysis.yaml
"""
import pytest
from uuid import uuid4


class TestOpportunityAnalysisContract:
    """Contract tests for analyze_top_pain_points task"""

    def test_task_function_exists(self):
        """Test that the opportunity analysis task function is importable"""
        from worker.tasks.opportunity_analysis import analyze_top_pain_points

        assert callable(analyze_top_pain_points)

    def test_task_signature_accepts_required_parameters(self):
        """Test task accepts search_run_id and pain_point_ids parameters"""
        from worker.tasks.opportunity_analysis import analyze_top_pain_points
        import inspect

        sig = inspect.signature(analyze_top_pain_points)
        params = list(sig.parameters.keys())

        assert "search_run_id" in params, "Task must accept search_run_id parameter"
        assert "pain_point_ids" in params, "Task must accept pain_point_ids parameter"

    def test_task_returns_required_fields(self):
        """Test task returns dict with opportunities_created, analysis_duration_ms, coverage_rate"""
        from worker.tasks.opportunity_analysis import analyze_top_pain_points

        # Mock inputs (per contract: search_run_id UUID, pain_point_ids array[UUID])
        search_run_id = uuid4()
        pain_point_ids = [uuid4() for _ in range(3)]

        # Call task (will fail since not implemented yet - expected for TDD)
        result = analyze_top_pain_points(search_run_id, pain_point_ids)

        # Verify contract: output must have these fields
        assert isinstance(result, dict), "Task must return a dictionary"
        assert "opportunities_created" in result, "Result must contain opportunities_created"
        assert "analysis_duration_ms" in result, "Result must contain analysis_duration_ms"
        assert "coverage_rate" in result, "Result must contain coverage_rate"

        # Verify types per contract
        assert isinstance(result["opportunities_created"], int), "opportunities_created must be integer"
        assert isinstance(result["analysis_duration_ms"], int), "analysis_duration_ms must be integer"
        assert isinstance(result["coverage_rate"], float), "coverage_rate must be float"

        # Verify coverage_rate range per contract
        assert 0.0 <= result["coverage_rate"] <= 1.0, "coverage_rate must be between 0.0 and 1.0"

    def test_task_validates_pain_point_ids_min_length(self):
        """Test task validates pain_point_ids has at least 1 element (contract: min_length=1)"""
        from worker.tasks.opportunity_analysis import analyze_top_pain_points

        search_run_id = uuid4()
        empty_ids = []

        # Should raise validation error for empty list
        with pytest.raises((ValueError, AssertionError)):
            analyze_top_pain_points(search_run_id, empty_ids)

    def test_task_validates_pain_point_ids_max_length(self):
        """Test task validates pain_point_ids has at most 10 elements (contract: max_length=10)"""
        from worker.tasks.opportunity_analysis import analyze_top_pain_points

        search_run_id = uuid4()
        too_many_ids = [uuid4() for _ in range(11)]

        # Should raise validation error for >10 elements
        with pytest.raises((ValueError, AssertionError)):
            analyze_top_pain_points(search_run_id, too_many_ids)
