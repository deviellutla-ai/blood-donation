import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "blood_donation.db")

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    first_time = not os.path.exists(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            blood_group TEXT,
            address TEXT,
            dob TEXT,
            role TEXT DEFAULT 'donor',
            availability INTEGER DEFAULT 1,
            total_donations INTEGER DEFAULT 0,
            next_eligible_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS blood_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            units_required INTEGER NOT NULL,
            contact_number TEXT NOT NULL,
            emergency_level TEXT DEFAULT 'Normal',
            status TEXT DEFAULT 'Pending',
            requester_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS donation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id INTEGER NOT NULL,
            donation_date TEXT NOT NULL,
            hospital TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Completed',
            FOREIGN KEY (donor_id) REFERENCES users (id)
        );

        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    db.commit()

    if first_time:
        seed(db)
    db.close()


def seed(db):
    demo_users = [
        ("Ramesh Kumar", "ramesh@example.com", "9876543210", "O+", "Hyderabad", "1995-04-12", "donor", 1, 3),
        ("Priya Sharma", "priya@example.com", "9123456780", "A+", "Secunderabad", "1998-09-02", "donor", 1, 5),
        ("Sumanth Reddy", "sumanth@example.com", "9988776655", "B+", "Hyderabad", "1993-01-20", "donor", 1, 1),
        ("Anil Varma", "anil@example.com", "9012345678", "AB+", "Kukatpally", "1990-11-30", "donor", 1, 7),
        ("Devi Nair", "devi@example.com", "9090909090", "O+", "Hyderabad", "1996-06-15", "donor", 1, 3),
        ("Admin User", "admin@blooddonation.org", "9000000000", "O+", "Hyderabad", "1988-01-01", "admin", 1, 0),
    ]
    pw = generate_password_hash("password123")
    for name, email, phone, bg, addr, dob, role, avail, donations in demo_users:
        next_elig = (datetime.utcnow() + timedelta(days=90)).strftime("%Y-%m-%d")
        db.execute(
            """INSERT INTO users (full_name, email, phone, password_hash, blood_group,
                address, dob, role, availability, total_donations, next_eligible_date)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (name, email, phone, pw, bg, addr, dob, role, avail, donations, next_elig),
        )
    db.commit()

    donor_ids = [r[0] for r in db.execute("SELECT id FROM users WHERE role='donor'").fetchall()]
    sample_history = [
        (donor_ids[0], "2024-01-10", "Red Cross", "O+", 1, "Completed"),
        (donor_ids[0], "2023-06-15", "City Hospital", "O+", 1, "Completed"),
        (donor_ids[0], "2022-11-20", "Apollo Hospital", "O+", 1, "Completed"),
    ]
    db.executemany(
        """INSERT INTO donation_history (donor_id, donation_date, hospital, blood_group, units, status)
           VALUES (?,?,?,?,?,?)""",
        sample_history,
    )

    sample_requests = [
        ("Ravi Kumar", "O+", "Apollo Hospital", 2, "9876500000", "Urgent", "Pending", donor_ids[0]),
        ("Lakshmi Devi", "A+", "City Hospital", 1, "9876511111", "Normal", "Approved", None),
    ]
    db.executemany(
        """INSERT INTO blood_requests (patient_name, blood_group, hospital_name, units_required,
            contact_number, emergency_level, status, requester_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        sample_requests,
    )
    db.commit()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


@app.context_processor
def inject_user():
    return {"current_user": current_user(), "blood_groups": BLOOD_GROUPS}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please login to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user["role"] != "admin":
            flash("Admin access only.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    db = get_db()
    stats = {
        "donors": db.execute("SELECT COUNT(*) FROM users WHERE role='donor'").fetchone()[0] or 0,
        "donations": db.execute("SELECT COUNT(*) FROM donation_history").fetchone()[0] or 0,
        "lives": db.execute("SELECT COUNT(*) FROM donation_history").fetchone()[0] * 3,
    }
    return render_template("home.html", stats=stats)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not (name and email and message):
            flash("Please fill in all fields.", "error")
        else:
            db = get_db()
            db.execute(
                "INSERT INTO contact_messages (name, email, message) VALUES (?,?,?)",
                (name, email, message),
            )
            db.commit()
            flash("Your message has been sent. We'll get back to you soon.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html")


# ---------------------------------------------------------------------------
# Auth pages
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        blood_group = request.form.get("blood_group", "")
        address = request.form.get("address", "").strip()
        dob = request.form.get("dob", "")

        errors = []
        if not full_name or not email or not password:
            errors.append("Name, email and password are required.")
        if blood_group not in BLOOD_GROUPS:
            errors.append("Please select a valid blood group.")

        db = get_db()
        if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            errors.append("An account with this email already exists.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", form=request.form)

        next_elig = datetime.utcnow().strftime("%Y-%m-%d")
        db.execute(
            """INSERT INTO users (full_name, email, phone, password_hash, blood_group,
                address, dob, role, availability, total_donations, next_eligible_date)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (full_name, email, phone, generate_password_hash(password), blood_group,
             address, dob, "donor", 1, 0, next_elig),
        )
        db.commit()
        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ? OR phone = ?", (identifier, identifier)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['full_name'].split(' ')[0]}!", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))
        flash("Invalid email/phone or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Donor pages
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    db = get_db()
    recent_requests = db.execute(
        "SELECT * FROM blood_requests WHERE requester_id = ? ORDER BY created_at DESC LIMIT 3",
        (user["id"],),
    ).fetchall()
    return render_template("dashboard.html", recent_requests=recent_requests)


@app.route("/dashboard/availability", methods=["POST"])
@login_required
def toggle_availability():
    user = current_user()
    db = get_db()
    new_val = 0 if user["availability"] else 1
    db.execute("UPDATE users SET availability = ? WHERE id = ?", (new_val, user["id"]))
    db.commit()
    flash("Availability updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/search", methods=["GET"])
def search():
    return render_template("search.html")


@app.route("/donors")
def donors():
    db = get_db()
    blood_group = request.args.get("blood_group", "").strip()
    city = request.args.get("city", "").strip()

    query = "SELECT * FROM users WHERE role = 'donor'"
    params = []
    if blood_group:
        query += " AND blood_group = ?"
        params.append(blood_group)
    if city:
        query += " AND address LIKE ?"
        params.append(f"%{city}%")
    query += " ORDER BY availability DESC, full_name ASC"

    donor_list = db.execute(query, params).fetchall()
    return render_template("donors.html", donor_list=donor_list, blood_group=blood_group, city=city)


@app.route("/request-blood", methods=["GET", "POST"])
def request_blood():
    if request.method == "POST":
        patient_name = request.form.get("patient_name", "").strip()
        blood_group = request.form.get("blood_group", "")
        hospital_name = request.form.get("hospital_name", "").strip()
        units_required = request.form.get("units_required", "1")
        contact_number = request.form.get("contact_number", "").strip()
        emergency_level = request.form.get("emergency_level", "Normal")

        if not (patient_name and blood_group and hospital_name and contact_number):
            flash("Please fill in all required fields.", "error")
            return render_template("request_blood.html", form=request.form)

        user = current_user()
        db = get_db()
        cur = db.execute(
            """INSERT INTO blood_requests (patient_name, blood_group, hospital_name,
                units_required, contact_number, emergency_level, status, requester_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (patient_name, blood_group, hospital_name, units_required, contact_number,
             emergency_level, "Pending", user["id"] if user else None),
        )
        db.commit()
        flash("Your blood request has been submitted.", "success")
        return redirect(url_for("request_status", request_id=cur.lastrowid))

    return render_template("request_blood.html", form={})


@app.route("/request-status")
@app.route("/request-status/<int:request_id>")
def request_status(request_id=None):
    db = get_db()
    if request_id:
        req = db.execute("SELECT * FROM blood_requests WHERE id = ?", (request_id,)).fetchone()
        return render_template("request_status.html", req=req, all_requests=None)

    user = current_user()
    all_requests = None
    if user:
        all_requests = db.execute(
            "SELECT * FROM blood_requests WHERE requester_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    return render_template("request_status.html", req=None, all_requests=all_requests)


@app.route("/history")
@login_required
def history():
    user = current_user()
    db = get_db()
    records = db.execute(
        "SELECT * FROM donation_history WHERE donor_id = ? ORDER BY donation_date DESC",
        (user["id"],),
    ).fetchall()
    return render_template("history.html", records=records)


# ---------------------------------------------------------------------------
# Admin pages
# ---------------------------------------------------------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) FROM users WHERE role='donor'").fetchone()[0]
    total_donors = db.execute(
        "SELECT COUNT(*) FROM users WHERE role='donor' AND availability=1"
    ).fetchone()[0]
    total_requests = db.execute("SELECT COUNT(*) FROM blood_requests").fetchone()[0]
    today_donations = db.execute(
        "SELECT COUNT(*) FROM donation_history WHERE donation_date = ?",
        (datetime.utcnow().strftime("%Y-%m-%d"),),
    ).fetchone()[0]

    bg_stats = db.execute(
        "SELECT blood_group, COUNT(*) as c FROM users WHERE role='donor' GROUP BY blood_group"
    ).fetchall()

    req_status = db.execute(
        "SELECT status, COUNT(*) as c FROM blood_requests GROUP BY status"
    ).fetchall()

    recent_requests = db.execute(
        "SELECT * FROM blood_requests ORDER BY created_at DESC LIMIT 6"
    ).fetchall()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_donors=total_donors,
        total_requests=total_requests,
        today_donations=today_donations,
        bg_stats=bg_stats,
        req_status=req_status,
        recent_requests=recent_requests,
    )


@app.route("/admin/request/<int:request_id>/<string:new_status>")
@admin_required
def admin_update_request(request_id, new_status):
    if new_status not in ("Pending", "Approved", "Completed", "Rejected"):
        flash("Invalid status.", "error")
        return redirect(url_for("admin_dashboard"))
    db = get_db()
    db.execute("UPDATE blood_requests SET status = ? WHERE id = ?", (new_status, request_id))
    db.commit()
    flash("Request status updated.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
