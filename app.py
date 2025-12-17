from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 🔹 ПОДКЛЮЧЕНИЕ К POSTGRESQL
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://inventory_user:inventory123@localhost:5432/inventory"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# 🔹 МОДЕЛЬ ТОВАРА
class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)


# 🔹 СОЗДАНИЕ ТАБЛИЦЫ (ОДИН РАЗ)
with app.app_context():
    db.create_all()


# -------------------- API --------------------

# ➕ Добавить товар
@app.route("/items", methods=["POST"])
def add_item():
    data = request.json

    if data["quantity"] < 0:
        return jsonify({"error": "Quantity cannot be negative"}), 400
    if data["price"] <= 0:
        return jsonify({"error": "Price must be greater than zero"}), 400

    item = Item(
        name=data["name"],
        quantity=data["quantity"],
        price=data["price"],
        category=data["category"]
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Item added"}), 201


# 📄 Получить список товаров (с фильтром)
@app.route("/items", methods=["GET"])
def get_items():
    category = request.args.get("category")

    if category:
        items = Item.query.filter_by(category=category).all()
    else:
        items = Item.query.all()

    result = []
    for i in items:
        result.append({
            "id": i.id,
            "name": i.name,
            "quantity": i.quantity,
            "price": i.price,
            "category": i.category
        })

    return jsonify(result)


# ✏️ Обновить товар
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json

    if "quantity" in data and data["quantity"] < 0:
        return jsonify({"error": "Quantity cannot be negative"}), 400
    if "price" in data and data["price"] <= 0:
        return jsonify({"error": "Price must be greater than zero"}), 400

    item.name = data.get("name", item.name)
    item.quantity = data.get("quantity", item.quantity)
    item.price = data.get("price", item.price)
    item.category = data.get("category", item.category)

    db.session.commit()
    return jsonify({"message": "Item updated"})


# ❌ Удалить товар
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"})


# 📊 Отчёт по складу
@app.route("/reports/summary", methods=["GET"])
def report_summary():
    items = Item.query.all()

    total_value = 0
    categories = {}
    invalid_items = []

    for item in items:
        value = item.quantity * item.price
        total_value += value

        if item.category not in categories:
            categories[item.category] = {
                "count": 0,
                "total_value": 0
            }

        categories[item.category]["count"] += item.quantity
        categories[item.category]["total_value"] += value

        if item.quantity <= 0:
            invalid_items.append({
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity
            })

    return jsonify({
        "total_value": total_value,
        "categories": categories,
        "invalid_items": invalid_items
    })


# --------------------

if __name__ == "__main__":
    app.run(debug=True)
