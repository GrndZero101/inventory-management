"""
Tests for reports API endpoints.
"""
import pytest


class TestQuarterlyReportsEndpoint:
    """Test suite for quarterly reports endpoint."""

    def test_get_quarterly_reports(self, client):
        """Test getting quarterly reports."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        quarter = data[0]
        assert "quarter" in quarter
        assert "total_orders" in quarter
        assert "total_revenue" in quarter
        assert "avg_order_value" in quarter
        assert "fulfillment_rate" in quarter

    def test_quarterly_reports_by_warehouse(self, client):
        """Test filtering quarterly reports by warehouse."""
        all_response = client.get("/api/reports/quarterly")
        filtered_response = client.get("/api/reports/quarterly?warehouse=Tokyo")

        assert filtered_response.status_code == 200

        all_data = all_response.json()
        filtered_data = filtered_response.json()

        # Filtering to a single warehouse should never produce more orders than unfiltered
        assert sum(q["total_orders"] for q in filtered_data) <= sum(q["total_orders"] for q in all_data)

    def test_quarterly_reports_by_month(self, client):
        """Test filtering quarterly reports by a single month restricts results to one quarter."""
        response = client.get("/api/reports/quarterly?month=2025-01")
        assert response.status_code == 200

        data = response.json()
        for quarter in data:
            assert quarter["quarter"] == "Q1-2025"

    def test_quarterly_reports_avg_order_value_calculation(self, client):
        """Test that avg_order_value matches total_revenue / total_orders."""
        response = client.get("/api/reports/quarterly")
        data = response.json()

        for quarter in data:
            if quarter["total_orders"] > 0:
                expected_avg = quarter["total_revenue"] / quarter["total_orders"]
                assert abs(quarter["avg_order_value"] - expected_avg) < 0.01


class TestMonthlyTrendsEndpoint:
    """Test suite for monthly trends endpoint."""

    def test_get_monthly_trends(self, client):
        """Test getting monthly trends."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        month = data[0]
        assert "month" in month
        assert "order_count" in month
        assert "revenue" in month
        assert "delivered_count" in month

    def test_monthly_trends_sorted_ascending(self, client):
        """Test that monthly trends are sorted by month ascending."""
        response = client.get("/api/reports/monthly-trends")
        data = response.json()

        months = [item["month"] for item in data]
        assert months == sorted(months)

    def test_monthly_trends_by_status(self, client):
        """Test filtering monthly trends by status only counts matching orders."""
        response = client.get("/api/reports/monthly-trends?status=Delivered")
        assert response.status_code == 200

        data = response.json()
        # When filtered to only delivered orders, delivered_count should equal order_count
        for month in data:
            assert month["delivered_count"] == month["order_count"]

    def test_monthly_trends_multiple_filters(self, client):
        """Test filtering monthly trends with warehouse and category combined."""
        response = client.get(
            "/api/reports/monthly-trends?warehouse=San Francisco&category=Sensors"
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
