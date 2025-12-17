import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app, db, Item


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_create_and_get_items(client):
    response = client.post(
        "/items",
        json={
            "name": "Test",
            "quantity": 2,
            "price": 100,
            "category": "TestCat"
        }
    )
    assert response.status_code == 201

    response = client.get("/items")
    items = response.get_json()

    assert len(items) == 1
    assert items[0]["name"] == "Test"


def test_update_quantity_put(client):
    item = Item(
        name="Phone",
        quantity=5,
        price=500,
        category="Tech"
    )
    db.session.add(item)
    db.session.commit()

    response = client.put(
        f"/items/{item.id}/quantity",
        json={"delta": -1}
    )

    assert response.status_code == 200
    assert response.get_json()["new_quantity"] == 4
