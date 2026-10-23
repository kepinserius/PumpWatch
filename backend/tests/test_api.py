from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pumpwatch.domain.models import MarketData
from pumpwatch.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_market_data():
    return MarketData(
        chain="solana",
        token_address="So11111111111111111111111111111111111111112",
        pool_address="58oQChx4yWmvKFELLZzBi4Fo6CmVE2e6X7DCRwymMgVV",
        observed_at=datetime.now(UTC),
        source="dexscreener",
        price_usd=Decimal("150.50"),
        liquidity_usd=Decimal("1000000.00"),
        volume_1h=Decimal("50000"),
        volume_24h=Decimal("1000000"),
        buys_1h=100,
        sells_1h=80,
        price_change_1h=Decimal("2.5"),
    )


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_ready(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ready", "degraded")
        assert "timestamp" in data


class TestProvidersHealth:
    def test_providers_health_endpoint(self, client):
        response = client.get("/api/v1/providers/health")
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "status" in data
        assert "timestamp" in data


class TestTokenEndpoints:
    @patch("pumpwatch.api.router.provider")
    def test_get_token_score_success(self, mock_provider, client, mock_market_data):
        mock_provider.fetch_market_data = AsyncMock(return_value=mock_market_data)
        
        response = client.get("/api/v1/tokens/solana/So11111111111111111111111111111111111111112/score")
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "risk" in data
        assert "momentum" in data
        assert data["token"]["chain"] == "solana"
        assert 0 <= data["momentum"]["score"] <= 100

    @patch("pumpwatch.api.router.provider")
    def test_get_token_score_not_found(self, mock_provider, client):
        mock_provider.fetch_market_data = AsyncMock(return_value=None)
        
        response = client.get("/api/v1/tokens/solana/invalid_address/score")
        
        assert response.status_code == 404

    @patch("pumpwatch.api.router.db")
    def test_list_tokens(self, mock_db, client):
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                "chain": "solana",
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Wrapped SOL",
                "last_seen": datetime.now(UTC),
                "snapshot_count": 5,
            }
        ])
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db.pool = mock_pool
        
        response = client.get("/api/v1/tokens")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("pumpwatch.api.router.db")
    def test_get_token_not_found(self, mock_db, client):
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_db.pool = mock_pool
        
        response = client.get("/api/v1/tokens/solana/invalid_address")
        
        assert response.status_code == 404


class TestAdminEndpoints:
    @patch("pumpwatch.main.ingestion")
    def test_trigger_scan(self, mock_ingestion, client):
        mock_ingestion.scan_and_ingest = AsyncMock(return_value=5)
        
        response = client.post("/api/v1/admin/scan?chain=solana")
        
        assert response.status_code == 200
        data = response.json()
        assert data["chain"] == "solana"
        assert data["tokens_ingested"] == 5
