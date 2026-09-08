"""
Tests for the restock order endpoints.
"""
import pytest


class TestRestockOrderEndpoints:
    """Test suite for restock order endpoints."""

    def test_create_restock_order(self, client):
        """Test submitting a valid restock order."""
        payload = {
            "items": [
                {
                    "item_sku": "WDG-001",
                    "item_name": "Industrial Widget Type A",
                    "quantity": 50,
                    "unit_cost": 24.99,
                    "line_total": 1249.50
                }
            ],
            "budget": 2000
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["total_cost"] == 1249.50
        assert data["budget"] == 2000
        assert data["status"] == "Processing"
        assert 7 <= data["lead_time_days"] <= 14

        order_date = data["order_date"]
        expected_delivery = data["expected_delivery_date"]
        assert expected_delivery > order_date

    def test_create_restock_order_requires_items(self, client):
        """Test that submitting a restock order with no items fails."""
        response = client.post("/api/restock-orders", json={"items": [], "budget": 500})
        assert response.status_code == 400

    def test_get_restock_orders_includes_created_order(self, client):
        """Test that a submitted restock order shows up in the list."""
        payload = {
            "items": [
                {
                    "item_sku": "FLT-405",
                    "item_name": "Oil Filter Cartridge",
                    "quantity": 100,
                    "unit_cost": 8.25,
                    "line_total": 825.00
                }
            ],
            "budget": 1000
        }
        create_response = client.post("/api/restock-orders", json=payload)
        created_id = create_response.json()["id"]

        list_response = client.get("/api/restock-orders")
        assert list_response.status_code == 200

        data = list_response.json()
        assert isinstance(data, list)
        assert any(order["id"] == created_id for order in data)
