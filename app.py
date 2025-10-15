from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
import uuid

# ---------------- Flask App Configuration ----------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "pradeep_secret_key")  # use env var for production

# ---------------- Flask-Mail Configuration ----------------
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="pradeepshaw276@gmail.com",        # your email
    MAIL_PASSWORD="azucjawqtemtvnvr",                # Gmail app password
    MAIL_DEFAULT_SENDER="pradeepshaw276@gmail.com",
)

mail = Mail(app)

# ---------------- Database Connection ----------------
DB_NAME = "example.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- Initialize Database ----------------
def init_db():
    """Create all necessary tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()

    tables = {
        "accounts": """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'student'
            )
        """,
        "students": """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                dob TEXT,
                gender TEXT,
                address TEXT,
                school_name TEXT,
                total_marks REAL,
                email TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """,
        "documents": """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER
            )
        """
    }

    for table_sql in tables.values():
        cursor.execute(table_sql)

    conn.commit()
    conn.close()

# ---------------- Login Required Decorator ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("You need to login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- Routes ----------------

@app.route("/")
def home():
    return render_template("home.html")

# -------- Registration --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            flash("All fields are required ❌", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO accounts (username, password) VALUES (?, ?)",
                             (username, hashed_password))
                conn.commit()
            flash("Registration Successful ✅ Please login", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists ❌", "danger")

    return render_template("register.html")

# -------- Login --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM accounts WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            flash("Login Successful ✅", "success")
            return redirect(url_for("details"))
        else:
            flash("Invalid username or password ❌", "danger")

    return render_template("login.html")

# -------- Details Form (with file upload + email sending) --------
@app.route("/details", methods=["GET", "POST"])
@login_required
def details():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        stream = request.form["stream"].strip()
        passing_year=request.form["passing_year"].strip()
        board=request.form["board"].strip()
        school_name=request.form["school_name"].strip()
        percentage=request.form["percentage"].strip()
        roll=request.form["roll"].strip()
        citizenship=request.form["citizenship"].strip()
        state=request.form["state"].strip()
        address=request.form["address"].strip()
        pin_code=request.form["pin_code"].strip()
        caste=request.form["caste"].strip()
        message_text = request.form["message"].strip()
        marksheet_file = request.files.get("marksheet_10th")

        try:
            # ---- Send confirmation email to user ----
            user_msg = Message(
                subject="We Received Your Details ✅",
                recipients=[email],
                body=f"Hello {name},\n\nYour details and document submission were received successfully.\nWe'll get back to you soon!\n\n- Team Admin"
            )
            mail.send(user_msg)

            # ---- Send admin notification ----
            admin_msg = Message(
                subject=f"New Submission from {name}",
                recipients=[app.config["MAIL_USERNAME"]],
                body=f"New submission received:\n\nName: {name}\nEmail: {email}\nMessage: {message_text} \nStream : {stream}\n  passing_year:{passing_year}\nboard:{board}\nschool_name:{school_name}\n percentage:{percentage} \ncitizenship:{citizenship}\nstate:{state}\naddress:{address}\npin_code:{pin_code}\ncaste:{caste} \n roll:{roll}")

            if marksheet_file and marksheet_file.filename:
                marksheet_file.seek(0)
                admin_msg.attach(
                    filename=marksheet_file.filename,
                    content_type=marksheet_file.content_type,
                    data=marksheet_file.read()
                )
                flash_msg = "Details & marksheet submitted successfully. Confirmation email sent ✅"
            else:
                admin_msg.body += "\n\n(Note: No marksheet file attached.)"
                flash_msg = "Details submitted successfully (no file attached). Confirmation email sent ✅"

            mail.send(admin_msg)
            flash(flash_msg, "success")

        except Exception as e:
            flash(f"Error processing submission or sending email: {e}", "danger")

        return redirect(url_for("details"))

    return render_template("details.html")

@app.route("/about")
def about():
    staff = [
        {"name": "Mr. Khursid Ali", "role": "Physics Teacher", "photo": "staff/s1.jpeg"},
        {"name": "Mr Birendra Yadav", "role": "Math Teacher", "photo": "staff/s1.jpeg"},
        {"name": "Mrs. Barnali Ma'm", "role": "Chemistry Teacher", "photo": "staff/s1.jpeg"},
    ]

    headmaster = {
        "name": "Sri Santosh Choudhary",
        "message": "Welcome to our school, a place where we are dedicated to cultivating both academic excellence and personal growth. We strive to inspire curiosity, nurture talent, and instill strong values, preparing every student to succeed with confidence and integrity in an ever-changing world.",
        "photo": "staff/headmaster.jpg"
    }

    videos = ["videos/v1.mp4", "videos/v2.mp4"]
    photos = ["images/school1.jpg", "images/school2.jpg", "images/school3.jpeg"]

    return render_template("about.html", staff=staff, headmaster=headmaster, videos=videos, photos=photos)

# -------- Logout --------
@app.route("/logout")
@login_required
def logout():
    session.pop("user", None)
    flash("Logged out successfully ✅", "info")
    return redirect(url_for("login"))
# ---------------- Contact route ----------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        # --- Send Email to Admin ---
        try:
            msg = Message(
                subject=f"New Contact Message: {subject}",
                sender=email,
                recipients=['pradeepshaw276@gmail.com']  # Replace with your admin mail
            )
            msg.body = f"""
            You have received a new message from your School Management System contact page.

            📩 Name: {name}
            📧 Email: {email}
            📝 Subject: {subject}

            💬 Message:
            {message}

            ---
            Regards,
            Barrackpore Cantonment Vidyapith
            """
            mail.send(msg)
            flash('✅ Thank you for contacting   Barrackpore Cantonment Vidyapith ! Your message has been sent successfully.', 'success')
        except Exception as e:
            flash('❌ Sorry, there was an error sending your message. Please try again later.', 'danger')
            print("Error:", e)

        return redirect(url_for('contact'))

    return render_template('contact.html')
# ---------------- Achievements route  ----------------
@app.route('/achievements')
def achievements():
    return render_template('achievements.html')
# ---------------- Run App ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)   