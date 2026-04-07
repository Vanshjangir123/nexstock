"""
NexStock - Advanced Warehouse Management System
Enhanced with: Activity Log, Category Stats, Export CSV,
Stock History, Dashboard Charts, Profile Page, and more.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import sqlite3
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nexstock_ultra_secret_2024'

DATABASE = 'nexstock.db'


# ─────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        full_name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        role TEXT DEFAULT 'Admin'
    )''')

    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        price REAL NOT NULL DEFAULT 0.0,
        supplier TEXT DEFAULT '',
        description TEXT DEFAULT '',
        date_added TEXT NOT NULL
    )''')

    # Activity log table — tracks every action
    c.execute('''CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        product_name TEXT NOT NULL,
        details TEXT DEFAULT '',
        user TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )''')

    # Stock history table — tracks every stock change
    c.execute('''CREATE TABLE IF NOT EXISTS stock_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        action_type TEXT NOT NULL,
        quantity_changed INTEGER NOT NULL,
        quantity_before INTEGER NOT NULL,
        quantity_after INTEGER NOT NULL,
        user TEXT NOT NULL,
        timestamp TEXT NOT NULL
    )''')

    # Default user: vansh17 / Vanshjangir17
    c.execute("SELECT * FROM users WHERE username = 'vansh17'")
    if not c.fetchone():
        c.execute("""INSERT INTO users (username, password, full_name, email, role)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('vansh17', 'Vanshjangir17', 'Vansh Jangir', 'vansh@nexstock.com', 'Super Admin'))

    # Seed some demo products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        demo_products = [
            ('MacBook Pro 16"', 'Electronics', 12, 149999.00, 'Apple Inc.', 'M3 Pro chip, 18GB RAM'),
            ('Samsung 4K Monitor', 'Electronics', 3, 32999.00, 'Samsung', '27-inch IPS panel'),
            ('Mechanical Keyboard', 'Accessories', 25, 4999.00, 'Keychron', 'K2 Pro Wireless'),
            ('Office Chair Pro', 'Furniture', 8, 18500.00, 'ErgoFlex', 'Lumbar support, adjustable'),
            ('Wireless Mouse', 'Accessories', 2, 2499.00, 'Logitech', 'MX Master 3S'),
            ('USB-C Hub 7-in-1', 'Accessories', 45, 1999.00, 'Anker', 'HDMI, USB 3.0, SD Card'),
            ('Standing Desk', 'Furniture', 0, 28000.00, 'FlexiSpot', 'Electric height adjustable'),
            ('Noise Cancelling Headphones', 'Electronics', 15, 24999.00, 'Sony', 'WH-1000XM5'),
            ('Webcam HD 1080p', 'Electronics', 4, 3999.00, 'Logitech', 'C920 with autofocus'),
            ('A4 Paper Ream (500 sheets)', 'Stationery', 120, 349.00, 'JK Paper', '75 GSM white'),
        ]
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for p in demo_products:
            c.execute("""INSERT INTO products (name, category, quantity, price, supplier, description, date_added)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""", (*p, ts))

    conn.commit()
    conn.close()


def log_activity(action, product_name, details, user):
    """Insert a record into the activity log."""
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_log (action, product_name, details, user, timestamp) VALUES (?, ?, ?, ?, ?)",
        (action, product_name, details, user, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()


def log_stock_history(product_id, product_name, action_type, qty_changed, qty_before, qty_after, user):
    """Insert a stock change record into stock_history."""
    conn = get_db()
    conn.execute(
        """INSERT INTO stock_history
           (product_id, product_name, action_type, quantity_changed, quantity_before, quantity_after, user, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (product_id, product_name, action_type, qty_changed, qty_before, qty_after, user,
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = username
            session['full_name'] = user['full_name'] or username
            session['role'] = user['role']
            log_activity('LOGIN', '-', f'User {username} logged in', username)
            flash(f'Welcome back, {user["full_name"] or username}! 👋', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    user = session.get('user', 'unknown')
    log_activity('LOGOUT', '-', f'User {user} logged out', user)
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_quantity = conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM products").fetchone()[0]
    total_value = conn.execute("SELECT COALESCE(SUM(quantity * price), 0) FROM products").fetchone()[0]
    low_stock = conn.execute("SELECT * FROM products WHERE quantity < 5 AND quantity > 0 ORDER BY quantity ASC").fetchall()
    out_of_stock = conn.execute("SELECT COUNT(*) FROM products WHERE quantity = 0").fetchone()[0]

    # Category breakdown for chart
    categories = conn.execute(
        "SELECT category, COUNT(*) as count, SUM(quantity) as total_qty FROM products GROUP BY category ORDER BY count DESC"
    ).fetchall()

    # Recent activity (last 8)
    recent_activity = conn.execute(
        "SELECT * FROM activity_log ORDER BY id DESC LIMIT 8"
    ).fetchall()

    # Top 5 products by value
    top_products = conn.execute(
        "SELECT name, quantity, price, (quantity * price) as total_val FROM products ORDER BY total_val DESC LIMIT 5"
    ).fetchall()

    # Stock In vs Out (last 30 days) for mini chart
    stock_in_total = conn.execute(
        "SELECT COALESCE(SUM(quantity_changed), 0) FROM stock_history WHERE action_type='IN'"
    ).fetchone()[0]
    stock_out_total = conn.execute(
        "SELECT COALESCE(SUM(quantity_changed), 0) FROM stock_history WHERE action_type='OUT'"
    ).fetchone()[0]

    conn.close()

    return render_template('dashboard.html',
        total_products=total_products,
        total_quantity=total_quantity,
        total_value=total_value,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        categories=categories,
        recent_activity=recent_activity,
        top_products=top_products,
        stock_in_total=stock_in_total,
        stock_out_total=stock_out_total
    )


# ─────────────────────────────────────────
# PRODUCTS (CRUD)
# ─────────────────────────────────────────

@app.route('/products')
def products():
    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    sort_by = request.args.get('sort', 'date_added')
    order = request.args.get('order', 'DESC')

    allowed_sorts = ['name', 'quantity', 'price', 'category', 'date_added']
    if sort_by not in allowed_sorts:
        sort_by = 'date_added'

    conn = get_db()
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR category LIKE ? OR supplier LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += f" ORDER BY {sort_by} {order}"
    product_list = conn.execute(query, params).fetchall()

    # All categories for filter dropdown
    all_categories = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    conn.close()

    return render_template('products.html',
        products=product_list,
        search=search,
        category_filter=category_filter,
        sort_by=sort_by,
        order=order,
        all_categories=all_categories
    )


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form['category'].strip()
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        supplier = request.form.get('supplier', '').strip()
        description = request.form.get('description', '').strip()
        date_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        conn.execute(
            "INSERT INTO products (name, category, quantity, price, supplier, description, date_added) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, category, quantity, price, supplier, description, date_added)
        )
        conn.commit()
        conn.close()

        log_activity('ADD', name, f'Added {quantity} units @ ₹{price}', session['user'])
        flash(f'✅ Product "{name}" added successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('add_product.html')


@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('products'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        category = request.form['category'].strip()
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        supplier = request.form.get('supplier', '').strip()
        description = request.form.get('description', '').strip()

        conn.execute(
            "UPDATE products SET name=?, category=?, quantity=?, price=?, supplier=?, description=? WHERE id=?",
            (name, category, quantity, price, supplier, description, id)
        )
        conn.commit()
        conn.close()

        log_activity('EDIT', name, f'Updated details. Qty: {quantity}, Price: ₹{price}', session['user'])
        flash(f'✅ Product "{name}" updated successfully!', 'success')
        return redirect(url_for('products'))

    conn.close()
    return render_template('edit_product.html', product=product)


@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

    if product:
        conn.execute("DELETE FROM products WHERE id = ?", (id,))
        conn.commit()
        log_activity('DELETE', product['name'], f'Deleted product (was {product["quantity"]} units)', session['user'])
        flash(f'🗑️ Product "{product["name"]}" deleted.', 'success')
    else:
        flash('Product not found!', 'danger')

    conn.close()
    return redirect(url_for('products'))


# ─────────────────────────────────────────
# STOCK IN / OUT
# ─────────────────────────────────────────

@app.route('/stock_in/<int:id>', methods=['POST'])
def stock_in(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    amount = int(request.form.get('amount', 0))
    if amount <= 0:
        flash('Enter a valid quantity.', 'warning')
        return redirect(url_for('products'))

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

    if product:
        new_qty = product['quantity'] + amount
        conn.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, id))
        conn.commit()
        log_stock_history(id, product['name'], 'IN', amount, product['quantity'], new_qty, session['user'])
        log_activity('STOCK IN', product['name'], f'+{amount} units. Total: {new_qty}', session['user'])
        flash(f'📦 Stock In: +{amount} units added to "{product["name"]}". New total: {new_qty}', 'success')

    conn.close()
    return redirect(url_for('products'))


@app.route('/stock_out/<int:id>', methods=['POST'])
def stock_out(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    amount = int(request.form.get('amount', 0))
    if amount <= 0:
        flash('Enter a valid quantity.', 'warning')
        return redirect(url_for('products'))

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()

    if product:
        if amount > product['quantity']:
            flash(f'❌ Cannot remove {amount}. Only {product["quantity"]} in stock.', 'danger')
        else:
            new_qty = product['quantity'] - amount
            conn.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_qty, id))
            conn.commit()
            log_stock_history(id, product['name'], 'OUT', amount, product['quantity'], new_qty, session['user'])
            log_activity('STOCK OUT', product['name'], f'-{amount} units. Remaining: {new_qty}', session['user'])
            flash(f'🚚 Stock Out: -{amount} units from "{product["name"]}". Remaining: {new_qty}', 'info')

    conn.close()
    return redirect(url_for('products'))


# ─────────────────────────────────────────
# NEW: ACTIVITY LOG PAGE
# ─────────────────────────────────────────

@app.route('/activity')
def activity():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    logs = conn.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    return render_template('activity.html', logs=logs)


# ─────────────────────────────────────────
# NEW: STOCK HISTORY PAGE
# ─────────────────────────────────────────

@app.route('/stock_history')
def stock_history():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    history = conn.execute("SELECT * FROM stock_history ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()

    return render_template('stock_history.html', history=history)


# ─────────────────────────────────────────
# NEW: EXPORT PRODUCTS AS CSV
# ─────────────────────────────────────────

@app.route('/export_csv')
def export_csv():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    products = conn.execute("SELECT id, name, category, quantity, price, supplier, description, date_added FROM products ORDER BY name").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Category', 'Quantity', 'Price (₹)', 'Supplier', 'Description', 'Date Added'])

    for p in products:
        writer.writerow([p['id'], p['name'], p['category'], p['quantity'],
                         f"{p['price']:.2f}", p['supplier'], p['description'], p['date_added']])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=nexstock_inventory_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    response.headers['Content-type'] = 'text/csv'

    log_activity('EXPORT', 'All Products', 'Exported inventory as CSV', session['user'])
    return response


# ─────────────────────────────────────────
# NEW: PROFILE PAGE
# ─────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match!', 'danger')
                conn.close()
                return render_template('profile.html', user=user)
            conn.execute("UPDATE users SET full_name=?, email=?, password=? WHERE username=?",
                         (full_name, email, new_password, session['user']))
        else:
            conn.execute("UPDATE users SET full_name=?, email=? WHERE username=?",
                         (full_name, email, session['user']))

        conn.commit()
        session['full_name'] = full_name
        flash('✅ Profile updated successfully!', 'success')
        log_activity('PROFILE UPDATE', '-', 'User updated their profile', session['user'])

    conn.close()
    conn2 = get_db()
    user = conn2.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    # Stats for profile
    total_actions = conn2.execute("SELECT COUNT(*) FROM activity_log WHERE user = ?", (session['user'],)).fetchone()[0]
    conn2.close()

    return render_template('profile.html', user=user, total_actions=total_actions)


# ─────────────────────────────────────────
# NEW: CATEGORIES PAGE
# ─────────────────────────────────────────

@app.route('/categories')
def categories():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cats = conn.execute("""
        SELECT category,
               COUNT(*) as product_count,
               SUM(quantity) as total_qty,
               SUM(quantity * price) as total_value,
               MIN(quantity) as min_qty,
               MAX(quantity) as max_qty
        FROM products
        GROUP BY category
        ORDER BY product_count DESC
    """).fetchall()
    conn.close()

    return render_template('categories.html', categories=cats)


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("=" * 55)
    print("  🚀 NexStock is running!")
    print("  Open: http://127.0.0.1:5000")
    print("  Login: vansh17 / Vanshjangir17")
    print("=" * 55)
    app.run(debug=True)
