from flask import Flask, render_template, request, jsonify, session, url_for, redirect, request, send_file
import mysql.connector
from datetime import datetime, timedelta
from decimal import Decimal
import secrets
import io
import pandas as pd
from fpdf import FPDF
import math
import calendar
from dateutil.relativedelta import relativedelta  # For month difference calculation



app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
USERNAME = "admin"
PASSWORD = "password"

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Darshan@2003',  # Change this to your actual password
    'database': 'Acounthandle'  # Ensure this matches your actual database name
}

# Function to connect to the database
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Function to create database and tables
def create_database():
    try:
        # Initial connection (without database)
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        conn.close()

        # Reconnect with the specified database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS Account (
    id INT AUTO_INCREMENT PRIMARY KEY,
    total_balance DECIMAL(10,2) NOT NULL,
    Balance_in_loan DECIMAL(10,2) NOT NULL,
    Free_balance DECIMAL(10,2) NOT NULL
)

""")

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            )
        """)

        # Create loan table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS deposits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    fixed_deposit DECIMAL(10,2) NOT NULL DEFAULT 1000.00,
    loan_interest DECIMAL(10,2) NOT NULL,
    extra_amount DECIMAL(10,2) NOT NULL,
    fine_applied DECIMAL(10,2) NOT NULL,
    total_deposit DECIMAL(10,2) NOT NULL,
    loan_before DECIMAL(10,2) NOT NULL,
    loan_after DECIMAL(10,2) NOT NULL,
    deposit_date date NOT NULL,
    deposit_duration DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)

''')
        cursor.execute('''
                       CREATE TABLE  IF NOT EXISTS total_loans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)

''')

        conn.commit()
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Automatically create database and tables on startup
create_database()

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
    users.name,
    COALESCE(total_loans.total_amount, '-') AS loan_amount
FROM users
LEFT JOIN total_loans ON users.id = total_loans.user_id;

    """
    cursor.execute(query)
    users = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('index.html', users=users)


@app.route('/add_loan', methods=['GET', 'POST'])
def add_loan():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch users for dropdown
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()

    message = session.pop('message', None)  # Retrieve and clear message after redirect
    free_balance = None

    try:
        # Lock Account row to prevent race conditions
        cursor.execute("SELECT free_balance, balance_in_loan FROM Account LIMIT 1 FOR UPDATE")
        account_record = cursor.fetchone()

        if account_record:
            free_balance = float(account_record['free_balance'])
            balance_in_loan = float(account_record['balance_in_loan'])
        else:
            message = "Error: No account data found."
            return render_template('add_loan.html', users=users, free_balance=free_balance, message=message)

    except Exception as e:
        message = f"Database Error: {str(e)}"
        return render_template('add_loan.html', users=users, free_balance=free_balance, message=message)

    if request.method == 'POST' and free_balance is not None:
        user_id = request.form['user_id']
        amount = float(request.form['amount'])

        if amount > free_balance:
            message = "Error: Entered amount exceeds available free balance."
        else:
            try:
                # Insert loan entry
                cursor.execute("INSERT INTO loan (user_id, amount) VALUES (%s, %s)", (user_id, amount))

                # Check & update `total_loans`
                cursor.execute("SELECT total_amount FROM total_loans WHERE user_id = %s", (user_id,))
                total_loan_record = cursor.fetchone()

                if total_loan_record:
                    new_total = float(total_loan_record['total_amount']) + amount
                    cursor.execute("UPDATE total_loans SET total_amount = %s WHERE user_id = %s", (new_total, user_id))
                else:
                    cursor.execute("INSERT INTO total_loans (user_id, total_amount) VALUES (%s, %s)", (user_id, amount))

                # Update Account table
                new_free_balance = free_balance - amount
                new_balance_in_loan = balance_in_loan + amount

                cursor.execute("UPDATE Account SET free_balance = %s, balance_in_loan = %s LIMIT 1",
                               (new_free_balance, new_balance_in_loan))

                # Commit transaction
                conn.commit()

                # ✅ Store success message in session before redirecting
                session['message'] = "Loan Approval Success ✅"

                return redirect(url_for('add_loan'))  # Redirect to clear POST data

            except Exception as e:
                conn.rollback()
                message = f"Error: {str(e)}"

    cursor.close()
    conn.close()
    return render_template('add_loan.html', users=users, free_balance=free_balance, message=message)



@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    users = get_users()
    message = session.pop('message', None)
    error = None
    loan_amount = 0
    total_interest = 0
    min_payment = 1000
    remaining_loan = 0
    extra_amount = 0
    fine = 0
    months_difference = 0

    if request.method == 'POST':
        username = request.form.get('username')
        inserted_amount = float(request.form.get('inserted_amount', 0))
        duration = int(request.form.get('duration', 30))  # Default 30 days
        deposit_date_str = request.form.get('deposit_date')
        apply_fine = request.form.get('apply_fine') == 'on'  # Check if fine is applied

        if not deposit_date_str:
            error = "Please select a deposit date."
        else:
            deposit_date = datetime.strptime(deposit_date_str, '%Y-%m-%d')

            if inserted_amount < 1000:
                error = "Amount must be at least 1000"
            else:
                # Fetch user
                cursor.execute('SELECT * FROM users WHERE name = %s', (username,))
                user = cursor.fetchone()

                if not user:
                    error = "User not found"
                else:
                    user_id = user['id']

                    # Fetch loan amount
                    cursor.execute('SELECT total_amount FROM total_loans WHERE user_id = %s', (user_id,))
                    loan = cursor.fetchone()
                    loan_amount = round(float(loan['total_amount'])) if loan else 0.0

                    # Fetch the last deposit date
                    cursor.execute('''
                        SELECT MAX(deposit_date) AS last_deposit_date
                        FROM deposits WHERE user_id = %s
                    ''', (user_id,))
                    last_deposit_data = cursor.fetchone()
                    last_deposit_date = last_deposit_data['last_deposit_date'] if last_deposit_data else None

                    # Loan Interest Calculation (from get_loan_details)
                    if last_deposit_date:
                        last_deposit_date = datetime.strptime(str(last_deposit_date), '%Y-%m-%d')
                        delta = relativedelta(deposit_date, last_deposit_date)
                        months_difference = delta.years * 12 + delta.months
                    else:
                        first_month_of_year = datetime(deposit_date.year, 1, 1)
                        delta = relativedelta(deposit_date, first_month_of_year)
                        months_difference = delta.years * 12 + delta.months + 1

                    total_months_due = max(1, months_difference)

                    # Fixed deposit per month
                    fixed_deposit = 1000
                    total_fixed_deposit = fixed_deposit * total_months_due

                    # Interest Calculation
                    interest_rate = 0.01 if duration == 30 else 0.005
                    total_interest = round(loan_amount * interest_rate * total_months_due)

                    # Fine Calculation
                    fine = 0
                    if apply_fine:
                        if last_deposit_date:
                            next_month_13th = (last_deposit_date.replace(day=1) + timedelta(days=32)).replace(day=13)
                            if deposit_date > next_month_13th:
                                fine_days = (deposit_date - next_month_13th).days
                                fine = round(fine_days * 10)
                        else:
                            first_month_13th = datetime(deposit_date.year, 1, 13)
                            if deposit_date > first_month_13th:
                                fine_days = (deposit_date - first_month_13th).days
                                fine = round(fine_days * 10)

                    # Minimum required payment
                    min_payment = round(total_fixed_deposit + total_interest + fine)

                    # Extra Amount & Loan Adjustment
                    extra_amount = round(max(0, inserted_amount - min_payment))
                    remaining_loan = round(max(0, loan_amount - extra_amount))

                    if loan:
                        cursor.execute('UPDATE total_loans SET total_amount = %s WHERE user_id = %s', (remaining_loan, user_id))

                    # Update Account Table
                    cursor.execute("SELECT total_balance, free_balance, balance_in_loan FROM Account LIMIT 1")
                    account = cursor.fetchone()
                    if not account:
                        error = "Account data not found!"
                    else:
                        total_balance = account['total_balance']
                        free_balance = account['free_balance']
                        balance_in_loan = account['balance_in_loan']

                        new_total_balance = float(total_balance) + total_interest + fine + total_fixed_deposit
                        new_free_balance = float(free_balance) + inserted_amount
                        new_balance_in_loan = float(balance_in_loan) - extra_amount

                        cursor.execute('''
                            UPDATE Account
                            SET total_balance = %s, free_balance = %s, balance_in_loan = %s
                            LIMIT 1
                        ''', (new_total_balance, new_free_balance, new_balance_in_loan))

                        # Insert deposit record
                        cursor.execute('''
                            INSERT INTO deposits (user_id, fixed_deposit, loan_interest, extra_amount, total_deposit, loan_before, loan_after, fine_applied, deposit_duration, deposit_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (user_id, total_fixed_deposit, total_interest, extra_amount, inserted_amount, loan_amount, remaining_loan, fine, duration, deposit_date_str))

                        conn.commit()

                        # Store success message in session before redirecting
                        session['message'] = f"Deposit added successfully for {total_months_due} months! ✅ (Interest: ₹{total_interest:.2f}, Fine: ₹{fine:.2f})"

                        return redirect(url_for('deposit'))

    cursor.close()
    conn.close()

    return render_template('deposit.html', users=users, message=message, error=error,
                           loan_amount=loan_amount, interest=total_interest, min_payment=min_payment,
                           remaining_loan=remaining_loan, extra_amount=extra_amount, fine=fine,
                           months_difference=months_difference)


@app.route('/loans', methods=['GET'])
def loans():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch loans with created_at
    query = "SELECT u.name, l.amount, l.created_at FROM users u JOIN loan l ON l.user_id = u.id"
    cursor.execute(query)
    loans = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('loans.html', loans=loans)

@app.route('/generate_loans_pdf', methods=['GET'])
def generate_loans_pdf():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT u.name, l.amount, l.created_at FROM users u JOIN loan l ON l.user_id = u.id"
    cursor.execute(query)
    loans = cursor.fetchall()

    cursor.close()
    conn.close()

    # Create PDF
    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    # Add a box around the title and center it
    title = "Loan Details Report"
    title_width = pdf.get_string_width(title) + 10  # Add padding
    title_height = 15  # Height of the box

    # Calculate the position to center the box
    x = (pdf.w - title_width) / 2
    y = 20  # Vertical position (adjust as needed)

    # Draw the box
    pdf.set_xy(x, y)
    pdf.cell(title_width, title_height, title, border=1, align="C", ln=True)

    pdf.ln(2)  # Add some space after the title box

    # Table Headers
    pdf.set_font("Arial", "B", 12)
    col_widths = [60, 40, 50]  # Widths for Name, Loan Amount, Created At columns
    total_width = sum(col_widths)

    # Center the table horizontally
    pdf.set_x((pdf.w - total_width) / 2)

    # Draw headers
    pdf.cell(col_widths[0], 10, "Name", border=1, align="C")
    pdf.cell(col_widths[1], 10, "Loan Amount", border=1, align="C")
    pdf.cell(col_widths[2], 10, "Created At", border=1, align="C")
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", "", 10)
    for loan in loans:
        # Center the table horizontally for each row
        pdf.set_x((pdf.w - total_width) / 2)

        pdf.cell(col_widths[0], 10, loan['name'], border=1, align="C")
        pdf.cell(col_widths[1], 10, f"{loan['amount']:.2f}", border=1, align="C")
        pdf.cell(col_widths[2], 10, str(loan['created_at']), border=1, align="C")
        pdf.ln()

    # Convert to BytesIO for download
    pdf_output = pdf.output(dest='S').encode('latin1')
    pdf_buffer = io.BytesIO(pdf_output)
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name="loans_report.pdf", as_attachment=True, mimetype="application/pdf")

@app.route('/get_loan_details')
def get_loan_details():
    username = request.args.get('username')
    duration = int(request.args.get('duration', 30))  # Default to 30 days
    deposit_date_str = request.args.get('deposit_date')  # Passed deposit date from frontend
    apply_fine = request.args.get('apply_fine', 'false').lower() == 'true'  # Check if fine is applied

    if not username or not deposit_date_str:
        return jsonify({"error": "Username and deposit date are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch user details
    cursor.execute('SELECT * FROM users WHERE name = %s', (username,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    user_id = user['id']

    # Fetch loan amount
    cursor.execute('SELECT total_amount FROM total_loans WHERE user_id = %s', (user_id,))
    loan = cursor.fetchone()
    loan_amount = round(float(loan['total_amount'])) if loan else 0

    # Fetch the last deposit date from the database
    cursor.execute('''
        SELECT MAX(deposit_date) AS last_deposit_date
        FROM deposits WHERE user_id = %s
    ''', (user_id,))
    last_deposit_data = cursor.fetchone()
    last_deposit_date = last_deposit_data['last_deposit_date'] if last_deposit_data else None

    # Convert string to datetime
    current_deposit_date = datetime.strptime(deposit_date_str, '%Y-%m-%d')

    if last_deposit_date:
        last_deposit_date = datetime.strptime(str(last_deposit_date), '%Y-%m-%d')

        # Calculate difference in months
        delta = relativedelta(current_deposit_date, last_deposit_date)
        months_difference = delta.years * 12 + delta.months

        # Ensure months_difference is at least 1 for every deposit
        total_months_due = max(1, months_difference)

    else:
        # If no previous deposit, count from the first month of the current year
        first_month_of_year = datetime(current_deposit_date.year, 1, 1)
        delta = relativedelta(current_deposit_date, first_month_of_year)
        months_difference = delta.years * 12 + delta.months + 1  # Include current month
        total_months_due = months_difference  # Keep them the same

    # Fixed deposit per month
    fixed_deposit = 1000  # ₹1000 per month
    total_fixed_deposit = fixed_deposit * total_months_due  # Total fixed deposit for all months

    # Calculate interest based on deposit duration
    interest_rate = 0.01 if duration == 30 else 0.005
    total_interest = round(loan_amount * interest_rate * total_months_due)  # Interest for all months

    # Fine Calculation (if deposit date is after the 13th of the next month and checkbox is checked)
    fine = 0
    if apply_fine:
        if last_deposit_date:
            # Calculate the 13th of the next month after the last deposit date
            next_month_13th = (last_deposit_date.replace(day=1) + timedelta(days=32)).replace(day=13)

            # If the current deposit date is after the 13th of the next month, calculate the fine
            if current_deposit_date > next_month_13th:
                fine_days = (current_deposit_date - next_month_13th).days
                fine = round(fine_days * 10)  # ₹10 fine per day
        else:
            # If no deposits found, calculate fine from the 13th of the first month of the current year
            first_month_13th = datetime(current_deposit_date.year, 1, 13)  # January 13th of the current year

            # If the current deposit date is after the 13th of the first month, calculate the fine
            if current_deposit_date > first_month_13th:
                fine_days = (current_deposit_date - first_month_13th).days
                fine = round(fine_days * 10) 
 # ₹10 fine per day

    # Minimum required payment includes fine and total fixed deposit
    min_payment = round(total_fixed_deposit + total_interest + fine)


    cursor.close()
    conn.close()

    return jsonify({
        "loan_amount": loan_amount,
        "fixed_deposit": fixed_deposit,
        "total_fixed_deposit": total_fixed_deposit,
        "interest": total_interest,
        "fine": fine,
        "min_payment": min_payment,
        "months_difference": months_difference,
        "total_months_due": total_months_due
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error message
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('deposit'))
        else:
            error = "Invalid username or password. Please try again."

    return render_template('login.html', error=error)


@app.route('/loan_login', methods=['GET', 'POST'])
def loan_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['add_loan_logged_in'] = True
            return redirect(url_for('add_loan'))
        else:
            error = "Invalid username or password. Please try again."

    return render_template('loan_login.html',error=error)

@app.route('/loan_details', methods=['GET', 'POST'])
def loan_details():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all users for dropdown
    cursor.execute("SELECT name FROM users")
    users = cursor.fetchall()

    loans = []
    deposits = []
    selected_user = None

    if request.method == 'POST':
        username = request.form['username']
        selected_user = username

        if username:
            cursor.execute("SELECT id FROM users WHERE name = %s", (username,))
            user = cursor.fetchone()

            if user:
                user_id = user['id']

                # Fetch loan details
                cursor.execute("""
                    SELECT u.name, a.amount, a.created_at
                    FROM users u
                    JOIN loan a ON u.id = a.user_id
                    WHERE u.id = %s
                """, (user_id,))
                loans = cursor.fetchall()

                # Fetch deposit details
                cursor.execute("""
                    SELECT loan_before, total_deposit, loan_interest, extra_amount,
                           fixed_deposit, loan_after, created_at,deposit_duration,fine_applied
                    FROM deposits
                    WHERE user_id = %s
                """, (user_id,))
                deposits = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('loan_details.html', users=users, loans=loans, deposits=deposits, selected_user=selected_user)

def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

@app.route('/download_pdf/<username>')
def download_pdf(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch deposit details for the user
    cursor.execute("""
        SELECT loan_before as Existing_loan, total_deposit, loan_interest, extra_amount as Loan_repay,
               fixed_deposit, loan_after as Loan_left, deposit_date as Deposit_date, fine_applied,
               deposit_duration as Deposit_duration_Days
        FROM deposits
        WHERE user_id = (SELECT id FROM users WHERE name = %s)
    """, (username,))

    deposit_data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not deposit_data:
        return "No data found for user", 404

    # Create PDF instance in LANDSCAPE mode
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Define table headers
    headers = [
        "Existing Loan", "Installment", "Interest", "Loan Repay", "Fixed Deposit",
        "Loan Left", "Deposit Date", "Fine", "Duration (Days)"
    ]

    col_widths = [30, 30, 30, 30, 30, 30, 30, 35, 35]  # Adjusted for landscape mode
    total_table_width = sum(col_widths)  # Total width of the table

    # Set font for title
    pdf.set_font("Arial", "B", 14)

    # Title Box: Spanning entire table width
    pdf.cell(total_table_width, 12, f"Deposit Details of {username}", border=1, ln=True, align="C")
    pdf.ln(5)

    # Set font for table headers
    pdf.set_font("Arial", "B", 10)

    # Print table headers
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, align="C")
    pdf.ln(8)

    pdf.set_font("Arial", "", 10)

    # Print table data
    for row in deposit_data:
        pdf.cell(col_widths[0], 8, str(row["Existing_loan"]), border=1, align="C")
        pdf.cell(col_widths[1], 8, str(row["total_deposit"]), border=1, align="C")
        pdf.cell(col_widths[2], 8, str(row["loan_interest"]), border=1, align="C")
        pdf.cell(col_widths[3], 8, str(row["Loan_repay"]), border=1, align="C")
        pdf.cell(col_widths[4], 8, str(row["fixed_deposit"]), border=1, align="C")
        pdf.cell(col_widths[5], 8, str(row["Loan_left"]), border=1, align="C")
        pdf.cell(col_widths[6], 8, str(row["Deposit_date"]), border=1, align="C")
        pdf.cell(col_widths[7], 8, str(row["fine_applied"]), border=1, align="C")
        pdf.cell(col_widths[8], 8, str(row["Deposit_duration_Days"]), border=1, align="C")
        pdf.ln(8)

    # Convert PDF to BytesIO
    pdf_output = io.BytesIO()
    pdf_output.write(pdf.output(dest="S").encode("latin-1"))
    pdf_output.seek(0)

    filename = f"{username}_deposit_details.pdf"
    return send_file(pdf_output, download_name=filename, as_attachment=True, mimetype="application/pdf")

@app.route('/get_deposits', methods=['GET'])
def get_deposits():
    month = request.args.get('month')
    year = request.args.get('year')

    if not month or not year:
        return render_template('deposits.html', error='Both month and year are required')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
SELECT
    u.id AS user_id,
    u.name AS name,
    COALESCE(d.loan_before, tl.total_amount, 0) AS loan_before,
    COALESCE(d.total_deposit, 0) AS total_deposit,
    COALESCE(d.loan_interest, 0) AS loan_interest,
    COALESCE(d.fine_applied, 0) AS fine_applied,
    COALESCE(d.extra_amount, 0) AS extra_amount,
    COALESCE(d.loan_after, tl.total_amount, 0) AS loan_after,
    COALESCE(d.fixed_deposit, 0) AS fixed_deposit,
    COALESCE(d.deposit_date, '-') AS deposit_date
FROM users u
LEFT JOIN deposits d
    ON u.id = d.user_id
    AND YEAR(d.deposit_date) = %s
    AND MONTH(d.deposit_date) = %s
LEFT JOIN total_loans tl
    ON u.id = tl.user_id
ORDER BY u.id;
"""
        cursor.execute(query, (year, month))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('deposits.html', results=results, month=month, year=year)
    except Exception as e:
        return render_template('deposits.html', error=str(e))


MONTH_MAP = {
    '1': 'January',
    '2': 'February',
    '3': 'March',
    '4': 'April',
    '5': 'May',
    '6': 'June',
    '7': 'July',
    '8': 'August',
    '9': 'September',
    '10': 'October',
    '11': 'November',
    '12': 'December'
}



def safe_decimal(value):
    return f"{value:.2f}" if isinstance(value, (int, float)) else str(value)

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:  # Print only on the first page
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Loan and Deposits Report', ln=True, align='C')
            self.ln(3)  # Add some spacing

@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    month = request.args.get('month')
    year = request.args.get('year')
    month_name = calendar.month_name[int(month)]  # Convert month number to name

    if not month or not year:
        return render_template('deposits.html', error='Both month and year are required')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch deposit details
        query = """
SELECT
    u.id AS user_id,
    u.name AS member_name,
    COALESCE(d.loan_before, tl.total_amount, 0) AS loan_amount,
    COALESCE(d.total_deposit, 0) AS installment,
    COALESCE(d.loan_interest, 0) AS loan_interest,
    COALESCE(d.fine_applied, 0) AS fine,
    COALESCE(d.extra_amount, 0) AS loan_repay,
    COALESCE(d.loan_after, tl.total_amount, 0) AS loan_remaining,
    COALESCE(d.fixed_deposit, 0) AS deposit_duration,
    COALESCE(d.deposit_date, '-') AS deposit_date
FROM users u
LEFT JOIN deposits d
    ON u.id = d.user_id
    AND YEAR(d.deposit_date) = %s
    AND MONTH(d.deposit_date) = %s
LEFT JOIN total_loans tl
    ON u.id = tl.user_id
ORDER BY u.id;
"""
        cursor.execute(query, (year, month))
        results = cursor.fetchall()


        # Fetch account details
        cursor.execute("SELECT total_balance, balance_in_loan, free_balance FROM Account LIMIT 1")
        account_details = cursor.fetchone()

        # Fetch total loans issued in the specified month
        cursor.execute("SELECT SUM(amount) AS total_loans_issued FROM loan WHERE MONTH(created_at) = %s AND YEAR(created_at) = %s", (month, year))
        loans_issued = cursor.fetchone()
        total_loans_issued = loans_issued['total_loans_issued'] if loans_issued['total_loans_issued'] else 0.0

        cursor.close()
        conn.close()

        # Generate PDF
        pdf = PDF('L', 'mm', 'A4')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'MONTH: {month_name} - {year}', ln=True, align='C')
        pdf.ln(3)

        # Define column widths for deposit details table
        col_widths = [10, 50, 25, 25, 25, 25, 25, 25, 25, 35]
        headers = ['S.No', 'Name', 'Loan Amount', 'Installment', 'Interest',
                   'Fine', 'Loan Repay', 'Remaining', 'Shares', 'Deposit Date']

        # **Step 1: Table Header Styling**
        pdf.set_fill_color(200, 200, 200)  # Light Gray background for header
        pdf.set_font('Arial', 'B', 10)

        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
        pdf.ln()

        pdf.set_font('Arial', '', 10)

        # Totals Initialization
        total_loan = total_installment = total_interest = 0.0
        total_fine = total_repay = total_remaining = total_shares = 0.0

        # **Step 2: Print Rows with Alternating Colors**
        for idx, row in enumerate(results, start=1):
            row_data = [
                str(idx), row['member_name'], safe_decimal(row['loan_amount']),
                safe_decimal(row['installment']), safe_decimal(row['loan_interest']),
                safe_decimal(row['fine']), safe_decimal(row['loan_repay']),
                safe_decimal(row['loan_remaining']), safe_decimal(row['deposit_duration']),
                row['deposit_date']
            ]

            # **Calculate Maximum Row Height**
            max_lines = 1
            for i, text in enumerate(row_data):
                estimated_lines = math.ceil(pdf.get_string_width(text) / (col_widths[i] - 2))
                max_lines = max(max_lines, estimated_lines)

            row_height = max_lines * 10

            # **Alternate row colors**
            if idx % 2 == 0:
                pdf.set_fill_color(235, 235, 235)  # Light gray fill for even rows
            else:
                pdf.set_fill_color(255, 255, 255)  # White background for odd rows

            y_start = pdf.get_y()

            # **Print Each Column with Proper Row Height**
            for i, text in enumerate(row_data):
                x_start = pdf.get_x()

                if i == 1:  # Multi-cell for Name column
                    pdf.multi_cell(col_widths[i], 10, text, border=1, align='C', fill=True)
                else:
                    pdf.cell(col_widths[i], row_height, text, border=1, align='C', fill=True)

                pdf.set_xy(x_start + col_widths[i], y_start)

            pdf.ln(row_height)

            # **Step 3: Update Totals**
            total_loan += float(row['loan_amount'])
            total_installment += float(row['installment'])
            total_interest += float(row['loan_interest'])
            total_fine += float(row['fine'])
            total_repay += float(row['loan_repay'])
            total_remaining += float(row['loan_remaining'])
            total_shares += float(row['deposit_duration'])

        # **Step 4: Print Totals Row**
        pdf.set_fill_color(200, 200, 200)  # Light gray for totals row
        pdf.set_font('Arial', 'B', 10)

        pdf.cell(col_widths[0], 9, '', border=1, align='C', fill=True)  # Empty S.No cell
        pdf.cell(col_widths[1], 9, 'Total', border=1, align='C', fill=True)  # "Total" in Name column

        for i, value in enumerate([
            safe_decimal(total_loan), safe_decimal(total_installment), safe_decimal(total_interest),
            safe_decimal(total_fine), safe_decimal(total_repay), safe_decimal(total_remaining),
            safe_decimal(total_shares), ''
        ]):
            pdf.cell(col_widths[i+2], 9, value, border=1, align='C', fill=True)

        pdf.ln(15)  # Add space before the next section

         # **Step 5: Add Account Details and Loans Issued Section**
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Account Details and Loans Issued', ln=True, align='C')
        pdf.ln(5)

        # Define column widths for the new table
        col_widths_account = [60, 40]  # Column 1: Label, Column 2: Value

        # Table Header Styling
        pdf.set_fill_color(200, 200, 200)  # Light gray background for header
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(col_widths_account[0], 10, 'Description', border=1, align='C', fill=True)
        pdf.cell(col_widths_account[1], 10, 'Amount (RS)', border=1, align='C', fill=True)
        pdf.ln()

        # Table Rows Styling
        pdf.set_font('Arial', '', 10)
        pdf.set_fill_color(255, 255, 255)  # White background for rows

        # Row 1: Total Balance
        pdf.cell(col_widths_account[0], 10, 'Total Balance', border=1, align='L', fill=True)
        pdf.cell(col_widths_account[1], 10, safe_decimal(account_details['total_balance']), border=1, align='R', fill=True)
        pdf.ln()

        # Row 2: Balance in Loan
        pdf.cell(col_widths_account[0], 10, 'Balance in Loan', border=1, align='L', fill=True)
        pdf.cell(col_widths_account[1], 10, safe_decimal(account_details['balance_in_loan']), border=1, align='R', fill=True)
        pdf.ln()

        # Row 3: Free Balance
        pdf.cell(col_widths_account[0], 10, 'Free Balance', border=1, align='L', fill=True)
        pdf.cell(col_widths_account[1], 10, safe_decimal(account_details['free_balance']), border=1, align='R', fill=True)
        pdf.ln()

        # Row 4: Total Loans Issued
        pdf.cell(col_widths_account[0], 10, 'Total Loans Issued', border=1, align='L', fill=True)
        pdf.cell(col_widths_account[1], 10, safe_decimal(total_loans_issued), border=1, align='R', fill=True)
        pdf.ln()

        # **Step 6: Output PDF**
        pdf_string = pdf.output(dest='S')
        pdf_bytes = pdf_string.encode('latin-1', 'replace')
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        filename = f'deposits_{month_name}_{year}.pdf'
        return send_file(pdf_buffer, download_name=filename, as_attachment=True, mimetype='application/pdf')

    except Exception as e:
        return render_template('deposits.html', error=str(e))


@app.route('/delete_deposit', methods=['GET', 'POST'])
def delete_deposit():


    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    error = None
    message = None
    deposits = []
    users = []
    preview_data = None

    # Fetch all users for dropdown selection
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()

    if request.method == 'POST':
        if 'preview_id' in request.form:
            deposit_id = request.form.get('preview_id')

            cursor.execute('SELECT * FROM deposits WHERE id = %s', (deposit_id,))
            deposit = cursor.fetchone()

            if deposit:
                preview_data = {
                    "deposit_id": deposit['id'],
                    "loan_before": float(deposit['loan_before']),
                    "loan_after": float(deposit['loan_after']),
                    "extra_amount": float(deposit['extra_amount']),
                    "interest": float(deposit['loan_interest']),
                    "fine": float(deposit['fine_applied']),
                    "total_deposit": float(deposit['total_deposit'])
                }
            else:
                error = "Deposit not found!"

        elif 'delete_id' in request.form:
            deposit_id = request.form.get('delete_id')

            cursor.execute('SELECT * FROM deposits WHERE id = %s', (deposit_id,))
            deposit = cursor.fetchone()

            if deposit:
                user_id = deposit['user_id']
                inserted_amount = float(deposit['total_deposit'])
                interest = float(deposit['loan_interest'])
                extra_amount = float(deposit['extra_amount'])
                fine = float(deposit['fine_applied'])
                loan_before = float(deposit['loan_before'])

                new_total_loans = loan_before
                cursor.execute('UPDATE total_loans SET total_amount = %s WHERE user_id = %s',
                               (new_total_loans, user_id))

                cursor.execute("SELECT total_balance, free_balance, balance_in_loan FROM Account LIMIT 1")
                account = cursor.fetchone()

                if account:
                    new_total_balance = float(account['total_balance']) - (interest + fine + 1000)
                    new_free_balance = float(account['free_balance']) - inserted_amount
                    new_balance_in_loan = float(account['balance_in_loan']) + extra_amount

                    cursor.execute('''
                        UPDATE Account
                        SET total_balance = %s, free_balance = %s, balance_in_loan = %s
                        LIMIT 1
                    ''', (new_total_balance, new_free_balance, new_balance_in_loan))

                cursor.execute('DELETE FROM deposits WHERE id = %s', (deposit_id,))
                conn.commit()
                message = "Deposit deleted successfully!"

                # ✅ Redirect to avoid resubmission on refresh
                return redirect(url_for('delete_deposit', message=message))

        elif 'username' in request.form:
            selected_username = request.form.get('username')

            cursor.execute('SELECT id FROM users WHERE name = %s', (selected_username,))
            user = cursor.fetchone()

            if user:
                user_id = user['id']
                cursor.execute('SELECT * FROM deposits WHERE user_id = %s', (user_id,))
                deposits = cursor.fetchall()
            else:
                error = "User not found!"

    cursor.close()
    conn.close()

    return render_template('delete_deposit.html', users=users, deposits=deposits, preview_data=preview_data,
                           message=message, error=error)


@app.route('/delete_loan', methods=['GET', 'POST'])
def delete_loan():


    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    message = session.pop('message', None)  # Retrieve and clear message after redirect
    users = []
    loans = []

    # Fetch users for dropdown selection
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()

    selected_user_id = request.form.get('user_id')

    if selected_user_id:
        # Fetch all loans for the selected user
        cursor.execute("SELECT * FROM loan WHERE user_id = %s", (selected_user_id,))
        loans = cursor.fetchall()

    if request.method == 'POST' and 'delete_id' in request.form:
        loan_id = request.form['delete_id']

        # Fetch loan details before deletion
        cursor.execute("SELECT * FROM loan WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()

        if loan:
            user_id = loan['user_id']
            loan_amount = float(loan['amount'])

            # Fetch total loan amount before deletion
            cursor.execute("SELECT total_amount FROM total_loans WHERE user_id = %s", (user_id,))
            total_loan_record = cursor.fetchone()

            if total_loan_record:
                new_total = max(0, float(total_loan_record['total_amount']) - loan_amount)  # Prevent negative values
                cursor.execute("UPDATE total_loans SET total_amount = %s WHERE user_id = %s", (new_total, user_id))

            # Fetch Account details
            cursor.execute("SELECT free_balance, balance_in_loan FROM Account LIMIT 1 FOR UPDATE")
            account = cursor.fetchone()

            if account:
                new_free_balance = float(account['free_balance']) + loan_amount
                new_balance_in_loan = max(0, float(account['balance_in_loan']) - loan_amount)  # Prevent negative values

                cursor.execute("UPDATE Account SET free_balance = %s, balance_in_loan = %s LIMIT 1",
                               (new_free_balance, new_balance_in_loan))

            # Delete loan record
            cursor.execute("DELETE FROM loan WHERE id = %s", (loan_id,))
            conn.commit()

            # ✅ Store success message in session before redirecting
            session['message'] = "Loan Deleted Successfully ✅"

            return redirect(url_for('delete_loan'))  # Redirect to clear POST data

    cursor.close()
    conn.close()

    return render_template('delete_loan.html', users=users, loans=loans, message=message)

@app.route('/admin_deposit_login', methods=['GET', 'POST'])
def admin_deposit_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'ArunC' and password == 'Arun@123Chouthai':
            session['add_admin_logged_in'] = True
            return redirect(url_for('delete_deposit'))
        else:
            error = "Invalid username or password. Please try again."

    return render_template('admin_deposit_login.html',error=error)

@app.route('/admin_loans_login', methods=['GET', 'POST'])
def admin_loans_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'ArunC' and password == 'Arun@123Chouthai':
            session['add_loans_logged_in'] = True
            return redirect(url_for('delete_loan'))
        else:
            error = "Invalid username or password. Please try again."

    return render_template('admin_loan_login.html',error=error)

if __name__ == '__main__':
    app.run(debug=True)
