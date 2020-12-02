from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ROS'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


# Index Route
@app.route('/')
def index():
    return render_template('welcome.html')


# Registration Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap



# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Home
@app.route('/home')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Loaded Orders
    result = cur.execute("SELECT * FROM customer_orders ORDER BY created_at ASC ")
    Responses = cur.fetchall()
    if result > 0:
        return render_template('home.html', Responses=Responses)      
    else:
        msg = 'No Available Customer Orders Available'
        return render_template('home.html', msg=msg)
    # Close connection
    cur.close()

#Get All Customer Orders
def customerOrders():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Customer Orders
    result = cur.execute("SELECT * FROM customer_orders ORDER BY created_at ASC")

    customerOrders = cur.fetchall()

    if result > 0:
        return render_template('home.html', customerOrders=customerOrders)
    else:
        msg = 'No Available Customer Orders Available'
        return render_template('home.html', msg=msg)
    # Close connection
    cur.close()

#Order Form Helper Class
class OrderForm(Form):
    customer_name= StringField('Customer Name', [validators.length(min=1, max=250)])
    order_food= StringField('Food Ordered', [validators.Length(min=1, max=200)])
    qty = StringField('Quantity Ordered', [validators.length(min=1, max=200)])
    price = StringField('Food Price',[validators.length(min=1,max=15)])
    status = StringField('Order Payment Status',[validators.length(min=1,max=15)])

#Make Order
@app.route('/make_order', methods=['GET', 'POST'])
@is_logged_in
def add_Customer_Order():
    form = OrderForm(request.form)
    if request.method == 'POST' and form.validate():
        order_food = form.order_food.data
        qty = form.qty.data
        price = form.price.data
        status = form.status.data
        customer_name = form.customer_name.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO customer_orders(customer_name, order_food, qty, price, status) VALUES(%s, %s, %s, %s, %s)", (customer_name,order_food, qty, price, status))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Customer Order Submitted', 'success')

        return redirect(url_for('dashboard'))

    return render_template('maker_order.html', form=form)


#Pay Order -To Be Implemented Further

#Print Receipt
@app.route('/print_receipt/<string:id>/')
def printReceipt(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Question
    result = cur.execute("SELECT * FROM customer_orders WHERE id = %s", [id])

    printReceipt = cur.fetchone()

    return render_template('print_receipt.html', printReceipt=printReceipt)

if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
