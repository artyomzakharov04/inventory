from flask import Flask, request, jsonify, Response
import psycopg2
import csv
import io
import os

app = Flask(__name__)

DB_URL = os.getenv(
    "DATABASE_URL",
    "dbname=inventory user=postgres password=postgres host=localhost port=5432"
)

def get_conn():
    return psycopg2.connect(DB_URL)

# ---------- CREATE TABLE ----------
with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price NUMERIC NOT NULL,
            category TEXT NOT NULL
        )
        """)
        conn.commit()

# ---------- VALIDATION ----------
def validate(data):
    if data.get("quantity", 0) < 0:
        return "Quantity cannot be negative"
    if data.get("price", 1) <= 0:
        return "Price must be greater than zero"
    return None

# ---------- POST /items ----------
@app.route("/items", methods=["POST"])
def add_item():
    data = request.json
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (name, quantity, price, category) VALUES (%s,%s,%s,%s)",
                (data["name"], data["quantity"], data["price"], data["category"])
            )
            conn.commit()
    return jsonify({"status": "created"}), 201

# ---------- GET /items ----------
@app.route("/items", methods=["GET"])
def get_items():
    category = request.args.get("category")
    with get_conn() as conn:
        with conn.cursor() as cur:
            if category:
                cur.execute("SELECT * FROM items WHERE category=%s", (category,))
            else:
                cur.execute("SELECT * FROM items")
            rows = cur.fetchall()

    return jsonify([
        {"id": r[0], "name": r[1], "quantity": r[2], "price": float(r[3]), "category": r[4]}
        for r in rows
    ])

# ---------- PUT /items/<id> ----------
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.json
    error = validate(data)
    if error:
        return jsonify({"error": error}), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE items
                SET name=%s, quantity=%s, price=%s, category=%s
                WHERE id=%s
            """, (data["name"], data["quantity"], data["price"], data["category"], item_id))
            conn.commit()

    return jsonify({"status": "updated"})

# ---------- DELETE /items/<id> ----------
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM items WHERE id=%s", (item_id,))
            conn.commit()
    return "", 204

# ---------- GET /reports/summary ----------
@app.route("/reports/summary", methods=["GET"])
def report():
    format_ = request.args.get("format", "json")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, quantity, price, category FROM items")
            rows = cur.fetchall()

    total = 0
    categories = {}
    bad_items = []

    for name, qty, price, cat in rows:
        value = qty * float(price)
        total += value

        categories.setdefault(cat, {"quantity": 0, "value": 0})
        categories[cat]["quantity"] += qty
        categories[cat]["value"] += value

        if qty <= 0:
            bad_items.append(name)

    report = {
        "total_value": total,
        "categories": categories,
        "bad_items": bad_items
    }

    if format_ == "csv":
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["TOTAL", total])
        for c, v in categories.items():
            w.writerow([c, v["quantity"], v["value"]])
        return Response(out.getvalue(), mimetype="text/csv")

    return jsonify(report)

if __name__ == "__main__":
    app.run()
