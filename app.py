from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import os
import csv
import io

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/inventory"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    category = db.Column(db.String, nullable=False)


def validate_item(data, partial=False):
    if not partial:
        for f in ("name", "quantity", "price", "category"):
            if f not in data:
                return f"Missing field: {f}"

    if "quantity" in data and data["quantity"] < 0:
        return "Quantity cannot be negative"

    if "price" in data and data["price"] <= 0:
        return "Price must be greater than zero"

    return None


@app.route("/items", methods=["POST"])
def create_item():
    data = request.json
    error = validate_item(data)
    if error:
        return jsonify({"error": error}), 400

    item = Item(**data)
    db.session.add(item)
    db.session.commit()
    return jsonify({"id": item.id}), 201


@app.route("/items", methods=["GET"])
def get_items():
    category = request.args.get("category")
    query = Item.query
    if category:
        query = query.filter_by(category=category)

    items = query.all()
    return jsonify([
        {
            "id": i.id,
            "name": i.name,
            "quantity": i.quantity,
            "price": float(i.price),
            "category": i.category
        } for i in items
    ])


@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.json

    error = validate_item(data, partial=True)
    if error:
        return jsonify({"error": error}), 400

    for k, v in data.items():
        setattr(item, k, v)

    db.session.commit()
    return jsonify({"status": "updated"})


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@app.route("/reports/summary", methods=["GET"])
def report_summary():
    format_ = request.args.get("format", "json")
    items = Item.query.all()

    total_value = 0
    categories = {}
    invalid_items = []

    for i in items:
        value = float(i.price) * i.quantity
        total_value += value

        if i.category not in categories:
            categories[i.category] = {
                "total_quantity": 0,
                "total_value": 0
            }

        categories[i.category]["total_quantity"] += i.quantity
        categories[i.category]["total_value"] += value

        if i.quantity <= 0:
            invalid_items.append({
                "id": i.id,
                "name": i.name,
                "quantity": i.quantity,
                "price": float(i.price),
                "category": i.category
            })

    report = {
        "total_inventory_value": total_value,
        "categories": categories,
        "items_with_non_positive_quantity": invalid_items
    }

    if format_ == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["TOTAL INVENTORY VALUE", total_value])
        writer.writerow([])
        writer.writerow(["CATEGORY", "QUANTITY", "VALUE"])

        for c, v in categories.items():
            writer.writerow([c, v["total_quantity"], v["total_value"]])

        writer.writerow([])
        writer.writerow(["ITEMS WITH ZERO OR NEGATIVE QUANTITY"])
        writer.writerow(["ID", "NAME", "QUANTITY", "PRICE", "CATEGORY"])

        for i in invalid_items:
            writer.writerow(i.values())

        return Response(output.getvalue(), mimetype="text/csv")

    return jsonify(report)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
