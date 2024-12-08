from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import mysql.connector
from mysql.connector import Error
import re
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'your_secret_key'  # Replace with a strong key for production

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='mobileshopee',
            user='root',
            password=''
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

# Route to check if the database connection works
@app.route('/check_connection', methods=['GET'])
def check_connection():
    conn = get_db_connection()
    if conn:
        conn.close()  # Close connection after checking
        return jsonify({"message": "Connection successful"})
    else:
        return jsonify({"message": "Connection failed"}), 500

# Login required decorator
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to access this page", category="danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Ensure the original function name is preserved
    return wrapper

# Superadmin page
@app.route('/super_home')
@login_required
def super_home():
    if session.get('role') != 'superadmin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('super_home.html')

# Admin page
@app.route('/admin_home')
@login_required
def admin_home():
    if session.get('role') not in ['admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_home.html')

# User home page
@app.route('/user_home')
@login_required
def user_home():
    if 'user_id' not in session:
        flash('Please log in to continue.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()

    if conn is None:
        return "Failed to connect to database."

    # Create a cursor with DictCursor to return rows as dictionaries
    cursor = conn.cursor(dictionary=True)

    # Query to fetch all products
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    # Close the cursor and connection after use
    cursor.close()
    conn.close()

    # Pass the products data to the template
    return render_template('user_home.html', products=products)


# Cart page
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []

    # Add the product ID to the cart
    session['cart'].append(product_id)
    session.modified = True  # Mark session as modified

    return redirect(url_for('user_home'))  # Redirect back to the product page@app.route('/cart')@app.route('/cart')

@app.route('/cart')
@login_required
def cart():
    # Get the database connection
    conn = get_db_connection()
    if conn is None:
        flash("Failed to connect to the database", category="danger")
        return redirect(url_for('product_page'))

    # Get product IDs in the cart from the session
    cart_product_ids = session.get('cart', [])

    # Fetch products from the database if cart is not empty
    products_in_cart = []
    total_price = 0
    if cart_product_ids:
        cursor = conn.cursor(dictionary=True)
        format_ids = ','.join(['%s'] * len(cart_product_ids))
        cursor.execute(f"SELECT * FROM products WHERE id IN ({format_ids})", tuple(cart_product_ids))
        products_in_cart = cursor.fetchall()
        cursor.close()

        # Calculate the total price
        total_price = sum(product['price'] for product in products_in_cart)

    # Close the database connection
    conn.close()

    # Render the cart page
    if not products_in_cart:
        flash("Your cart is empty! Add items to view them here.", category="info")

    return render_template('cart.html', products=products_in_cart, total_price=total_price)


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    # Check if 'cart' exists in the session
    if 'cart' in session:
        try:
            session['cart'].remove(product_id)  # Remove the product ID from the cart
            session.modified = True  # Mark session as modified
            flash("Product removed from cart.", category="success")
        except ValueError:
            flash("Product not in cart.", category="warning")
    else:
        flash("Cart is empty.", category="warning")

    return redirect(url_for('cart'))  # Redirect back to the cart page

@app.route('/checkout')
def checkout():
    cart_product_ids = session.get('cart', [])

    if not cart_product_ids:  # Check if the cart is empty
        flash("Your cart is empty", category="warning")
        return redirect(url_for('cart'))  # Redirect to product page if cart is empty
    
    # Get the database connection
    conn = get_db_connection()
    if conn is None:
        flash("Failed to connect to the database", category="danger")
        return redirect(url_for('user_page'))

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id IN (%s)", (','.join([str(id) for id in cart_product_ids]),))
    products_in_cart = cursor.fetchall()
    cursor.close()

    # Close the connection after the operation
    conn.close()

    # Calculate total price
    total_price = sum(product['price'] for product in products_in_cart)

    return render_template('checkout.html', products=products_in_cart, total_price=total_price)




@app.route('/checkout_complete', methods=['POST'])
def checkout_complete():
    session.pop('cart', None)  # Clear the cart
    return redirect(url_for('user_page'))  # Redirect to product page or home

# Homepage route
@app.route('/')
def homepage():

    conn = get_db_connection()

    if conn is None:
        return "Failed to connect to database."

    # Create a cursor with DictCursor to return rows as dictionaries
    cursor = conn.cursor(dictionary=True)

    # Query to fetch all products
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    # Close the cursor and connection after use
    cursor.close()
    conn.close()

    # Pass the products data to the template
    return render_template('homepage.html', products=products)

# Account page route
@app.route('/account_page')
def account_page():
    return render_template('account_page.html')

@app.route('/seller_approve')
def seller_approve():
    return render_template('seller_approve.html')

@app.route('/seller_dashboard')
@login_required
def seller_dashboard():
    # Ensure seller status is updated in session if user is approved
    session['seller_status'] = 'approved'  # This is just for illustration; you may already have this set during registration
    return render_template('seller_dashboard.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clears all session data (logs the user out)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Admin home user management
@app.route('/admin_home_user', methods=['GET'])
@login_required
def admin_home_user():
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('home'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, password, role FROM users")
        rows = cursor.fetchall()
        return render_template('admin_home_user.html', users=rows)

    except Error as e:
        flash("An error occurred while fetching users", "danger")
        print("Error:", e)
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()

# Admin home sellers management
@app.route('/admin_home_sellers', methods=['GET'])
@login_required
def admin_home_sellers():
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('home'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sellers WHERE status = 'approved'")
        rows = cursor.fetchall()
        return render_template('admin_home_sellers.html', sellers=rows)

    except Error as e:
        flash("An error occurred while fetching approved sellers", "danger")
        print("Error:", e)
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()

# Admin home seller registration
@app.route('/admin_home_reg', methods=['GET'])
@login_required
def admin_home_reg():
    # Check if the user is an admin
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))
    
    # Establish a database connection
    conn = get_db_connection()
    if conn is None:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('home'))

    try:
        cursor = conn.cursor(dictionary=True)

        # Fetch all seller applications from the database
        cursor.execute("SELECT * FROM sellers")
        rows = cursor.fetchall()

        # Render the template and pass the sellers data
        return render_template('admin_home_reg.html', sellers=rows)

    except Error as e:
        print("Error:", e)
        flash("An error occurred while fetching seller applications", "danger")
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()  # Close the database connection

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM users WHERE email = %s AND password = %s"
                cursor.execute(query, (email, password))
                user = cursor.fetchone()

                if user:
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    flash('Login successful!', 'success')

                    if user['role'] == 'superadmin':
                        return redirect(url_for('super_home'))
                    elif user['role'] == 'admin':
                        return redirect(url_for('admin_home'))
                    else:
                        return redirect(url_for('user_home'))
                else:
                    flash('Invalid email or password.', 'danger')
            except Error as e:
                flash('An error occurred while processing your request.', 'danger')
                print(f"Error: {e}")
            finally:
                conn.close()
        else:
            flash('Unable to connect to the database.', 'danger')
    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email format.', 'danger')
            return redirect(url_for('signup'))

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                check_query = "SELECT * FROM users WHERE email = %s"
                cursor.execute(check_query, (email,))
                if cursor.fetchone():
                    flash('Email is already registered.', 'warning')
                    return redirect(url_for('signup'))

                insert_query = "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (email, password, 'user'))
                conn.commit()
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash('An error occurred while processing your request.', 'danger')
                print(f"Error: {e}")
            finally:
                conn.close()
        else:
            flash('Unable to connect to the database.', 'danger')
    return render_template('signup.html')

# Seller registration route
@app.route('/seller_registration', methods=['GET', 'POST'])
@login_required
def seller_registration():
    conn = get_db_connection()
    if conn is None:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('user_home'))

    user_id = session['user_id']
    try:
        cursor = conn.cursor(dictionary=True)

        # Check if the user already applied as a seller
        cursor.execute("SELECT * FROM sellers WHERE user_id = %s", (user_id,))
        existing_seller = cursor.fetchone()

        if existing_seller:
            if existing_seller['status'] == 'approved':
                # Check if the user hasn't seen the approval page yet
                if not session.get('seen_approval'):
                    session['seen_approval'] = True
                    return render_template('seller_approve.html')
                return redirect(url_for('seller_dashboard'))

            elif existing_seller['status'] == 'declined':
                flash("Your application was declined. You can reapply.")
            else:  # Pending status
                flash("Your application is still pending.", "info")
                return render_template('reg_after_sub.html')

        # Handle the form submission
        if request.method == 'POST':
            # Get form data
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            email = request.form.get('email')
            phone_number = request.form.get('phoneNumber')
            address = request.form.get('address')
            postal_code = request.form.get('postalCode')
            business_name = request.form.get('businessName')
            description = request.form.get('description')

            # Validate required fields
            if not all([first_name, last_name, email, phone_number, address, postal_code, business_name, description]):
                flash("All fields are required.", "danger")
                return render_template('seller_registration.html')

            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash("Invalid email format.", "danger")
                return render_template('seller_registration.html')

            # Validate phone number format (optional: add more strict validation if needed)
            if not re.match(r"^\+?\d{10,15}$", phone_number):  # Simple international phone number format
                flash("Invalid phone number. It should be a valid number.", "danger")
                return render_template('seller_registration.html')

            # Validate postal code (optional: adjust regex based on the country format)
            if not re.match(r"^\d{3,6}$", postal_code):  # Example for a 5 or 6 digit postal code
                flash("Invalid postal code format.", "danger")
                return render_template('seller_registration.html')

            # Insert seller application into the database
            cursor.execute(""" 
                INSERT INTO sellers (user_id, first_name, last_name, email, phone_number, address, postal_code, business_name, description, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (user_id, first_name, last_name, email, phone_number, address, postal_code, business_name, description))
            conn.commit()

            flash("Your seller application has been submitted successfully!", "success")
            return render_template('reg_after_sub.html')

    except Error as e:
        print(f"Error during seller registration: {e}")
        flash("An error occurred. Please try again later.", "danger")
    finally:
        cursor.close()
        conn.close()

    # Render the seller registration form
    return render_template('seller_registration.html')

@app.route('/seller_orders')
@login_required
def seller_orders():
    print("Navigating to seller orders page")

    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # Check if the logged-in seller has 'approved' status in the sellers table
        cursor.execute("""
            SELECT status FROM sellers
            WHERE user_id = %s
        """, (session['user_id'],))

        seller_status = cursor.fetchone()
        print("Seller status:", seller_status)  # Debugging the status value

        # If the status is not 'approved', redirect to the dashboard
        if not seller_status or seller_status['status'] != 'approved':
            flash("You are not an approved seller.", category="danger")
            return redirect(url_for('seller_dashboard'))

        # Fetch orders associated with the seller (ensure you use the correct column for user_id)
        cursor.execute("""
            SELECT * FROM orders
            WHERE user_id = %s  # Ensure this matches the correct column in your orders table
            ORDER BY created_at DESC
        """, (session['user_id'],))

        # Fetch all orders related to the logged-in seller
        orders = cursor.fetchall()

        # Ensure that orders were found
        if not orders:
            flash("No orders found.", category="warning")

        # Render the 'seller_orders.html' template with the orders data
        return render_template('seller_orders.html', orders=orders)

    except Error as e:
        # Handle any errors by flashing a message and redirecting to the seller dashboard
        flash(f"Error: {e}", category="danger")
        return redirect(url_for('seller_dashboard'))  # Redirect only if there's an error

    finally:
        if conn:
            conn.close()
    
@app.route('/product_management')
@login_required
def product_management():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # Ensure user_id exists in session
        user_id = session.get('user_id')
        if not user_id:
            flash("User not logged in", category="danger")
            return redirect(url_for('login'))

        # Fetch products for the logged-in seller
        cursor.execute("SELECT * FROM products WHERE seller_id = %s", (user_id,))
        products = cursor.fetchall()

        print("Products fetched:", products)  # Debugging line
        print("User ID from session:", session.get('user_id'))  # Debugging line


        return render_template('product_management.html', products=products)

    except Error as e:
        flash(f"Error: {e}", category="danger")
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    conn = get_db_connection()
    try:
        # Check if the logged-in user is an approved seller
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM sellers WHERE user_id = %s AND status = 'approved'", (session['user_id'],))
        seller = cursor.fetchone()
        
        if not seller:
            flash("You need to be an approved seller to add products.", category="danger")
            return redirect(url_for('home'))  # Redirect to homepage if not an approved seller

        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            stock_quantity = request.form.get('stock_quantity')  # Changed from quantity to stock_quantity
            category = request.form.get('category')
            image_file = request.files.get('image_file')

            # Ensure all fields are filled
            if not name or not description or not price or not stock_quantity or not category:
                flash("All fields are required", category="danger")
                return render_template('add_product.html')

            # Validate and save the uploaded image
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join('static/uploads/')
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, filename)
                image_file.save(image_path)
            else:
                flash("Invalid image file. Please upload a valid image (png, jpg, jpeg, gif).", category="danger")
                return render_template('add_product.html')

            # Insert the product into the database using MySQL connector
            cursor.execute("""
            INSERT INTO products (name, description, price, stock_quantity, image_url, category, seller_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, description, price, stock_quantity, filename, category, session['user_id']))

            conn.commit()
            flash("Product added successfully!", category="success")
            return redirect(url_for('product_management'))

    except mysql.connector.Error as e:
        flash(f"Error: {e}", category="danger")
    finally:
        if conn:
            conn.close()

    return render_template('add_product.html')

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/approve_seller/<int:id>', methods=['POST'])
@login_required
def approve_seller(id):
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if conn is None:
        flash("Database connection error", category="danger")
        return redirect(url_for('admin_home_reg'))

    try:
        cursor = conn.cursor()
        # Update seller's status to 'approved'
        query = "UPDATE sellers SET status = 'approved' WHERE id = %s"
        cursor.execute(query, (id,))
        conn.commit()

        flash("Seller approved successfully!", category="success")
    except Error as e:
        print(f"Error approving seller: {e}")
        flash("Failed to approve seller", category="danger")
        conn.rollback()
    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin_home_reg'))



@app.route('/decline_seller/<int:id>', methods=['POST'])
@login_required
def decline_seller(id):
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if conn is None:
        flash("Database connection error", category="danger")
        return redirect(url_for('admin_home_reg'))

    try:
        cursor = conn.cursor()
        # Update seller's status to 'declined'
        query = "UPDATE sellers SET status = 'declined' WHERE id = %s"
        cursor.execute(query, (id,))
        conn.commit()

        flash("Seller declined successfully!", category="success")
    except Error as e:
        print(f"Error declining seller: {e}")
        flash("Failed to decline seller", category="danger")
        conn.rollback()
    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin_home_reg'))

@app.route('/update_product/<int:id>', methods=['GET', 'POST'])
@login_required
def update_product(id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # Fetch the product to be updated
        cursor.execute("SELECT * FROM products WHERE id = %s AND seller_id = %s", (id, session['user_id']))
        product = cursor.fetchone()

        if not product:
            flash("Product not found or you don't have permission to update this product.", category="danger")
            return redirect(url_for('seller_dashboard'))

        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            quantity = request.form.get('quantity')
            image_url = request.form.get('image_url')

            # Update the product
            cursor.execute("""
                UPDATE products
                SET name = %s, description = %s, price = %s, quantity = %s, image_url = %s
                WHERE id = %s
            """, (name, description, price, quantity, image_url, id))
            conn.commit()
            flash("Product updated successfully!", category="success")
            return redirect(url_for('seller_dashboard'))

        return render_template('update_product.html', product=product)
    
    except Error as e:
        flash(f"Error: {e}", category="danger")
        return redirect(url_for('seller_dashboard'))
    finally:
        if conn:
            conn.close()

@app.route('/delete_product/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s AND seller_id = %s", (id, session['user_id']))
        conn.commit()
        flash("Product deleted successfully", category="success")
    except Error as e:
        flash(f"Error: {e}", category="danger")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('product_management'))


if __name__ == '__main__':
    app.run(debug=True)
