from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
import sqlite3, os
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)
UPLOAD_FOLDER = 'app/static/uploads'

# ------------------------
# PUBLIC PAGES
# ------------------------

@main.route('/')
def home():
    return render_template("home.html")

# ------------------------
# PRODUCT VIEWS
# ------------------------

@main.route('/products')
@login_required
def products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, image_filename FROM products")
    items = cursor.fetchall()
    conn.close()

    product_list = [{"id": id_, "name": name, "price": price, "image": image} for id_, name, price, image in items]
    return render_template("products.html", products=product_list, username=current_user.username)

@main.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        image_file = request.files['image']
        filename = None

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_path)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, price, image_filename) VALUES (?, ?, ?)", (name, price, filename))
        conn.commit()
        conn.close()
        return redirect('/products')

    return render_template("add_product.html")

@main.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        cursor.execute("UPDATE products SET name = ?, price = ? WHERE id = ?", (name, price, product_id))
        conn.commit()
        conn.close()
        return redirect('/products')

    cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return render_template('edit_product.html', product_id=product_id, name=product[0], price=product[1])

@main.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect('/products')

# ------------------------
# CART & CHECKOUT
# ------------------------

@main.route('/add-to-cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    cart = session.get('cart', [])
    if product_id not in cart:
        cart.append(product_id)
    session['cart'] = cart
    return redirect('/products')

@main.route('/cart')
@login_required
def cart():
    cart_ids = session.get('cart', [])
    products = []

    if cart_ids:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        query = f"SELECT id, name, price, image_filename FROM products WHERE id IN ({','.join(['?']*len(cart_ids))})"
        cursor.execute(query, cart_ids)
        rows = cursor.fetchall()
        conn.close()

        products = [{"id": id_, "name": name, "price": price, "image": image} for id_, name, price, image in rows]

    return render_template('cart.html', products=products, username=current_user.username)

@main.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_ids = session.get('cart', [])
    if cart_ids:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        query = f"SELECT name, price, image_filename FROM products WHERE id IN ({','.join(['?']*len(cart_ids))})"
        cursor.execute(query, cart_ids)
        items = cursor.fetchall()

        for name, price, image in items:
            cursor.execute("INSERT INTO orders (user_id, product_name, product_price, image_filename) VALUES (?, ?, ?, ?)",
                           (current_user.id, name, price, image))

        conn.commit()
        conn.close()
        session['cart'] = []

    return render_template('checkout_success.html', username=current_user.username)

# ------------------------
# USER ORDER HISTORY
# ------------------------

@main.route('/orders')
@login_required
def order_history():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, product_price, image_filename, timestamp FROM orders WHERE user_id = ? ORDER BY timestamp DESC", (current_user.id,))
    rows = cursor.fetchall()
    conn.close()

    orders = [{"name": r[0], "price": r[1], "image": r[2], "time": r[3]} for r in rows]
    return render_template("orders.html", orders=orders, username=current_user.username)

# ------------------------
# ADMIN SECTION
# ------------------------

def is_admin():
    return current_user.is_authenticated and current_user.id == 1

@main.route('/admin')
@login_required
def admin_dashboard():
    if not is_admin():
        return "🚫 Access Denied", 403
    return render_template("admin/dashboard.html", username=current_user.username)

@main.route('/admin/users')
@login_required
def admin_users():
    if not is_admin():
        return "🚫 Access Denied", 403

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin/users.html", users=users)

@main.route('/admin/products')
@login_required
def admin_products():
    if not is_admin():
        return "🚫 Access Denied", 403

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template("admin/products.html", products=products)
@main.route('/initdb')
def init_db():
    import sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price TEXT NOT NULL,
            image_filename TEXT
        )
    ''')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            total_price TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

    return '✅ Database initialized!'


