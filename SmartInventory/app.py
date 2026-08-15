from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import os
import sys
import webbrowser
import threading

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

app = Flask(__name__,
            template_folder=resource_path("templates"),
            static_folder=resource_path("static"))
app.secret_key = "SmartInventorySecretKey2026"


DATA_FOLDER = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "SmartInventory"
)

os.makedirs(DATA_FOLDER, exist_ok=True)

DATABASE = os.path.join(DATA_FOLDER, "inventory.db")

# Copy the original database to LocalAppData
# only when a database does not already exist
if not os.path.exists(DATABASE):
    bundled_database = resource_path("inventory.db")

    if os.path.exists(bundled_database):
        import shutil
        shutil.copy2(bundled_database, DATABASE)


# -----------------------------
# Create Database
# -----------------------------
def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER,
            price REAL,
            supplier TEXT
        )
    """)
    try:
        cursor.execute("""
            ALTER TABLE products
            ADD COLUMN low_stock_limit INTEGER DEFAULT 5
        """)
    except sqlite3.OperationalError:
        pass
    cursor.execute("""
CREATE TABLE IF NOT EXISTS issue_history (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_id TEXT,

    product_name TEXT,

    issued_qty INTEGER,

    remaining_qty INTEGER,

    issue_date TEXT,

    issue_time TEXT

)
""")

    conn.commit()
    conn.close()


# -----------------------------
# Login
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "gmes":

            session["logged_in"] = True

            return redirect("/dashboard")

        else:

            return render_template(
                "login.html",
                error="Invalid ID or Password"
            )

    return render_template("login.html")


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE quantity > 5")
    in_stock = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*) FROM products
    WHERE quantity > 0
    AND quantity <= low_stock_limit
""")
    low_stock = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products WHERE quantity = 0")
    out_of_stock = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM products")
    product_list = cursor.fetchall()

    conn.close()

    return render_template(
    "dashboard.html",
    total_products=total_products,
    in_stock=in_stock,
    low_stock=low_stock,
    out_of_stock=out_of_stock,
    products=product_list
)


# -----------------------------
# Add Product
# -----------------------------
@app.route("/add_product")
def add_product():
    return render_template("add_product.html")


# -----------------------------
# Save Product
# -----------------------------
@app.route("/save_product", methods=["POST"])
def save_product():

    product_id = request.form["product_id"]
    name = request.form["name"]
    category = request.form["category"]
    quantity = request.form["quantity"]
    price = request.form["price"]
    supplier = request.form["supplier"]
    low_stock_limit = request.form["low_stock_limit"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO products
    (product_id, name, category, quantity, low_stock_limit, price, supplier)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    product_id,
    name,
    category,
    quantity,
    low_stock_limit,
    price,
    supplier
))

    conn.commit()
    conn.close()

    return redirect("/products")


# -----------------------------
# Product List
# -----------------------------
@app.route("/products")
def products():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products ORDER BY id")
    products = cursor.fetchall()

    conn.close()

    return render_template("products.html", products=products)


# -----------------------------
# Edit Product
# -----------------------------
@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        product_id = request.form["product_id"]
        name = request.form["name"]
        category = request.form["category"]
        quantity = request.form["quantity"]
        price = request.form["price"]
        supplier = request.form["supplier"]
        low_stock_limit = request.form["low_stock_limit"]

        cursor.execute("""
            UPDATE products
            SET product_id = ?,
                name = ?,
                category = ?,
                quantity = ?,
                price = ?,
                supplier = ?,
                low_stock_limit = ?
            WHERE id = ?
        """, (
            product_id,
            name,
            category,
            quantity,
            price,
            supplier,
            low_stock_limit,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/products")

    cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    product = cursor.fetchone()

    conn.close()

    return render_template("edit_product.html", product=product)

# -----------------------------
# Update Product
# -----------------------------
@app.route("/update_product", methods=["POST"])
def update_product():

    id = request.form["id"]
    product_id = request.form["product_id"]
    name = request.form["name"]
    category = request.form["category"]
    quantity = request.form["quantity"]
    price = request.form["price"]
    supplier = request.form["supplier"]
    low_stock_limit = request.form["low_stock_limit"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE products
    SET
        product_id=?,
        name=?,
        category=?,
        quantity=?,
        low_stock_limit=?,
        price=?,
        supplier=?
    WHERE id=?
""", (
    product_id,
    name,
    category,
    quantity,
    low_stock_limit,
    price,
    supplier,
    id
))

    conn.commit()
    conn.close()

    return redirect("/low_stock")


# -----------------------------
# Delete Product
# -----------------------------
@app.route("/delete_product/<int:id>")
def delete_product(id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/products")


# -----------------------------
# Low Stock Page
# -----------------------------
@app.route("/low_stock")
def low_stock():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM products
    WHERE quantity > 0
    AND quantity <= low_stock_limit
""")

    products = cursor.fetchall()

    conn.close()

    return render_template("low_stock.html", products=products)

@app.route("/out_of_stock")
def out_of_stock_products():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE quantity = 0")
    products = cursor.fetchall()

    conn.close()

    return render_template("out_of_stock.html", products=products)
# -----------------------------
# Start Program
# -----------------------------
@app.route("/issue_stock", methods=["POST"])
def issue_stock():

    product_id = request.form["id"]
    issue_qty = int(request.form["issue_qty"])

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Get current quantity
    cursor.execute(
        "SELECT quantity FROM products WHERE id=?",
        (product_id,)
    )
    current_qty = cursor.fetchone()[0]

    if issue_qty <= current_qty:

        new_qty = current_qty - issue_qty

        # Update product quantity
        cursor.execute(
            "UPDATE products SET quantity=? WHERE id=?",
            (new_qty, product_id)
        )

        # Get product details
        cursor.execute(
            "SELECT product_id, name FROM products WHERE id=?",
            (product_id,)
        )
        product = cursor.fetchone()

        # Current date and time
        today = datetime.now().strftime("%d-%m-%Y")
        time = datetime.now().strftime("%I:%M:%S %p")

        # Save issue history
        cursor.execute("""
            INSERT INTO issue_history
            (product_id, product_name, issued_qty, remaining_qty, issue_date, issue_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            product[0],
            product[1],
            issue_qty,
            new_qty,
            today,
            time
        ))

        conn.commit()

    conn.close()

    return redirect("/dashboard")
@app.route("/issue_history")
def issue_history():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM issue_history
        ORDER BY id DESC
    """)

    history = cursor.fetchall()

    conn.close()

    return render_template(
        "issue_history.html",
        history=history
    )
if __name__ == "__main__":
    create_table()

    threading.Timer(
        2.0,
        lambda: webbrowser.open("http://127.0.0.1:5000")
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )