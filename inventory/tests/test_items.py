import json
from app import app, db


def setup_module():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()


def test_create_item():
    client = app.test_client()
    response = client.post("/items", json={
        "name": "Test",
        "quantity": 10,
        "price": 5,
        "category": "A"
    })
    assert response.status_code == 201


def test_negative_quantity():
    client = app.test_client()
    response = client.post("/items", json={
        "name": "Bad",
        "quantity": -1,
        "price": 5,
        "category": "A"
    })
    assert response.status_code == 400


def test_price_zero():
    client = app.test_client()
    response = client.post("/items", json={
        "name": "Bad",
        "quantity": 1,
        "price": 0,
        "category": "A"
    })
    assert response.status_code == 400
