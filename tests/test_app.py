import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Adiciona a raiz do projeto ao PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


# Variáveis exigidas pelo app.py
os.environ["DATABASE_URL"] = "postgresql://fake:fake@localhost:5432/fake"
os.environ["AUTH_SERVICE_URL"] = "http://auth-service"


# Evita conexão real com PostgreSQL durante o import
with patch("psycopg2.pool.SimpleConnectionPool") as mock_pool_class:
    mock_pool_class.return_value = MagicMock()

    import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_rules_without_authorization(client):
    response = client.get("/rules/test-flag")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Authorization header obrigatório"}


def test_rules_with_invalid_api_key(client):
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch.object(
        app_module.requests,
        "get",
        return_value=mock_response,
    ):
        response = client.get(
            "/rules/test-flag",
            headers={"Authorization": "Bearer invalid-key"},
        )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Chave de API inválida"}


def test_auth_service_timeout(client):
    with patch.object(
        app_module.requests,
        "get",
        side_effect=app_module.requests.exceptions.Timeout,
    ):
        response = client.get(
            "/rules/test-flag",
            headers={"Authorization": "Bearer test-key"},
        )

    assert response.status_code == 504
    assert response.get_json() == {
        "error": "Serviço de autenticação indisponível (timeout)"
    }


def test_create_rule_without_required_fields(client):
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(
        app_module.requests,
        "get",
        return_value=mock_response,
    ):
        response = client.post(
            "/rules",
            headers={"Authorization": "Bearer valid-key"},
            json={},
        )

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "'flag_name' e 'rules' (JSON) são obrigatórios"
    }
