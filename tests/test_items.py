from app import app

def test_add_item():
    client = app.test_client()
    r = client.post("/items", json={
        "name": "Test",
        "quantity": 1,
        "price": 10,
        "category": "A"
    })
    assert r.status_code == 201


