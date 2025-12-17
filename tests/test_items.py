import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


def test_add_item():
    client = app.test_client()
    response = client.post("/items", json={
        "name": "Test",
        "quantity": 1,
        "price": 10,
        "category": "A"
    })
    assert response.status_code == 201
