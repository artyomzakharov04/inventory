import os
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# =========================
# НАСТРОЙКИ
# =========================
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =========================
# МОДЕЛЬ
# =========================
class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)

# =========================
# СОЗДАНИЕ ТАБЛИЦЫ
# =========================
with app.app_context():
    db.create_all()

# =========================
# API: GET /items
# =========================
@app.route("/items", methods=["GET"])
def get_items():
    category = request.args.get("category")

    if category:
        items = Item.query.filter_by(category=category).all()
    else:
        items = Item.query.all()

    return jsonify([
        {
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price,
            "category": item.category
        }
        for item in items
    ])

# =========================
# API: POST /items (JSON)
# =========================
@app.route("/items", methods=["POST"])
def create_item():
    data = request.get_json()

    if not data:
        return {"error": "JSON body required"}, 400

    name = data.get("name")
    quantity = data.get("quantity")
    price = data.get("price")
    category = data.get("category")

    if not all([name, quantity is not None, price, category]):
        return {"error": "Missing fields"}, 400

    if quantity < 0:
        return {"error": "Quantity cannot be negative"}, 400

    if price <= 0:
        return {"error": "Price must be greater than zero"}, 400

    item = Item(
        name=name,
        quantity=quantity,
        price=price,
        category=category
    )

    db.session.add(item)
    db.session.commit()

    return {"message": "Item created", "id": item.id}, 201

# =========================
# API: DELETE /items/<id>
# =========================
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get(item_id)

    if not item:
        return {"error": "Item not found"}, 404

    db.session.delete(item)
    db.session.commit()

    return {"message": f"Item {item_id} deleted"}

# =========================
# WEB: ДОБАВЛЕНИЕ ТОВАРА
# =========================
@app.route("/add-item", methods=["GET", "POST"])
def add_item_page():
    if request.method == "POST":
        name = request.form.get("name")
        quantity = int(request.form.get("quantity"))
        price = float(request.form.get("price"))
        category = request.form.get("category")

        if quantity < 0 or price <= 0:
            return "Некорректные данные", 400

        item = Item(
            name=name,
            quantity=quantity,
            price=price,
            category=category
        )

        db.session.add(item)
        db.session.commit()

        return "Товар добавлен"

    return render_template("add_item.html")
@app.route("/reports/summary", methods=["GET"])
def inventory_summary():
    # 1. Общая стоимость всех товаров
    total_value = db.session.query(
        db.func.sum(Item.price * Item.quantity)
    ).scalar() or 0

    # 2. Разбивка по категориям
    categories = db.session.query(
        Item.category,
        db.func.sum(Item.quantity).label("items"),
        db.func.sum(Item.price * Item.quantity).label("value")
    ).group_by(Item.category).all()

    by_category = {}
    for category, items, value in categories:
        by_category[category] = {
            "items": int(items),
            "value": float(value)
        }

    # 3. Товары с нулевым или отрицательным количеством
    problem_items = Item.query.filter(Item.quantity <= 0).all()

    problem_items_data = [
        {
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity
        }
        for item in problem_items
    ]

    return jsonify({
        "total_value": float(total_value),
        "by_category": by_category,
        "problem_items": problem_items_data
    })


# =========================
# WEB: УДАЛЕНИЕ ТОВАРА (DELETE)
# =========================
@app.route("/delete-item")
def delete_item_page():
    return render_template("delete_item.html")

# HTML-страница (ТОЛЬКО GET)
@app.route("/update-quantity", methods=["GET"])
def update_quantity_page():
    return render_template("update_quantity.html")


# API — изменение количества (ТОЛЬКО PUT)
@app.route("/items/<int:item_id>/quantity", methods=["PUT"])
def update_quantity_put(item_id):
    data = request.get_json()
    if not data or "delta" not in data:
        return {"error": "delta is required"}, 400

    item = Item.query.get(item_id)
    if not item:
        return {"error": "Item not found"}, 404

    delta = int(data["delta"])
    new_quantity = item.quantity + delta

    if new_quantity < 0:
        return {"error": "Quantity cannot be negative"}, 400

    item.quantity = new_quantity
    db.session.commit()

    return {
        "message": "Quantity updated",
        "new_quantity": item.quantity
    }



# =========================
# ЗАПУСК
# =========================
if __name__ == "__main__":
    app.run()

