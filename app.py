"""ShopEase — E-Commerce website (Flask + MySQL / SQLite fallback)."""
import os
import sqlite3
from functools import wraps
from datetime import datetime

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, g)
from werkzeug.security import generate_password_hash, check_password_hash
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

USE_MYSQL = config.USE_MYSQL
_mysql = None
if USE_MYSQL:
    import mysql.connector
    _mysql_cfg = config.MYSQL_CONFIG

CATEGORIES = ["Electronics", "Fashion", "Home", "Beauty", "Sports", "Grocery"]
PAYMENTS = ["Cash on Delivery", "UPI", "Credit/Debit Card", "Net Banking"]
STATUSES = ["Placed", "Packed", "Shipped", "Out for Delivery", "Delivered", "Cancelled"]


# ---------- DB helpers ----------
def mysql_conn():
    import mysql.connector
    return mysql.connector.connect(**_mysql_cfg)


def get_db():
    if USE_MYSQL:
        conn = mysql_conn()
        return conn
    conn = sqlite3.connect(config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def qmark(query):
    """Convert ? placeholders to %s for MySQL."""
    if USE_MYSQL:
        return query.replace("?", "%s")
    return query


def fetchall(query, params=()):
    db = get_db()
    try:
        if USE_MYSQL:
            cur = db.cursor(dictionary=True)
            cur.execute(qmark(query), params)
            rows = cur.fetchall()
            cur.close()
            return rows
        cur = db.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        db.close()


def fetchone(query, params=()):
    rows = fetchall(query, params)
    return rows[0] if rows else None


def execute(query, params=()):
    db = get_db()
    try:
        if USE_MYSQL:
            cur = db.cursor()
            cur.execute(qmark(query), params)
            db.commit()
            lid = cur.lastrowid
            cur.close()
            return lid
        cur = db.execute(query, params)
        db.commit()
        lid = cur.lastrowid
        return lid
    finally:
        db.close()


def init_db():
    if USE_MYSQL:
        # create database if missing, then tables
        import mysql.connector
        tmp = dict(_mysql_cfg)
        dbname = tmp.pop("database")
        c = mysql.connector.connect(**tmp)
        cur = c.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS `%s`" % dbname)
        c.commit()
        cur.close()
        c.close()
        schema_path = os.path.join(os.path.dirname(__file__), "schema_mysql.sql")
        with open(schema_path, encoding="utf-8") as f:
            sql = f.read()
        db = mysql_conn()
        cur = db.cursor()
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            cur.execute(stmt)
        db.commit()
        cur.close()
        db.close()
    else:
        db = sqlite3.connect(config.SQLITE_PATH)
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL, is_admin INTEGER DEFAULT 0,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS products(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, description TEXT DEFAULT '',
          price REAL NOT NULL, mrp REAL NOT NULL DEFAULT 0,
          category TEXT DEFAULT 'Electronics',
          image_url TEXT DEFAULT '', stock INTEGER DEFAULT 50,
          rating REAL DEFAULT 4.0, is_offer INTEGER DEFAULT 0,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS cart_items(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, qty INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL, total REAL NOT NULL DEFAULT 0,
          status TEXT DEFAULT 'Placed', payment_method TEXT DEFAULT 'Cash on Delivery',
          name TEXT DEFAULT '', address TEXT DEFAULT '', phone TEXT DEFAULT '',
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS order_items(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
          qty INTEGER NOT NULL, price REAL NOT NULL);
        """)
        db.commit()
        db.close()
    seed()


def seed():
    if fetchone("SELECT id FROM users WHERE email=?", ("admin@shop.com",)):
        pass
    else:
        execute("INSERT INTO users(name,email,password_hash,is_admin) VALUES(?,?,?,?)",
                ("Admin", "admin@shop.com", generate_password_hash("admin123"), 1))
    if fetchone("SELECT id FROM products LIMIT 1"):
        return
    demo = [
        ("Wireless Bluetooth Headphones", "Noise-cancelling over-ear headphones, 40h battery, deep bass.", 1999, 3999, "Electronics", 4.5, 1, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600"),
        ("Smartwatch Fit Pro", "1.85\" HD display, heart-rate + SpO2, 7-day battery.", 2499, 4999, "Electronics", 4.3, 1, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"),
        ("Men's Cotton T-Shirt", "Premium breathable cotton, regular fit.", 499, 999, "Fashion", 4.2, 1, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600"),
        ("Women's Summer Dress", "Light floral midi dress, comfortable daily wear.", 1299, 2499, "Fashion", 4.4, 0, "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600"),
        ("Running Shoes", "Lightweight anti-skid running shoes for daily training.", 1799, 3299, "Sports", 4.6, 1, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600"),
        ("Stainless Steel Cookware Set", "5-piece induction-friendly cookware set.", 2999, 5999, "Home", 4.5, 0, "https://images.unsplash.com/photo-1584990347449-a2d4c2c0f8e5?w=600"),
        ("Ceramic Coffee Mug (Pack of 4)", "350ml Modern matte-finish mugs.", 699, 1299, "Home", 4.1, 0, "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=600"),
        ("Vitamin C Face Serum", "Brightening serum with hyaluronic acid, 30ml.", 599, 999, "Beauty", 4.3, 1, "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=600"),
        ("Laptop Backpack", "Water-resistant 15.6\" laptop backpack with USB port.", 1199, 2299, "Fashion", 4.4, 0, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"),
        ("Bluetooth Speaker", "Portable waterproof speaker, 12h playtime.", 1499, 2999, "Electronics", 4.5, 1, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600"),
        ("Yoga Mat Anti-Skid", "6mm thick non-slip yoga & exercise mat.", 899, 1599, "Sports", 4.2, 0, "https://images.unsplash.com/photo-1592432678016-e910b452f9a2?w=600"),
        ("Organic Atta 5kg", "Stone-ground whole wheat flour, high fibre.", 349, 450, "Grocery", 4.0, 0, "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600"),
    ]
    for d in demo:
        execute("INSERT INTO products(name,description,price,mrp,category,rating,is_offer,image_url) VALUES(?,?,?,?,?,?,?,?)",
                (d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]))


# ---------- auth helpers ----------
def current_user():
    if "user_id" not in session:
        return None
    return fetchone("SELECT * FROM users WHERE id=?", (session["user_id"],))


def login_required(f):
    @wraps(f)
    def w(*a, **kw):
        if "user_id" not in session:
            flash("Please log in first.", "warn")
            return redirect(url_for("login", next=request.path))
        return f(*a, **kw)
    return w


def admin_required(f):
    @wraps(f)
    def w(*a, **kw):
        u = current_user()
        if not u or not u.get("is_admin"):
            flash("Admin access only.", "error")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w


@app.context_processor
def inject_globals():
    u = current_user()
    cart_count = 0
    if u:
        r = fetchone("SELECT COALESCE(SUM(qty),0) c FROM cart_items WHERE user_id=?", (u["id"],))
        cart_count = r["c"] if r else 0
    return dict(user=u, cart_count=cart_count, categories=CATEGORIES)


# ---------- shop routes ----------
@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    offer = request.args.get("offer", "")
    sort = request.args.get("sort", "new")
    sql = "SELECT * FROM products WHERE 1=1"
    p = []
    if q:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = "%" + q + "%"
        p += [like, like, like]
    if cat:
        sql += " AND category=?"
        p.append(cat)
    if offer == "1":
        sql += " AND is_offer=1"
    if sort == "low":
        sql += " ORDER BY price ASC"
    elif sort == "high":
        sql += " ORDER BY price DESC"
    elif sort == "rating":
        sql += " ORDER BY rating DESC"
    else:
        sql += " ORDER BY id DESC"
    products = fetchall(sql, tuple(p))
    offers = fetchall("SELECT * FROM products WHERE is_offer=1 ORDER BY id DESC LIMIT 4")
    return render_template("index.html", products=products, offers=offers,
                           q=q, cat=cat, offer=offer, sort=sort)


@app.route("/product/<int:pid>")
def product_detail(pid):
    prod = fetchone("SELECT * FROM products WHERE id=?", (pid,))
    if not prod:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    related = fetchall("SELECT * FROM products WHERE category=? AND id!=? LIMIT 4",
                       (prod["category"], pid))
    return render_template("product_detail.html", p=prod, related=related)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        if not name or not email or not pw:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if fetchone("SELECT id FROM users WHERE email=?", (email,)):
            flash("Email already registered. Please log in.", "error")
            return render_template("register.html")
        uid = execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                      (name, email, generate_password_hash(pw)))
        session["user_id"] = uid
        flash("Welcome, %s! Registration successful." % name, "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        u = fetchone("SELECT * FROM users WHERE email=?", (email,))
        if u and check_password_hash(u["password_hash"], pw):
            session["user_id"] = u["id"]
            flash("Welcome back, %s!" % u["name"], "success")
            nxt = request.args.get("next") or request.form.get("next")
            if u.get("is_admin"):
                return redirect(nxt or url_for("admin"))
            return redirect(nxt or url_for("index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


# ---------- cart ----------
@app.route("/cart")
@login_required
def cart():
    u = current_user()
    items = fetchall("""SELECT c.id AS cid, c.qty, p.* FROM cart_items c
                        JOIN products p ON p.id=c.product_id WHERE c.user_id=?""", (u["id"],))
    total = sum(i["price"] * i["qty"] for i in items)
    mrp_total = sum((i["mrp"] or i["price"]) * i["qty"] for i in items)
    return render_template("cart.html", items=items, total=total, saving=mrp_total - total)


@app.route("/cart/add/<int:pid>", methods=["POST", "GET"])
@login_required
def cart_add(pid):
    u = current_user()
    qty = int(request.values.get("qty", 1))
    ex = fetchone("SELECT * FROM cart_items WHERE user_id=? AND product_id=?", (u["id"], pid))
    if ex:
        execute("UPDATE cart_items SET qty=qty+? WHERE id=?", (qty, ex["id"]))
    else:
        execute("INSERT INTO cart_items(user_id,product_id,qty) VALUES(?,?,?)", (u["id"], pid, qty))
    flash("Added to cart.", "success")
    return redirect(request.referrer or url_for("cart"))


@app.route("/cart/update/<int:cid>", methods=["POST"])
@login_required
def cart_update(cid):
    qty = max(1, int(request.form.get("qty", 1)))
    execute("UPDATE cart_items SET qty=? WHERE id=? AND user_id=?", (qty, cid, session["user_id"]))
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:cid>")
@login_required
def cart_remove(cid):
    execute("DELETE FROM cart_items WHERE id=? AND user_id=?", (cid, session["user_id"]))
    flash("Item removed.", "success")
    return redirect(url_for("cart"))


# ---------- checkout & orders ----------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    u = current_user()
    items = fetchall("""SELECT c.qty, p.* FROM cart_items c JOIN products p
                        ON p.id=c.product_id WHERE c.user_id=?""", (u["id"],))
    if not items:
        flash("Your cart is empty.", "warn")
        return redirect(url_for("index"))
    total = sum(i["price"] * i["qty"] for i in items)
    if request.method == "POST":
        name = request.form.get("name", u["name"])
        phone = request.form.get("phone", "")
        address = request.form.get("address", "")
        pay = request.form.get("payment", PAYMENTS[0])
        if not address or not phone:
            flash("Phone and address are required.", "error")
            return render_template("checkout.html", items=items, total=total, payments=PAYMENTS)
        oid = execute("""INSERT INTO orders(user_id,total,status,payment_method,name,address,phone)
                         VALUES(?,?,?,?,?,?,?)""",
                      (u["id"], total, "Placed", pay, name, address, phone))
        for i in items:
            execute("INSERT INTO order_items(order_id,product_id,qty,price) VALUES(?,?,?,?)",
                    (oid, i["id"], i["qty"], i["price"]))
            execute("UPDATE products SET stock=stock-? WHERE id=?", (i["qty"], i["id"]))
        execute("DELETE FROM cart_items WHERE user_id=?", (u["id"],))
        flash("Order #%s placed successfully!" % oid, "success")
        return redirect(url_for("order_detail", oid=oid))
    return render_template("checkout.html", items=items, total=total, payments=PAYMENTS)


@app.route("/orders")
@login_required
def orders():
    u = current_user()
    rows = fetchall("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (u["id"],))
    return render_template("orders.html", orders=rows)


@app.route("/order/<int:oid>")
@login_required
def order_detail(oid):
    u = current_user()
    o = fetchone("SELECT * FROM orders WHERE id=?", (oid,))
    if not o:
        flash("Order not found.", "error")
        return redirect(url_for("orders"))
    if not u.get("is_admin") and o["user_id"] != u["id"]:
        flash("Not allowed.", "error")
        return redirect(url_for("orders"))
    items = fetchall("""SELECT oi.qty, oi.price, p.name, p.image_url FROM order_items oi
                        JOIN products p ON p.id=oi.product_id WHERE oi.order_id=?""", (oid,))
    progress = STATUSES.index(o["status"]) if o["status"] in STATUSES else 0
    return render_template("order_detail.html", o=o, items=items,
                           statuses=STATUSES, progress=progress)


# ---------- admin ----------
@app.route("/admin")
@admin_required
def admin():
    q = request.args.get("q", "").strip()
    if q:
        like = "%" + q + "%"
        products = fetchall("SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY id DESC", (like, like))
    else:
        products = fetchall("SELECT * FROM products ORDER BY id DESC")
    stats = {
        "products": fetchone("SELECT COUNT(*) c FROM products")["c"],
        "orders": fetchone("SELECT COUNT(*) c FROM orders")["c"],
        "users": fetchone("SELECT COUNT(*) c FROM users")["c"],
        "revenue": fetchone("SELECT COALESCE(SUM(total),0) c FROM orders WHERE status!='Cancelled'")["c"],
    }
    recent_orders = fetchall("SELECT * FROM orders ORDER BY id DESC LIMIT 8")
    return render_template("admin/dashboard.html", products=products, stats=stats,
                           recent=recent_orders, q=q, statuses=STATUSES)


@app.route("/admin/product/new", methods=["GET", "POST"])
@admin_required
def admin_new():
    if request.method == "POST":
        f = request.form
        execute("""INSERT INTO products(name,description,price,mrp,category,image_url,stock,rating,is_offer)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (f.get("name"), f.get("description", ""), float(f.get("price", 0)),
                 float(f.get("mrp", 0) or f.get("price", 0)), f.get("category", "Electronics"),
                 f.get("image_url", ""), int(f.get("stock", 50)), float(f.get("rating", 4.0)),
                 1 if f.get("is_offer") else 0))
        flash("Product added.", "success")
        return redirect(url_for("admin"))
    return render_template("admin/product_form.html", p=None, categories=CATEGORIES)


@app.route("/admin/product/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit(pid):
    p = fetchone("SELECT * FROM products WHERE id=?", (pid,))
    if not p:
        flash("Not found.", "error")
        return redirect(url_for("admin"))
    if request.method == "POST":
        f = request.form
        execute("""UPDATE products SET name=?,description=?,price=?,mrp=?,category=?,
                   image_url=?,stock=?,rating=?,is_offer=? WHERE id=?""",
                (f.get("name"), f.get("description", ""), float(f.get("price", 0)),
                 float(f.get("mrp", 0) or f.get("price", 0)), f.get("category"),
                 f.get("image_url", ""), int(f.get("stock", 50)), float(f.get("rating", 4.0)),
                 1 if f.get("is_offer") else 0, pid))
        flash("Product updated.", "success")
        return redirect(url_for("admin"))
    return render_template("admin/product_form.html", p=p, categories=CATEGORIES)


@app.route("/admin/product/<int:pid>/delete")
@admin_required
def admin_delete(pid):
    execute("DELETE FROM products WHERE id=?", (pid,))
    flash("Product deleted.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/order/<int:oid>/status", methods=["POST"])
@admin_required
def admin_status(oid):
    st = request.form.get("status", "Placed")
    execute("UPDATE orders SET status=? WHERE id=?", (st, oid))
    flash("Order #%s → %s" % (oid, st), "success")
    return redirect(request.referrer or url_for("admin"))


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    like = "%" + q + "%"
    rows = fetchall("SELECT id,name,price,image_url FROM products WHERE name LIKE ? LIMIT 6", (like,)) if q else []
    return jsonify(rows)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
